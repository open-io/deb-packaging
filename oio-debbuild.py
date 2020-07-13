#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2019-2020 OpenIO <info@openio.io>
# Copyright © 2019-2020 Vincent Legoll <vincent.legoll@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Get source code tarball from the `sources` file and rename it to the blessed
debian file name then build the .deb package(s) and upload it to the specified
mirror subdirectory.

This is based on a translation of oio-debbuild.sh
'''

import os
import sys
import glob
import shutil
import argparse
import subprocess
from zipfile import ZipFile
import tarfile

################################################################################

_VERBOSE = False

(_ERROR, _WARN, _INFO) = range(3)

_VPRINT_PREFIX = {
    _ERROR: 'ERROR: ',
    _WARN:  'WARNING: ',
    _INFO:  'INFO: ',
}

def vprint(msg, severity=_INFO):
    '''Display verbose infos'''
    if _VERBOSE or severity == _ERROR:
        print(_VPRINT_PREFIX[severity] + msg)
    if severity == _ERROR:
        sys.exit(1)

################################################################################

# Do not build source code packages for the following closed-source projects
_PRIVATE_PKGS = (
    "oiofs-fuse",
    "openio-billing",
    "oio-grid",
    "openio-sds-replicator"
)

# Base pbuilder path
_PBUILDER = '/var/cache/pbuilder'

# Projects code names
_MDI_PROJECTS = (
    'g4a',
    'sds',
    'oiofs',
    'oiocb',
    'replicator',
    'oioswiftext',
)

# Projects versions (mini-dinstall targets)
_MDI_VERSIONS = (
    'unstable', # FIXME: kept for 18.04 only, remove when it's been phased out
    '18.04',
    '18.10',
    '18.10-unstable',
    '19.04',
    '19.04-unstable',
    '19.10',
    '19.10-unstable',
    '20.04',
    '20.04-unstable',
    '20.10',
    '20.10-unstable',
)

# Supported distributions
_DISTIDS = (
    'debian',
    'raspbian',
    'ubuntu',
)

# Mirror names (not FQDNs)
_MIRRORS = ('mirror', 'mirror2')

################################################################################

def doit(args):
    '''Do the work'''

    basedir = os.getcwd()
    pkgname = os.path.basename(basedir)
    osdistro = os.path.basename(os.path.dirname(basedir))
    osdistid, osdistcodename = osdistro.split('-')
    basework = os.path.join(os.environ['HOME'], 'debbuildir')
    work = os.path.join(basework, osdistro, pkgname)
    sources = os.path.join(basedir, 'sources')
    destmirror = args.destmirror
    mirror = args.mirror

    # Arguments validation
    if mirror not in _MIRRORS:
        vprint('Invalid mirror: %s' % mirror, _ERROR)

    if not os.path.isdir(basework):
        vprint("Working directory '%s' doesn't exist." % basework, _ERROR)

    if osdistid not in _DISTIDS:
        vprint("Unknown distribution: %s" % osdistid, _ERROR)

    if not os.path.exists(sources):
        vprint("No `sources` file available in this directory.", _ERROR)

    if destmirror:
        if args.mirror in destmirror:
            vprint('You should not pass the mirror name in "--destmirror"'
                   ' as it is automatically added', _ERROR)
        if '-stable' in destmirror:
            vprint('You should not pass "-stable" suffix in "--destmirror" as '
                   'it is automatically added', _ERROR)

    # Use arguments or environment variables
    if args.arch:
        arch = args.arch
        vprint('Using --arch CLI argument: ' + arch)
    elif 'ARCH' in os.environ:
        arch = os.environ['ARCH']
        vprint('Using ARCH environment variable: ' + arch)
    else:
        arch = subprocess.check_output(['dpkg', '--print-architecture'])
        arch = arch.strip().decode('ascii')
        vprint('Defaulting to `dpkg --print-architecture`: ' + arch)

    if args.release:
        release = args.release
        vprint('Using --release CLI argument: ' + release)
    elif 'SDS_RELEASE' in os.environ:
        release = os.environ['SDS_RELEASE']
        vprint('Using SDS_RELEASE environment variable: ' + release)
    else:
        git_branch = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        release = subprocess.check_output(git_branch).strip().decode('ascii')
        vprint('Using guessed version from current git repo branch: ' + release)

    vprint("Recreating working directory")

    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)

    vprint("Downloading source files")

    wrkdst = parse_sources(sources, work)

    vprint("Building source package")

    dpkg_buildpackage(wrkdst, work)

    vprint("Building package")

    pb_cfg_kwargs = {
        'osdistid': osdistid,
        'osdistcodename': osdistcodename,
        'arch': arch,
        'release': release,
        'mirror': mirror,
        'unstable': args.unstable,
        'destmirror': destmirror,
    }

    pbuilder(pkgname, work=work, **pb_cfg_kwargs)

    if destmirror:
        pkgupload(work=work, **pb_cfg_kwargs)
    else:
        vprint("Not uploading package(s)")


def pbuilder_cfg_name(**kwargs):
    '''Return the pbuilder config name'''
    vprint('pbuilder_cfg_name(), kwargs:' + str(kwargs))
    pb_cfg_fmt = "{osdistid}-{osdistcodename}-{arch}-{release}"
    if kwargs['unstable']:
        pb_cfg_fmt += "-unstable"
    else:
        pb_cfg_fmt += "-stable"
    pb_cfg_fmt += "-{mirror}"
    return pb_cfg_fmt.format(**kwargs)


def pkgupload(work, **kwargs):
    '''Upload package to specified mirror (args.destmirror), if any'''

    vprint("Uploading package(s)")
    pkgdsc = [f for f in os.listdir(work) if f.endswith('.dsc')][0]
    vprint('Using *.dsc file: ' + pkgdsc)
    dsc = os.path.basename(pkgdsc)
    pkg_basename = os.path.splitext(dsc)[0]
    tgt_subdir = pbuilder_cfg_name(**kwargs)
    resultdir = os.path.join(_PBUILDER, tgt_subdir, 'result')
    if is_mini_dinstall_target(**kwargs):
        upload_pkg_dput(resultdir, pkg_basename, pkgdsc, **kwargs)
    else:
        vprint('Unknown target repository: ' + kwargs['destmirror'], _ERROR)


def is_mini_dinstall_target(**kwargs):
    '''
    Check if the parameter is OK as a mini-dinstall target and also ensure it is
    consistent with the packaging release (repository branch or CLI argument)
    '''

    tgt = kwargs['destmirror']
    if '-' not in tgt:
        vprint('Target repository does not contain any "-" character', _WARN)
        return False
    elts = tgt.split('-')
    if len(elts) == 1:
        vprint('Target repository is missing (at least) one "-"-separated '
               'element', _WARN)
        return False
    if len(elts) == 2:
        name, version = elts
    elif len(elts) == 3:
        name, version, unstable = elts
        if unstable != 'unstable':
            vprint("Target repository should ends with '-unstable' : %s" % tgt,
                   _WARN)
            return False
        if not kwargs['unstable']:
            vprint('You did not pass the "-u / --unstable" CLI argument, but '
                   'it looks like you should have: %s' % tgt, _WARN)
            # No return here, this one is only a harmless warning
    else:
        vprint('Target repository name contains too much "-" characters:', tgt,
               _WARN)
        return False
    if version != kwargs['release']:
        vprint('Target repository (%s) / release (%s) mismatch' %
               (version, kwargs['release']), _WARN)
    if name not in _MDI_PROJECTS:
        vprint('Unknown mini-dinstall project: ' + name, _WARN)
        return False
    if version not in _MDI_VERSIONS:
        vprint('Unknown mini-dinstall version: ' + version, _WARN)
        return False
    return True


def upload_pkg_dput(resultdir, pkg_basename, pkgdsc, **kwargs):
    '''Use `dput` & `mini-dinstall` to upload package to mirror'''

    repo_codename = '{osdistid}-openio-{destmirror}'.format(**kwargs)
    vprint("Uploading package %s to repository %s" % (pkgdsc, repo_codename))
    dput = ['dput', '-f', '-u', repo_codename]
    changes_file_glob = os.path.join(resultdir, pkg_basename + '*.changes')
    changes_fn = glob.glob(changes_file_glob)
    if not changes_fn:
        vprint('No match for: ' + changes_file_glob, _ERROR)
    else:
        vprint('Found *.changes files: ' + str(changes_fn))
    dput.extend(changes_fn)
    vprint('Launching dput command: ' + str(dput))
    subprocess.run(dput).check_returncode()


def parse_sources(sources, work):
    '''
    Parse the `sources` file, retrieve & extract the tarball to its target
    directory
    '''

    with open(sources, 'rb') as sources_fd:
        for line in sources_fd:
            line = line.decode('ascii').strip()
            if not line or line.startswith('#'):
                continue
            items = line.split()
            if len(items) != 2:
                vprint("Malformed 'sources' file: " + sources, _ERROR)
            # VL: here we ignore dest & taropts as they are not currently used
            src, filename = items[0], items[1]
            if not filename:
                filename = os.path.basename(src)
            wrkfn = os.path.join(work, filename)
            if src.startswith('http') or src.startswith('ftp'):
                vprint('parse_sources(): downloading source file: ' + src +
                       ', to: ' + wrkfn)
                curl = ['curl', '-s', '-L', '-o', wrkfn, src]
                subprocess.check_call(curl)
            else:
                vprint('parse_sources(): copying local source file: ' + src +
                       ', to: ' + wrkfn)
                shutil.copy(src, wrkfn)

            # convert zip files to tar.gz as dpkg does not undestand zip files (wtf ?)
            if filename.endswith('.zip'):
                filename = filename.replace('.zip', '.tar.gz')
                zipfn = wrkfn
                wrkfn = os.path.join(work, filename)

                vprint("Opening zip file for reading " + zipfn)
                with ZipFile(zipfn) as zipf:
                    vprint("Opening tar file for writing " + wrkfn)
                    with tarfile.open(wrkfn, 'w:gz') as tarf:
                        for zip_info in zipf.infolist():
                            vprint("found file " + zip_info.filename + " size=" + str(zip_info.file_size))
                            tar_info = tarfile.TarInfo(name=zip_info.filename)
                            tar_info.size = zip_info.file_size
                            # TODO handle copying mtime, rights, attr, ...
                            #  tar_info.mtime = time.mktime(list(zip_info.date_time) + [-1, -1, -1])
                            tarf.addfile(tarinfo=tar_info, fileobj=zipf.open(zip_info.filename))
                os.unlink(zipfn)


    return work


def dpkg_buildpackage(wrkdst, work):
    '''Build source code package with dpkg-buildpackage'''

    vprint("dpkg_buildpackage wrkdst:" + wrkdst + ", work:" + work)

    builddir = os.path.join(wrkdst, 'builddir')
    debdir = os.path.join(builddir, 'debian')

    shutil.rmtree(builddir, ignore_errors=True)
    os.mkdir(builddir)
    shutil.copytree('debian', debdir)


    dpkg_bp = ['dpkg-buildpackage', '-S', '-us', '-uc', '-nc', '-d']
    vprint('Launching dpkg-buildpackage command: ' + str(dpkg_bp))
    subprocess.run(dpkg_bp, cwd=builddir).check_returncode()


def pbuilder(pkgname, work, **kwargs):
    '''Build the .deb package with pbuilder'''

    pbuilder_cmd = ['sudo', '-E', 'pbuilder', 'build']
    if pkgname in _PRIVATE_PKGS:
        vprint("Do not build source code package for closed-source project")
        pbuilder_cmd.extend(["--debbuildopts", "-b"])
    pbuilder_cmd.extend(glob.glob(os.path.join(work, '*.dsc')))
    env = dict(os.environ)
    # The environment variables for the /root/.pbuilderrc script
    newenv = {
        'ARCH': kwargs['arch'],
        'DISTID': kwargs['osdistid'],
        'DIST': kwargs['osdistcodename'],
        'NAME': pbuilder_cfg_name(**kwargs),
    }
    env.update(newenv)
    #FIXME: This workaround is for redis 4.0.9 packaging abusing ${ARCH}
    if pkgname == 'redis':
        del env['ARCH']
    vprint('pbuilder CLI:\n' + str(pbuilder_cmd))
    vprint('pbuilder env:\n' + str(env))
    subprocess.run(pbuilder_cmd, env=env).check_returncode()

################################################################################

def do_argparse():
    '''Handle global CLI options'''

    fmt_cls = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=fmt_cls)

    # Global options
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display additional information')

    parser.add_argument('-a', '--arch',
                        help='Use the given architecture (amd64, i386, armhf, '
                        'arm64)')

    # This is not an url or something like that, because it cannot be changed at
    # package build time, but must be built into the pbuilder tarball.
    # See also: pbuilderrc & create_build_envs.sh
    parser.add_argument('-m', '--mirror', default='mirror2',
                        help='Use the given openio mirror (mirror, mirror2). '
                        'This is only used to get openio dependencies at '
                        'package build time, and not used at package upload '
                        'time.')

    parser.add_argument('-r', '--release',
                        help='Use the given OpenIO SDS release (%s)' %
                        ', '.join(_MDI_VERSIONS))

    parser.add_argument('-u', '--unstable', action='store_true', default=False,
                        help='This will be an "unstable" build')

    parser.add_argument('destmirror', metavar='STRING', nargs='?',
                        help='Target mirror, either a mini-dinstall codename, '
                        'for example: oiofs-18.10 or sds-19.10-unstable, or an '
                        'url to an `oiorepo` service, or nothing to disable '
                        'upload')

    return parser


def validate_args(args):
    '''Global CLI arguments validation'''
    global _VERBOSE # pylint: disable=global-statement
    if args.verbose:
        _VERBOSE = True
        vprint('Verbose mode')

################################################################################

def main(sys_argv=None):
    '''Parse CLI args & do it...'''

    if sys_argv is None:
        sys_argv = sys.argv[1:]
    parser = do_argparse()
    args = parser.parse_args(sys_argv)
    validate_args(args)

    doit(args)


if __name__ == '__main__': # pragma: no cover
    main()

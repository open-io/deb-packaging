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

################################################################################

_VERBOSE = False


def vprint(msg):
    '''Display verbose infos'''
    if _VERBOSE:
        print(msg)

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

    mirror = args.mirror

    if mirror not in _MIRRORS:
        print('### invalid mirror: %s' % mirror)
        sys.exit(1)

    if not os.path.isdir(basework):
        print("### Working directory '%s' doesn't exist." % basework)
        sys.exit(1)

    if osdistid not in _DISTIDS:
        print("### Unknown distribution: %s" % osdistid)
        sys.exit(1)

    if not os.path.exists(sources):
        print("### No `sources` file available in this directory.")
        sys.exit(1)

    if args.arch:
        arch = args.arch
        print('Using --arch CLI argument: ' + arch)
    elif 'ARCH' in os.environ:
        arch = os.environ['ARCH']
        print('Using ARCH environment variable: ' + arch)
    else:
        arch = subprocess.check_output(['dpkg', '--print-architecture'])
        arch = arch.strip().decode('ascii')
        print('Defaulting to `dpkg --print-architecture`: ' + arch)

    if args.release:
        release = args.release
        print('Using --release CLI argument: ' + release)
    elif 'SDS_RELEASE' in os.environ:
        release = os.environ['SDS_RELEASE']
        print('Using SDS_RELEASE environment variable: ' + release)
    else:
        git_branch = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        release = subprocess.check_output(git_branch).strip().decode('ascii')
        print('Using guessed version from current git repo branch: ' + release)

    print("### Recreating working directory")

    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)

    print("### Downloading source files")

    wrkdst = parse_sources(sources, work)

    print("### Building source package")

    dpkg_buildpackage(wrkdst, work)

    print("### Building package")

    pbuilder(pkgname, work=work, arch=arch, release=release, osdistid=osdistid,
             osdistcodename=osdistcodename, mirror=mirror,
             unstable=args.unstable)
    pkgupload(args, work, arch, release, osdistid, osdistcodename, mirror)


def pkgupload(args, work, arch, release, osdistid, osdistcodename, mdi_mirror):
    '''Upload package to specified mirror (args.destmirror), if any'''

    mirror = args.destmirror
    if mirror:
        print("### Uploading package")
        pkgdsc = [f for f in os.listdir(work) if f.endswith('.dsc')][0]
        vprint('Using *.dsc file: ' + pkgdsc)
        dsc = os.path.basename(pkgdsc)
        pkg_basename = os.path.splitext(dsc)[0]
        if args.unstable:
            release += '-unstable'
        else:
            release += '-stable'
        tgt_elts = (osdistid, osdistcodename, arch, release, mdi_mirror)
        tgt_subdir = "%s-%s-%s-%s-%s" % tgt_elts
        resultdir = os.path.join(_PBUILDER, tgt_subdir, 'result')
        if mirror.startswith('http://'):
            upload_pkg_oiorepo(mirror, resultdir, pkgdsc)
        elif is_mini_dinstall_target(mirror, release, args):
            upload_pkg_dput(mirror, resultdir, pkg_basename, pkgdsc, osdistid)
        else:
            print('Unknown target repository:', mirror)
            sys.exit(1)


def is_mini_dinstall_target(tgt, release, args):
    '''
    Check if the parameter is OK as a mini-dinstall target and also ensure it is
    consistent with the packaging release (repository branch or CLI argument)
    '''

    elts = tgt.split('-')
    if len(elts) == 2:
        name, version = elts
    elif len(elts) == 3:
        name, version, unstable = elts
        if unstable != 'unstable':
            print("Target repository should ends with '-unstable' : %s" % tgt)
            return False
        if not args.unstable:
            print('You did not pass the "-u / --unstable" CLI argument, but '
                  'it looks like you should have: %s' % tgt)
            # No return here, this one is only a warning
    else:
        print('Target repository name contains too much "-" characters:', tgt)
        return False
    if version != release:
        print('WARNING: target repository (%s) / release (%s) mismatch' %
              (version, release))
    if name not in _MDI_PROJECTS:
        print('Unknown mini-dinstall project:', name)
        return False
    if version not in _MDI_VERSIONS:
        print('Unknown mini-dinstall version:', version)
        return False
    return True


def upload_pkg_dput(destmirror, resultdir, pkg_basename, pkgdsc, osdistid):
    '''Use `dput` & `mini-dinstall` to upload package to mirror'''

    repo_codename = '%s-openio-%s' % (osdistid, destmirror)
    print("### Uploading package %s to repository %s" % (pkgdsc, repo_codename))
    dput = ['dput', '-f', '-u', repo_codename]
    changes_file_glob = os.path.join(resultdir, pkg_basename + '*.changes')
    changes_fn = glob.glob(changes_file_glob)
    if not changes_fn:
        print('No match for: ' + changes_file_glob)
        sys.exit(1)
    else:
        vprint('Found *.changes files: ' + str(changes_fn))
    dput.extend(changes_fn)
    vprint(str(dput))
    subprocess.run(dput).check_returncode()


def upload_pkg_oiorepo(destmirror, resultdir, pkgdsc):
    '''
    Use the `oiorepo` service, see:
    https://github.com/open-io/dockerfiles/tree/master/openio-repo
    '''
    print("### Uploading package %s from %s to repository %s" %
          (pkgdsc, resultdir, destmirror))
    print('### FIXME: NOT IMPLEMENTED ###')

    #~ for f in resultdir + '*.deb':
        #~ curl -F "file=@${f}" \
             #~ -F "company=${OIO_COMPANY}" \
             #~ -F "prod=${OIO_PROD}" \
             #~ -F "prod_ver=${OIO_PROD_VER}" \
             #~ -F "distro=${OSDISTID}" \
             #~ -F "distro_ver=${OSDISTCODENAME}" \
             #~ -F "arch=${ARCH}" \
             #~ "${REPO}"


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
                vprint("Malformed 'sources' file: " + sources)
            # VL: here we ignore dest & taropts as they are not currently used
            src, filename, dest, taropt = items[0], items[1], '', ''
            if dest == '-':
                dest = ''
            if not filename:
                filename = os.path.basename(src)
            wrkfn = os.path.join(work, filename)
            if src.startswith('http') or src.startswith('ftp'):
                curl = ['curl', '-s', '-L', '-o', wrkfn, src]
                subprocess.check_call(curl)
            else:
                shutil.copy(src, wrkfn)
            wrkdst = os.path.join(work, dest)
            tar = ['tar', 'xf', wrkfn, '-C', wrkdst]
            if taropt == 'strip1':
                tar.extend("--strip-components", "1")
            subprocess.check_call(tar)

            # Assume a single tarball in sources
            return wrkdst


def dpkg_buildpackage(wrkdst, work):
    '''Build source code package with dpkg-buildpackage'''

    dircont = os.listdir(wrkdst)
    vprint('dpkg_buildpackage(), dircont: ' + str(dircont))

    isdir = os.path.isdir
    join = os.path.join

    tarsubdir = [d for d in dircont if isdir(join(wrkdst, d))][0]
    tardir = join(wrkdst, tarsubdir)
    debdir = join(tardir, 'debian')
    shutil.rmtree(debdir, ignore_errors=True)
    shutil.copytree('debian', debdir)

    vprint('dpkg_buildpackage(), tardir: ' + str(os.listdir(tardir)))
    vprint('dpkg_buildpackage(), work: ' + str(os.listdir(work)))

    dpkg_bp = ['dpkg-buildpackage', '-S', '-us', '-uc', '-nc', '-d']
    subprocess.run(dpkg_bp, cwd=tardir).check_returncode()


def pbuilder(pkgname, work, **kwargs):
    '''Build the .deb package with pbuilder'''

    pbuilder_cmd = ['sudo', '-E', 'pbuilder', 'build']
    if pkgname in _PRIVATE_PKGS:
        print("### Do not build source code package for closed-source project")
        pbuilder_cmd.extend(["--debbuildopts", "-b"])
    pbuilder_cmd.extend(glob.glob(os.path.join(work, '*.dsc')))
    env = dict(os.environ)
    # The pbuilder tarball file name
    pb_cfg_fmt = "{osdistid}-{osdistcodename}-{arch}-{release}"
    if kwargs['unstable']:
        pb_cfg_fmt += "-unstable"
    else:
        pb_cfg_fmt += "-stable"
    pb_cfg_fmt += "-{mirror}"
    # The parameters for the /root/.pbuilderrc script
    newenv = {
        'ARCH': kwargs['arch'],
        'DISTID': kwargs['osdistid'],
        'DIST': kwargs['osdistcodename'],
        'NAME': pb_cfg_fmt.format(**kwargs),
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
        vprint('verbose mode')

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

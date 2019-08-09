#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2019 OpenIO <info@openio.io>
# Copyright © 2019 Vincent Legoll <vincent.legoll@gmail.com>

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
_PRIVATE_PKGS = ("oiofs-fuse", "openio-billing", "openio-sds-replicator")

# Base pbuilder path
_PBUILDER = '/var/cache/pbuilder'

# Projects code names (mini-dinstall targets)
_MDI_PROJECTS = ('sds', 'oiofs', 'g4a', 'replicator')
_MDI_VERSIONS = ('18.04', '18.10', '19.04', 'unstable')

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

    if not os.path.isdir(basework):
        print("### Working directory '%s' doesn't exist." % basework)
        sys.exit(1)

    if osdistid not in ('ubuntu', 'debian', 'raspbian'):
        print("### Unknown distribution: %s" % osdistid)
        sys.exit(1)

    if not os.path.exists(sources):
        print("### No `sources` file available in this directory.")
        sys.exit(1)

    if args.arch:
        arch = args.arch
    elif 'ARCH' in os.environ:
        arch = os.environ['ARCH']
        print('Using ARCH environment variable: ' + arch)
    else:
        arch = subprocess.check_output(['dpkg', '--print-architecture'])
        arch = arch.strip().decode('ascii')
        print('Defaulting to `dpkg --print-architecture`: ' + arch)

    if args.release:
        release = args.release
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

    pbuilder(pkgname, work, arch, release, osdistid, osdistcodename)
    pkgupload(args, work, arch, release, osdistid, osdistcodename)


def pkgupload(args, work, arch, release, osdistid, osdistcodename):
    '''Upload package to specified mirror, if any'''

    if args.destmirror:
        print("### Uploading package")
        mirror = args.destmirror
        pkgdsc = [f for f in os.listdir(work) if f.endswith('.dsc')][0]
        vprint(pkgdsc)
        dsc = os.path.basename(pkgdsc)
        pkg_basename = os.path.splitext(dsc)[0]
        tgt_subdir = "%s-%s-%s-%s" % (osdistid, osdistcodename, arch, release)
        resultdir = os.path.join(_PBUILDER, tgt_subdir, 'result')
        if args.destmirror.startswith('http://'):
            upload_pkg_oiorepo(args.destmirror, resultdir, pkgdsc)
        elif is_mini_dinstall_target(args.destmirror, release):
            upload_pkg_dput(mirror, resultdir, pkg_basename, pkgdsc, osdistid)
        else:
            print('Unknown target repository:', args.destmirror)
            sys.exit(1)


def is_mini_dinstall_target(tgt, release):
    '''
    Check if the parameter is OK as a mini-dinstall target and also ensure it is
    consistent with the packaging release (repository branch or CLI argument)
    '''

    elts = tgt.split('-')
    if len(elts) != 2:
        print('Target repository name contains too much "-" characters:', tgt)
        return False
    name, version = elts
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
    subprocess.run(dput)


def upload_pkg_oiorepo(destmirror, resultdir, pkgdsc):
    '''
    Use the `oiorepo` service, see:
    https://github.com/open-io/dockerfiles/tree/master/openio-repo
    '''
    print("### Uploading package %s from %s to repository %s" %
          (pkgdsc, resultdir, destmirror))

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
    '''Parse the `sources` file and retrieve the tarball to its destination'''

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
                wget = ['wget', '--no-check-certificate', src, '-O', wrkfn]
                subprocess.check_call(wget)
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
    vprint(dircont)

    isdir = os.path.isdir
    join = os.path.join

    tarsubdir = [d for d in dircont if isdir(join(wrkdst, d))][0]
    tardir = join(wrkdst, tarsubdir)
    debdir = join(tardir, 'debian')
    shutil.rmtree(debdir, ignore_errors=True)
    shutil.copytree('debian', debdir)

    dpkg_bp = ['dpkg-buildpackage', '-S', '-us', '-uc', '-nc', '-d']
    subprocess.run(dpkg_bp, cwd=tardir)

    vprint(os.listdir(tardir))
    vprint(os.listdir(work))


def pbuilder(pkgname, work, arch, release, osdistid, osdistcodename):
    '''Build the .deb package with pbuilder'''

    pbuilder_cmd = ['sudo', '-E', 'pbuilder', 'build']
    if pkgname in _PRIVATE_PKGS:
        print("### Do not build source code package for closed-source project")
        pbuilder_cmd.extend("--debbuildopts", "-b")
    pbuilder_cmd.extend(glob.glob(os.path.join(work, '*.dsc')))
    env = dict(os.environ)
    newenv = {
        'ARCH': arch,
        'DISTID': osdistid,
        'DIST': osdistcodename,
        'SDS_RELEASE': release,
    }
    env.update(newenv)
    vprint(str(pbuilder_cmd))
    subprocess.run(pbuilder_cmd, env=env)

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
                        help='Use the given architecture (amd64, i386, armhf)')

    parser.add_argument('-r', '--release',
                        help='Use the given OpenIO SDS release (18.04, 18.10, '
                        '19.04)')

    parser.add_argument('destmirror', metavar='STRING', nargs='?',
                        help='Target mirror, either a mini-dinstall codename, '
                        'for example: oiofs-18.10 or sds-unstable, or an url to'
                        ' an `oiorepo` service, or nothing to disable upload')

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

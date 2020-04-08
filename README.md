# OpenIO Debian and Ubuntu packaging

This repository gathers the deb packaging files used to build OpenIO softwares.

## How to build OpenIO SDS

### Preparation

    # Log on the build VM (OpenStack)
    sft ssh oio-buildsys-deb
    # Setup your debian developper identity
    cat << EOF >> ~/.bashrc
        DEBEMAIL="your.email@openio.io"
        DEBFULLNAME="Your Name"
        export DEBEMAIL DEBFULLNAME
    EOF
    # Create the DEB build environment
    mkdir ~/debbuildir
    # Clone OpenIO's DEB packaging repository
    git clone https://github.com/open-io/deb-packaging.git

### Build one package

    # Log on the build VM (OpenStack)
    sft ssh oio-buildsys-deb

    NEW_VERSION=4.1.14
    RELEASE=1

    DISTRO_BASE=ubuntu
    DISTRO_VER=xenial

    cd ~/deb-packaging/${DISTRO_BASE}-${DISTRO_VER}/openio-sds
    sed -i -e "s#\([_/]\)[0-9.]*\(orig\.\)\{0,1\}\(tar\.gz\)#\1${NEW_VERSION}.\2\3#g" ./sources
    dch --force-distribution -b -v ${NEW_VERSION}-${RELEASE} --distribution ${DISTRO_VER} 'New release'

    # Check everything is OK
    git diff ./sources ./debian/rules ./debian/changelog

    # Change first param to `sds-testing` or `sds-unstable`
    ../../oio-debbuild.py sds-17.04

## Setup build host

We are using pbuilder to build our packages, this guide will help you setup and create or update the packages for Debian and Ubuntu using this repository.
In this guide, we are using a Debian server to build our Debian and Ubuntu packages but it should work the same on an Ubuntu server.

### Setup a Debian based build server

See [here](https://github.com/open-io/oio-ansible-oldbuild/blob/master/build_hosts/deb/site.yml).

## Building packages

### Prequel

The pbuilder environment chroot tarballs should already be created.
More info [here](https://github.com/open-io/oio-ansible-oldbuild/blob/master/build_hosts/deb/files/create_build_envs.sh).

### Setup

In your user home directory, clone this repository:
`# git clone git@github.com:open-io/deb-packaging.git`

Create the building directory that will be used to create the Debian source package:
`# mkdir ~/debbuildir`

### Rebuilding a package

To rebuild the `openio-sds` package for Debian Jessie, change to the corresponding directory:
`# cd deb-packaging/debian-jessie/openio-sds`
Then run the command:
`# ../../oio-debbuild.sh`
This will download the source tarball in the `sources` file, create the Debian source package and run the pbuilder command that creates the packages.  
The resulting packages are in the `/var/cache/pbuilder/jessie-amd64/result/` directory.

### Updating a package

To update the `openio-sds` package for Debian Jessie, change to the corresponding directory:
`# cd deb-packaging/debian-jessie/openio-sds`
Change the `sources` file to the correct source tarball. The first field is the URL to download the tarball and the second field is the name of the source tarball (should match the convention *pkgname_pkgversion.orig.tar.gz*).  
Example of `sources` file:

```
https://github.com/open-io/oio-sds/archive/3.0.0.tar.gz openio-sds_3.0.0.orig.tar.gz
```

Then create a new changelog entry for the packages:
`# dch -b -v 3.0.0-1 --distribution jessie`

You are ready to run the `oio-debbuild.sh` that will download the source and build the package:
`# ../../oio-debbuild.sh`

### Adding the packages to a repository

If dput and mini-dinstall are configured, you can put the packages in the repository using the command:  
`# dput -u debian-openio-sds-testing /var/cache/pbuilder/jessie-amd64/result/openio-sds_*.changes`

### Repair the mirror / Remove a broken package

The method shown below has been replaced by a
[jenkins pipeline](https://jenkins.openio.io/job/oio-jenkins-ci/job/T_mirror_fix/),
but may still work:

    # Log on the build VM (OpenStack)
    ssh buildsys-deb
    # Go inside the mirror (NFS mounted directory from mirror2.openio.io)
    cd /mnt/koji/mirror/pub/repo/openio/sds/17.04/ubuntu
    # Remove the broken package(s)
    sudo rm -i xenial/openio-gridinit-1.7.0*
    # Delete the old metadata
    sudo rm -f xenial.db xenial/Packages* xenial/InRelease xenial/Sources* xenial/Release*
    # Re-create the metadatas
    sudo mini-dinstall --batch -c /etc/mini-dinstall-ubuntu-sds-17.04.conf /mnt/koji/mirror/pub/repo/openio/sds/17.04/ubuntu
    # Ask the QA team to double-check mirror2
    # Synchronize to the external mirror, if needed

*NOTE*: The DEB repositories only hold one package release, so you will have to rebuild the good/old one after that. 

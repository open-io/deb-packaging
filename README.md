# OpenIO Debian and Ubuntu packaging

This repository gathers the deb packaging files used to build OpenIO softwares.

## Setup

We are using pbuilder to build our packages, this guide will help you setup and create or update the packages for Debian and Ubuntu using this repository.
In this guide, we are using a Debian server to build our Debian and Ubuntu packages but it should work the same on an Ubuntu server.

### Setup a Debian based build server

Based on a minimal Debian server, install the following packages:
`# apt-get install pbuilder debootstrap dh-make ubuntu-archive-keyring devscripts`

Create a user to build your packages and add it to sudoers.

Add the following to your user's `~/.bashrc`

```
DEBEMAIL="name@email.com"
DEBFULLNAME="First Name Surname"
export DEBEMAIL DEBFULLNAME
```
In your root `/root/.pbuilderrc`:

```
#ALLOWUNTRUSTED=yes
AUTO_DEBSIGN=${AUTO_DEBSIGN:-no}
HOOKDIR=/var/cache/pbuilder/hook.d
#EXTRAPACKAGES=""

# Codenames for Debian suites according to their alias. Update these when
# needed.
UNSTABLE_CODENAME="sid"
TESTING_CODENAME="stretch"
STABLE_CODENAME="jessie"
STABLE_BACKPORTS_SUITE="$STABLE_CODENAME-backports"

# List of Debian suites.
DEBIAN_SUITES=($UNSTABLE_CODENAME $TESTING_CODENAME $STABLE_CODENAME $STABLE_BACKPORTS_SUITE
    "unstable" "testing" "stable")

# List of Ubuntu suites. Update these when needed.
UBUNTU_STABLE_CODENAME="xenial"
UBUNTU_SUITES=("trusty" "vivid" "wily" "xenial")

# Mirrors to use. Update these to your preferred mirror.
DEBIAN_MIRROR="ftp.fr.debian.org"
UBUNTU_MIRROR="mirrors.kernel.org"

# Optionally use the changelog of a package to determine the suite to use if
# none set.
if [ -z "${DIST}" ] && [ -r "debian/changelog" ]; then
    DIST=$(dpkg-parsechangelog | awk '/^Distribution: / {print $2}')
    # Use the unstable suite for certain suite values.
    if $(echo "experimental UNRELEASED" | grep -q $DIST); then
        DIST="$UNSTABLE_CODENAME"
    fi
    # Use the stable suite for stable-backports.
    if $(echo "$STABLE_BACKPORTS_SUITE" | grep -q $DIST); then
        DIST="$STABLE_CODENAME"
    fi
fi

# Optionally set a default distribution if none is used. Note that you can set
# your own default (i.e. ${DIST:="unstable"}).
: ${DIST:="$(lsb_release --short --codename)"}

# Optionally change Debian release states in $DIST to their names.
case "$DIST" in
    unstable)
        DIST="$UNSTABLE_CODENAME"
        ;;
    testing)
        DIST="$TESTING_CODENAME"
        ;;
    stable)
        DIST="$STABLE_CODENAME"
        ;;
esac

# Optionally set the architecture to the host architecture if none set. Note
# that you can set your own default (i.e. ${ARCH:="i386"}).
: ${ARCH:="$(dpkg --print-architecture)"}

NAME="$DIST"
if [ -n "${ARCH}" ]; then
    NAME="$NAME-$ARCH"
    DEBOOTSTRAPOPTS=("--arch" "$ARCH" "${DEBOOTSTRAPOPTS[@]}")
fi
if [ "$ARCH" == "arm64" ] && [ "$(dpkg --print-architecture)" != "arm64" ]; then
    DEBOOTSTRAP="qemu-debootstrap"
fi
BASETGZ="/var/cache/pbuilder/$NAME-base.tgz"
# Optionally, set BASEPATH (and not BASETGZ) if using cowbuilder
# BASEPATH="/var/cache/pbuilder/$NAME/base.cow/"
DISTRIBUTION="$DIST"
BUILDRESULT="/var/cache/pbuilder/$NAME/result/"
APTCACHE="/var/cache/pbuilder/$NAME/aptcache/"
BUILDPLACE="/var/cache/pbuilder/build/"
#BINDMOUNTS="/var/cache/archive"

if $(echo ${DEBIAN_SUITES[@]} | grep -q $DIST); then
    # Debian configuration
    MIRRORSITE="http://$DEBIAN_MIRROR/debian/"
    COMPONENTS="main contrib non-free"
    DEBOOTSTRAPOPTS=("${DEBOOTSTRAPOPTS[@]}" "--keyring=/usr/share/keyrings/debian-archive-keyring.gpg")
    OTHERMIRROR="$OTHERMIRROR | deb $MIRRORSITE $STABLE_BACKPORTS_SUITE $COMPONENTS"
    OTHERMIRROR="${OTHERMIRROR} | deb http://mirror.openio.io/pub/repo/openio/sds/16.10/debian $DIST/"

elif $(echo ${UBUNTU_SUITES[@]} | grep -q $DIST); then
    # Ubuntu configuration
    MIRRORSITE="http://$UBUNTU_MIRROR/ubuntu/"
    #MIRRORSITE="http://ports.ubuntu.com/ubuntu-ports/"
    COMPONENTS="main restricted universe multiverse"
    DEBOOTSTRAPOPTS=("${DEBOOTSTRAPOPTS[@]}" "--keyring=/usr/share/keyrings/ubuntu-archive-keyring.gpg")
    OTHERMIRROR="${OTHERMIRROR} | deb http://mirror.openio.io/pub/repo/openio/sds/16.10/ubuntu $DIST/"

else
    echo "Unknown distribution: $DIST"
    exit 1
fi
```

## Building packages

### Prequel

Before building your first packages, you need to create the tarball chroot for the targeted distribution. This base image contains the minimal packages used to create a chroot environment and the repository configuration that provides the packages dependencies required by the packages you'll build. As its prebuilt, it is fast, the drowback is that you'll need to refresh it when the repository changes.  

For a Debian Jessie, to create or rebuild the initial chroot (due to changes in your `.pbuilderrc` for example):  
`# sudo DIST=jessie pbuilder create`

You can simply update the environment by using:  
`# sudo DIST=jessie pbuilder update`


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





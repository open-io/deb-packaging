#!/bin/bash
set -e


if [ $# -ne 1 ]; then
  echo "You must specify a repository like <sds-testing>."
  exit 1
fi
REPO=$1

BASEDIR="$PWD"
PKGNAME=$(basename "$BASEDIR")
OSDISTRO=$(basename $(dirname "$BASEDIR"))
OSDISTCODENAME=${OSDISTRO//*-}
OSDISTID=${OSDISTRO//-*}

BASEWRK="$HOME/debbuildir"
if [ ! -d "$BASEWRK" ]; then
  echo "Working directory $BASEWRK doesnt exists."
  exit 1
fi
WRK="$BASEWRK/$OSDISTRO/$PKGNAME"

# Check if trying to build a Debian/Ubuntu package
if [ "$OSDISTID" != 'ubuntu' -a "$OSDISTID" != 'debian' ]; then
  echo "Unknown distribution"
  exit 1
fi

if [ ! -f sources ]; then
  echo "No sources file available in this directory."
  exit 1
fi

# Unpack in working dir
echo "### Creating working directory"
rm -rf "$WRK"
mkdir -p "$WRK"
#while IFS='' read -r src || [[ -n "$src" ]]; do
echo "### Downloading source files"
while read -r src filename dest taropt || [[ -n "$src" ]]; do
  if [[ "$src" =~ ^# ]]; then
    continue
  fi
  TAROPT=''
  if [ "${taropt}" == 'strip1' ]; then
    TAROPT="--strip-components 1"
  fi
  if [ "${dest}" == '-' ]; then
    dest=''
  fi
  if [[ "$src" =~ ^http ]] || [[ "$src" =~ ^ftp ]]; then
    wget "$src" -O "${WRK}/${filename}"
  else
    cp -a "$src" "${WRK}/${filename}"
  fi
  tar xf "$WRK/${filename}" -C "$WRK/${dest}" ${TAROPT}
done <sources

# Create the package now
pushd "$WRK" >/dev/null
pushd */ >/dev/null
echo "### Building source package"
cp -a "$BASEDIR/debian" ./
dpkg-buildpackage -S -us -uc -nc -d >/dev/null
popd >/dev/null
pkgdsc=$(ls *.dsc)
echo "### Starting building package"
sudo DIST="$OSDISTCODENAME" pbuilder build ${WRK}/*.dsc
echo "### Building done"
popd >/dev/null
echo
echo "### Uploading package $pkgdsc to repository ${OSDISTID}-openio-${REPO}"
dput -f -u ${OSDISTID}-openio-${REPO} /var/cache/pbuilder/${OSDISTCODENAME}-amd64/result/$(basename ${pkgdsc} .dsc)*.changes

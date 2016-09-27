#!/bin/bash
set -e


REPO=$1
if [ -n "$REPO" ]; then
  echo "You must specify a repository like sds-testing."
  exit 1
fi

BASEDIR="$PWD"
PKGNAME=$(basename "$BASEDIR")
OSDISTRO=$(basename $(dirname "$BASEDIR"))
OSDISTCODENAME=${OSDISTRO//*-}
OSDISTID=${OSDISTRO//-*}

BASEWRK="$HOME/packaging/workspace"
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
rm -rf "$WRK"
mkdir -pv "$WRK"
#while IFS='' read -r src || [[ -n "$src" ]]; do
while read -r src filename dest taropt || [[ -n "$src" ]]; do
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
pushd "$WRK"
pushd *
cp -a "$BASEDIR/debian" ./
dpkg-buildpackage -S -us -uc -nc -d
popd
pkgdsc=$(ls *.dsc)
echo sudo DIST="$OSDISTCODENAME" pbuilder build ${WRK}/*.dsc
popd
echo
echo dput -u ${OSDISTID}-openio-${REPO} /var/cache/pbuilder/${OSDISTCODENAME}-amd64/result/$(basename ${pkgdsc} .dsc)*.changes

#!/bin/bash
set -ex

#DISTID
#ARCH


if [ $# -ne 1 ]; then
  echo "You must specify a destination repository like <sds-testing>, " \
       "or <http://oio-repo.openio.io:5000/package>."
  exit 1
fi
REPO=$1

BASEDIR="$PWD"
PKGNAME=$(basename "$BASEDIR")
OSDISTRO=$(basename $(dirname "$BASEDIR"))
OSDISTCODENAME=${OSDISTRO//*-}
OSDISTID=${DISTID:-${OSDISTRO//-*}}
: ${ARCH:="$(dpkg --print-architecture)"}

BASEWRK="$HOME/debbuildir"
if [ ! -d "$BASEWRK" ]; then
  echo "Working directory $BASEWRK doesnt exists."
  exit 1
fi
WRK="$BASEWRK/$OSDISTRO/$PKGNAME"

# Check if trying to build a Debian/Ubuntu package
if [ "$OSDISTID" != 'ubuntu' -a "$OSDISTID" != 'debian' -a "$OSDISTID" != 'raspbian' ]; then
  echo "Unknown distribution"
  exit 1
fi

if [ ! -f sources ]; then
  echo "No sources file available in this directory."
  exit 1
fi

function uri_parser() {
    # uri capture
    uri="$@"

    # safe escaping
    uri="${uri//\`/%60}"
    uri="${uri//\"/%22}"

    # top level parsing
    pattern='^(([a-z]{3,5})://)?((([^:\/]+)(:([^@\/]*))?@)?([^:\/?]+)(:([0-9]+))?)(\/[^?]*)?(\?[^#]*)?(#.*)?$'
    [[ "$uri" =~ $pattern ]] || return 1;

    # component extraction
    uri=${BASH_REMATCH[0]}
    uri_schema=${BASH_REMATCH[2]}
    uri_address=${BASH_REMATCH[3]}
    uri_user=${BASH_REMATCH[5]}
    uri_password=${BASH_REMATCH[7]}
    uri_host=${BASH_REMATCH[8]}
    uri_port=${BASH_REMATCH[10]}
    uri_path=${BASH_REMATCH[11]}
    uri_query=${BASH_REMATCH[12]}
    uri_fragment=${BASH_REMATCH[13]}

    # path parsing
    count=0
    path="$uri_path"
    pattern='^/+([^/]+)'
    while [[ $path =~ $pattern ]]; do
        eval "uri_parts[$count]=\"${BASH_REMATCH[1]}\""
        path="${path:${#BASH_REMATCH[0]}}"
        ((count++))
    done

    # query parsing
    count=0
    query="$uri_query"
    pattern='^[?&]+([^= ]+)(=([^&]*))?'
    while [[ $query =~ $pattern ]]; do
        eval "uri_args[$count]=\"${BASH_REMATCH[1]}\""
        eval "uri_arg_${BASH_REMATCH[1]}=\"${BASH_REMATCH[3]}\""
        query="${query:${#BASH_REMATCH[0]}}"
        ((count++))
    done

    # return success
    return 0
}

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
  if [ -z "$filename" ]; then
    filename=$(basename $src)
  fi
  if [[ "$src" =~ ^http ]] || [[ "$src" =~ ^ftp ]]; then
    unset WGET_OPT
    #uri_parser ${src}
    if [ -r .token ]; then
      TOKEN=$(cat .token)
      if [ "${uri_host}" == *'github.com' ]; then
        echo "GitHub tokens are not supported yet!"
      elif [ "${uri_host}" == *'gitlab'* ]; then
        WGET_OPT="--header=\'PRIVATE-TOKEN: ${TOKEN}\'"
      else
        echo "Unsupported"
      fi
    fi
    wget --no-check-certificate "$src" ${WGET_OPT} -O "${WRK}/${filename}"
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
sudo ARCH="$ARCH" DISTID="$OSDISTID" DIST="$OSDISTCODENAME" pbuilder build ${WRK}/*.dsc
echo "### Building done"
popd >/dev/null

#if [[ "${REPO}" =~ ^http:// ]]; then
#    echo "### Uploading package $pkgdsc to repository ${REPO}"
#    for f in /var/cache/pbuilder/${OSDISTID}-${OSDISTCODENAME}-${ARCH}/result/$(basename ${pkgdsc} .dsc)*.deb; do
#        curl -F "file=@${f}" \
#             -F "company=${OIO_COMPANY}" \
#             -F "prod=${OIO_PROD}" \
#             -F "prod_ver=${OIO_PROD_VER}" \
#             -F "distro=${OSDISTID}" \
#             -F "distro_ver=${OSDISTCODENAME}" \
#             -F "arch=${ARCH}" \
#             "${REPO}"
#    done
#else
    echo "### Uploading package $pkgdsc to repository ${OSDISTID}-openio-${REPO}"
    if [ "${OSDISTID}" == 'ubuntu' -a "${ARCH}" == 'arm64' ]; then
      dput -f -u ${OSDISTID}-arm64-openio-${REPO} /var/cache/pbuilder/${OSDISTID}-${OSDISTCODENAME}-${ARCH}/result/$(basename ${pkgdsc} .dsc)*.changes
    else
      dput -f -u ${OSDISTID}-openio-${REPO} /var/cache/pbuilder/${OSDISTID}-${OSDISTCODENAME}-${ARCH}/result/$(basename ${pkgdsc} .dsc)*.changes
    fi
#fi

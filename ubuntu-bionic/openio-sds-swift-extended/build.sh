#!/bin/bash
set -x
cdate=$(date +%Y%m%d)
last_deb=$(ls -dt *_*.debian.tar.xz | head -n1)

if [ -n "$1" ]; then
  id=$1
else
  github_organization="open-io"
  repo_name="oio-swift"
  id=$(curl -s https://api.github.com/repos/${github_organization}/${repo_name}/commits/master | jq '.sha' | sed 's/"//g')
  echo "Setting up tarball with id ${id}"
fi

if [ ! -f *_${cdate}.git${id:0:7}.orig.tar.gz ]; then
  if [ ! -f ${id}.tar.gz ]; then
    wget https://github.com/open-io/oio-swift/archive/${id}.tar.gz
  fi
  mv ${id}.tar.gz openio-sds-swift-extended_${cdate}.git${id:0:7}.orig.tar.gz
fi

tar xf openio-sds-swift-extended_${cdate}.git${id:0:7}.orig.tar.gz
tar xf ${last_deb} -C *-${id}/

pushd *-${id}
dch --force-distribution -b -v ${cdate}.git${id:0:7}-1 --distribution xenial 'Testing'
dpkg-buildpackage -S -us -uc -nc
popd
echo "sudo DIST=xenial pbuilder build openio-sds-swift-extended_${cdate}.git${id:0:7}-1.dsc"

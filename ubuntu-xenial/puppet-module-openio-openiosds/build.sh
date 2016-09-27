#!/bin/bash
set -x

#github_organization="open-io"
github_organization="racciari"
repo_name="puppet-openiosds"
src=$repo_name
pkg=puppet-module-openio-openiosds
release=2


cdate=$(date +%Y%m%d)
last_deb=$(ls -dt ${pkg}_*.debian.tar.xz | head -n1)

if [ -n "$1" ]; then
  id=$1
else
  id=$(curl -s https://api.github.com/repos/${github_organization}/${repo_name}/commits/master | jq '.sha' | sed 's/"//g')
  echo "Setting up tarball with id ${id}"
fi

if [ ! -f ${pkg}_${cdate}.git${id:0:7}.orig.tar.gz ]; then
  if [ ! -f ${id}.tar.gz ]; then
    wget https://github.com/${github_organization}/${repo_name}/archive/${id}.tar.gz
  fi
  mv ${id}.tar.gz ${pkg}_${cdate}.git${id:0:7}.orig.tar.gz
fi

tar xf ${pkg}_${cdate}.git${id:0:7}.orig.tar.gz
tar xf ${last_deb} -C ${src}-${id}/

pushd ${src}-${id}
dch --force-distribution -b -v ${cdate}.git${id:0:7}-${release} --distribution xenial 'Testing'
dpkg-buildpackage -S -us -uc -nc
popd
echo "sudo DIST=xenial pbuilder build ${pkg}_${cdate}.git${id:0:7}-${release}.dsc"

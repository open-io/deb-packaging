#!/bin/bash
cid=4e60775548fcddb2babf38fdd895039945e4630f

rm -vf oio-fs.tar.gz
rm -vrf oio-fs
#git clone -v --depth 1 git@gitlab.openio.io:openio/oio-fs.git
#git clone --depth 1 git@gitlab.openio.io:jkasarherou/oio-fs.git
git clone -n git@gitlab.openio.io:openio/oio-fs.git
pushd oio-fs
  git checkout $cid
  git submodule update --init
  rm -rf .git
popd
tar zvcf oio-fs.tar.gz oio-fs

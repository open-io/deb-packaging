#!/bin/bash
cid=6be0fdcc97535bbb2363e7d08dd44c0792bfb962

rm -vf oio-fs.tar.gz
rm -vrf oio-fs
git clone -n git@gitlab.openio.io:openio/oio-fs.git
pushd oio-fs
  git checkout $cid
  git submodule update --init
  rm -rf .git
popd
tar zvcf oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz oio-fs
rm -vrf oio-fs

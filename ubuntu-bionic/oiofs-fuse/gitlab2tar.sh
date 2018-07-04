#!/bin/bash
#set -x

giturl="git@gitlab.openio.io:openio/oio-fs.git"

echo "###$1###"
if [ -n "$1" -a "$1" != ' ' ]; then
  cid=$1
else
  cid=master
fi

rm -vf oio-fs.tar.gz
rm -vrf oio-fs
git clone -n $giturl
pushd oio-fs
  git checkout tags/$cid
  git submodule update --init
  if [ "$cid" == "master" ]; then
    cid=$(git log --format="%H" -n 1)
  fi
  rm -rf .git
popd
if [ "$cid" == 'master' ]; then
  tar zvcf oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz oio-fs
  echo oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz  oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz >sources
else
  tar zvcf oiofs-fuse_${cid}.orig.tar.gz oio-fs
  echo oiofs-fuse_${cid}.orig.tar.gz oiofs-fuse_${cid}.orig.tar.gz >sources
fi
rm -vrf oio-fs

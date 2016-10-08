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
  git checkout $cid
  git submodule update --init
  rm -rf .git
  if [ "$cid" == "master" ]; then
    cid=$(git log --format="%H" -n 1)
  fi
popd
tar zvcf oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz oio-fs
rm -vrf oio-fs
echo oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz  oiofs-fuse_$(date +%Y%m%d%H%M).git${cid:0:7}.orig.tar.gz >sources

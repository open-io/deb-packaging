#!/bin/bash
set -xe

cdate=$(date +%Y%m%d)
github_organization="open-io";
repo_name="oio-fs";
if [ -r .token ]; then
  TOKEN=$(cat .token)
  curlauth="-u \"token:${TOKEN}\""
fi

if [ "$1" ]; then
  id=$1
else
  id=$(eval curl -s $curlauth https://api.github.com/repos/${github_organization}/${repo_name}/commits/master | jq '.sha' | sed 's/"//g');
  if [ $id == 'null' ]; then
    echo "Failed to get commit id"
    exit 1
  fi
fi
#if [ ! -f "${id}.tar.gz" ]; then
if [ ! -f oiofs-fuse_${cdate}.git${id:0:7}.orig.tar.gz ]; then
  eval curl -sL $curlauth https://github.com/${github_organization}/${repo_name}/archive/${id}.tar.gz >oiofs-fuse_${cdate}.git${id:0:7}.orig.tar.gz
#  tar xf ${id}.tar.gz ; rm -f ${id}.tar.gz ; 
  echo oiofs-fuse_${cdate}.git${id:0:7}.orig.tar.gz oiofs-fuse_${cdate}.git${id:0:7}.orig.tar.gz >sources
fi

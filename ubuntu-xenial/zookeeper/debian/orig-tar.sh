#!/bin/bash -e

VERSION=$2
TAR=../zookeeper_$VERSION.orig.tar.xz
DIR=zookeeper-$VERSION

# Unpack ready fo re-packing
mkdir -p $DIR
tar -xzf $3 -C $DIR --strip-components=1
rm $3

# Repack excluding stuff we don't need
XZ_OPT=--best tar -cvJf $TAR \
         --exclude '*.jar' \
         --exclude "Makefile.in" \
         --exclude "aclocal.m4" \
         --exclude "autom4te.cache" \
         --exclude "compile" \
         --exclude "config.guess" \
         --exclude "config.sub" \
         --exclude "configure" \
         --exclude "ltmain.sh" \
         --exclude "zookeeper-${VERSION}/contrib" \
         --exclude "zookeeper-${VERSION}/docs" \
         --exclude "zookeeper-${VERSION}/recipes" \
         --exclude "zookeeper-${VERSION}/dist-maven" \
         --exclude "zookeeper-${VERSION}/src/contrib/fatjar" \
         --exclude "zookeeper-${VERSION}/src/contrib/loggraph" \
         --exclude "zookeeper-${VERSION}/src/c/generated" \
         --exclude "zookeeper-${VERSION}/src/java/main/org/apache/jute/compiler/generated/*.java" \
         --exclude "zookeeper-${VERSION}/src/java/generated" \
         $DIR

rm -rf $DIR

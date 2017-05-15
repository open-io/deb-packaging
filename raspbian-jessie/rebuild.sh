#!/bin/bash
set -x

pkgname=$1
#repo_source=jessie-backports
repo_source=jessie
#repo_comp=main
repo_comp=non-free
mkdir -pv $pkgname
cd $pkgname

pkgdebian=$(wget -q https://packages.debian.org/source/${repo_source}/${pkgname} -O -|html2text -width 800|awk "/${pkgname}.*\.debian\./ {print \$1}")
wget -q "http://cdn-fastly.deb.debian.org/debian/pool/${repo_comp}/${pkgname:0:1}/${pkgname}/${pkgdebian}"
tar xf $pkgdebian
rm $pkgdebian

pkgorig=$(wget -q https://packages.debian.org/source/${repo_source}/${pkgname} -O -|html2text -width 800|awk "/${pkgname}.*\.orig\./ {print \$1}")
echo "http://cdn-fastly.deb.debian.org/debian/pool/${repo_comp}/${pkgname:0:1}/${pkgname}/${pkgorig}" >sources

sed -i -e '1 s@-backports@@' debian/changelog
sed -i -e '1 s@unstable@jessie@' debian/changelog

ARCH=armhf DISTID=raspbian ~/deb-packaging/oio-debbuild.sh sds-16.10

cd ..

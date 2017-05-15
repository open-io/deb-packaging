#!/bin/sh

PACKAGE=leveldb
BASE_REL=$(dpkg-parsechangelog 2>/dev/null | sed -ne 's/Version: \([0-9.]\+\)\+.*/\1/p')
OLDDIR=${PWD}
GOS_DIR=${OLDDIR}/get-orig-source
GIT_COMMIT_STR='git log --no-color -1 --oneline | cut -d" " -f1'
GIT_DATE_STR='git log --no-color -1 --date=iso | sed -ne "s/Date:\s\+\(.*\).*/\1/p" | cut -d" " -f1 | tr -d "-"'

if [ -z ${BASE_REL} ]; then
	echo 'Please run this script from the sources root directory.'
	exit 1
fi


rm -rf ${GOS_DIR}
mkdir ${GOS_DIR} && cd ${GOS_DIR}
git clone http://code.google.com/p/leveldb/ ${PACKAGE}
cd ${PACKAGE}/
GIT_COMMIT=$(eval "${GIT_COMMIT_STR}")
GIT_DATE=$(eval "${GIT_DATE_STR}")
cd .. && tar cjf \
	${OLDDIR}/${PACKAGE}_${BASE_REL}+${GIT_DATE}.git${GIT_COMMIT}.orig.tar.bz2 \
	${PACKAGE} --exclude-vcs
rm -rf ${GOS_DIR}

#!/bin/sh

test_description="functions"

. ./sharness.sh

test_expect_success "update-alternatives" "
  update-alternatives --list puppet-module-stdlib
"

test_done

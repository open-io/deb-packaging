#!/bin/sh

test_description="functions"

. ./sharness.sh

fixtures=../fixtures

test_expect_success "functions" "
    puppet apply ${fixtures}/functions.pp
"

test_done

#!/bin/bash

set -e

PATH="$HOME/.local/bin:$PATH"

sh /unittesting.sh bootstrap

echo 'bootstrap finished'

if xvfb-run sh -c 'echo $DISPLAY' -e '/tmp/error.txt'; then
	true
else
	cat /tmp/error.txt
	false
fi

xvfb-run sh /unittesting.sh run_tests --coverage

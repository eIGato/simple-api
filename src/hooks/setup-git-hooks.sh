#!/usr/bin/env bash
set -ex

if [ -d .git ]; then
    GIT_DIR='.git'
else
    GIT_DIR=`awk '{print $2}' .git`
fi
rm -f $GIT_DIR/hooks/pre-commit
ln -s ../../src/hooks/pre-commit.sh $GIT_DIR/hooks/pre-commit

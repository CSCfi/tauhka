#!/bin/bash
################################################################
# This contains the TauhkaTestCase.
#
# This file is part of Tauhka project.
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright (c) 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
# ----
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################
set -e

NEXT_RELEASE=$1

function usage() {
  echo "---------------"
  echo "USAGE: $0 [next_release]"
  echo "EXAMPLE: $0 0.0.3"
  echo "---------------"
  echo
}

CURRENT_BRANCH=`git branch|grep "\*"|sed "s/\* //g"`
if [[ ${CURRENT_BRANCH} != "next" ]]; then
  echo "ERROR: this can be ran only on next branch."
  usage
  exit 2
fi

echo
echo "Lets ensure that master and next branches are up to date."
git pull
git checkout master
git pull
git checkout next
echo "..done"
echo

CURRENT_RELEASE=`python -c "from tauhka import __version__; print(__version__)"`
echo "This tool will do release tag for ${CURRENT_RELEASE}."
echo "After that tag is pushed, the next release will be set for packaging."
echo
echo "Tags:"
git tag
echo

if [[ -z ${NEXT_RELEASE} ]]; then
  echo "Current release is ${CURRENT_RELEASE}."
  echo -n "Next Release: "
  read NEXT_RELEASE
fi

if [[ !("${NEXT_RELEASE}" =~ ^[0-9.]*$) ]]; then
  usage
  echo "ERROR: Invalid release number"
  exit 3
fi

git tag -a v${CURRENT_RELEASE} -m "version ${CURRENT_RELEASE}"

echo
echo "The version ${CURRENT_RELEASE} has been tagged."
echo "Press <enter> to push tags to remove, or <ctrl+c> to cancel."
read
git push -u origin v${CURRENT_RELEASE}

echo
echo "Merge next to master."
git checkout master
git pull
git merge next
git push -u origin master
git checkout next
git pull
echo "..done"
echo

echo
echo "The tag has been released."
sed -i ".bak" "s/__version__ = \"[0-9.]*\"/__version__ = \"${NEXT_RELEASE}\"/g" tauhka/__init__.py
echo "The next version has been set."
echo

git add tauhka/__init__.py
git commit -a -m "Version number bump to v${NEXT_RELEASE}."
git push -u origin next

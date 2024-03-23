#!/bin/bash

cd $REPO_PATH

pip3 install -r .upbase/requirements.txt

python3 ../.upbase.py

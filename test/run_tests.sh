#!/bin/bash
script_dir=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$script_dir/..:$PATH:$PYTHONPATH
python3 -u -m unittest discover -p "*_test.py"

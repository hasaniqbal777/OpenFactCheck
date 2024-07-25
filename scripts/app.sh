#!/bin/bash

# Script for running openfactcheck
#
# Examples
# --------
# $ ./run.sh
#

source "${BASH_SOURCE%/*}/common.sh"

# Executing Python script
export PYTHONPATH="$PYTHONPATH:src/"
gradio src/openfactcheck/app/app.py --demo-name=demo
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
streamlit run src/openfactcheck/app/app.py -- "$@"
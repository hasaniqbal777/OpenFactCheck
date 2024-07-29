#!/bin/bash

################################################################################
# Shell dependencies                                                           #
################################################################################
# https://stackoverflow.com/questions/592620/how-can-i-check-if-a-program-exists-from-a-bash-script

if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed.' >&2
  exit 1
fi

if ! [ -x "$(command -v bump2version)" ]; then
  echo 'Error: bump2version is not installed.' >&2
  exit 1
fi

################################################################################
# Common Functions                                                             #
################################################################################

# Echo's the text to the screen with the designated color
c_echo () {
    local color=$1
    local txt=$2

    echo -e "${color}${txt}${NC}"
}

# Enforces you are running from project root
force_project_root () {
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    PARENT_DIR=$(dirname $DIR)

    if [ "$(pwd)" != $PARENT_DIR ]
    then
        c_echo $RED "You must be in $PARENT_DIR to run"
        exit 1
    fi
}

################################################################################
# Color Constants                                                              #
################################################################################
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

################################################################################
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ENFORCE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
################################################################################
force_project_root

################################################################################
# Application Versioning Information                                           #
################################################################################
APP_NAME=openfactcheck
APP_VERSION=$(git describe --tags --dirty) || exit 1
COMMIT=$(git rev-parse HEAD)

################################################################################
# Common Paths                                                                 #
################################################################################
BUILDBIN_PATH=$(pwd)/tmp/build/bin
DEPLOYMENTS_PATH=$(pwd)/deployments
TERRAFORM_PATH=$(pwd)/deployments/terraform
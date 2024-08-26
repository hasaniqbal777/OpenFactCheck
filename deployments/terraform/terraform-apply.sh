#!/bin/bash

source "${BASH_SOURCE%/*}/../../scripts/common.sh"

if [ -z "$1" ] ; then
    c_echo $RED "Need to provide the ENVIRONMENT as first argument. \n"
    c_echo $YELLOW "Usage: $0 <environment> [auto]"
    exit 1
fi

c_echo $GREEN "
--------------------------------------------------------------------------------
--                           Deploying Terraform                              --
--------------------------------------------------------------------------------
"

INPUT_FALSE=""
AUTO_APPROVE=""
if [ "$2" = "auto" ] ; then
    c_echo $YELLOW "Auto approval set..."
    INPUT_FALSE="-input=false"
    AUTO_APPROVE="-auto-approve"
fi

ENVIRONMENT=$1

AWS_ACCOUNT_NAME=$(cat environments/${ENVIRONMENT}.tfvars.json | jq .aws_account_name | tr -d '"')

if [ -z "$AWS_ACCOUNT_NAME" ] ; then
    c_echo $RED "There was a problem loading Account Name configuration from file environments/${ENVIRONMENT}.tfvars.json"
    exit 1
fi

echo "Account:"
cat environments/${ENVIRONMENT}.tfvars.json 

pushd deployments/terraform > /dev/null

    terraform init -reconfigure -backend-config=../../accounts/${AWS_ACCOUNT_NAME}.backend.conf $INPUT_FALSE
    if [ "$?" -ne "0" ]; then
        echo "Error in initing the terraform!"
        exit 1
    fi

    echo
    terraform workspace select -or-create $ENVIRONMENT
    if [ "$?" -ne "0" ]; then
        echo "Error in selecting workspace!"
        exit 1
    fi

    echo
    echo "Workspaces:"
    terraform workspace list
    if [ "$?" -ne "0" ]; then
        echo "Error in listing workspaces!"
        exit 1
    fi

    terraform apply -var-file=../../environments/${ENVIRONMENT}.tfvars.json $INPUT_FALSE $AUTO_APPROVE
    if [ "$?" -ne "0" ]; then
        echo "Error in terraform apply!"
        exit 1
    fi

popd > /dev/null
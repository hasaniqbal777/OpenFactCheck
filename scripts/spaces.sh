#!/bin/bash

source "${BASH_SOURCE%/*}/common.sh"

READMEFILE="README.md"

# Replace "<!--" and "-->" with "---" in README.md file
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/<!--/---/g; s/-->/---/g' $READMEFILE
else
    sed -i 's/<!--/---/g; s/-->/---/g' $READMEFILE
fi

# Commit changes
git add $READMEFILE
git commit -m "Uncommented HuggingFace Spaces Configuration"
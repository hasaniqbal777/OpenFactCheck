#!/bin/bash

source "${BASH_SOURCE%/*}/../../scripts/common.sh"

# Configurable variables
ROOT=$(realpath "$(dirname "${BASH_SOURCE[0]}")/../..")
WEBSITE_HOME="https://openfactcheck.readthedocs.io/en"
DOCS_HOME="docs"
DOCS_LATEST="latest"
DOCS_ROOT="$ROOT/$DOCS_HOME"
DOCS_DEST="$ROOT/public"
VERSION_FILE="$DOCS_ROOT/src/_static/versions.json"

# Formats a version entry
function format_version_entry {
    local version=$1
    echo "{\"name\": \"$version\", \"version\": \"v$version\", \"url\": \"$WEBSITE_HOME/v$version/\"}"
}

# Formats the development version entry
function format_dev_version_entry {
    echo "{\"version\": \"dev\", \"url\": \"$WEBSITE_HOME/latest/\"}"
}

# Formats the stable version entry
function format_stable_version_entry {
    local version=$1
    echo "{\"name\": \"$version (stable)\", \"version\": \"v$version\", \"url\": \"$WEBSITE_HOME/stable/\", \"preferred\": true}"
}

# Retrieves versions from versions.json
function get_versions {
    jq -r '.[] | .name' "$VERSION_FILE"
}

# Generate the version.json file
function generate_versions_file {
    local versions=$(get_versions)
    local entries=($(format_dev_version_entry))
    
    for version in $versions; do
        entries+=($(format_version_entry "$version"))
    done

    echo "${entries[@]}" | jq -s '.' > "$DOCS_DEST/version.json"
}

# Initialize default values
dry_run=0
new_version=""

# Function to show help message
function show_help {
    echo "Usage: $0 [-d|--dryrun] -n|--new-version <version>"
    echo "  -d, --dryrun: Dry run; do not write any changes, just print the output."
    echo "  -n, --new-version: Specify the new version to be added. This is a required argument."
}

# Manual parsing of command-line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        (-d|--dryrun)
            dry_run=1
            shift
            ;;
        (-n|--new-version)
            if [[ -n "$2" ]]; then
                new_version="$2"
                shift 2
            else
                echo "Error: Argument for $1 is missing."
                show_help
                exit 1
            fi
            ;;
        (-h|--help)
            show_help
            exit 0
            ;;
        (*)
            echo "Invalid option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if new version was specified
if [[ -z "$new_version" ]]; then
    echo "Error: -n|--new-version is required."
    show_help
    exit 1
fi

# Check if new version was specified
if [[ -z "$new_version" ]]; then
    echo "Error: -n new_version is required."
    show_help
    exit 1
fi

# Check the last stable version
current_versions=$(get_versions)
stable_version=$(echo "$current_versions" | tail -n +2 | head -n 1 | cut -d' ' -f1)
echo "Last Stable version: $stable_version"

# Check the old versions
old_versions=($(echo "$current_versions" | tail -n +3))
old_versions+=("$stable_version")
old_versions=($(printf '%s\n' "${old_versions[@]}" | tac))
echo "Old versions: ${old_versions[*]}"

# Create new version entry
if echo "${old_versions[@]}" | grep -q "$new_version"; then
    echo "Version $new_version already exists in versions.json"
    exit 1
fi

entries=( $(format_dev_version_entry) $(format_stable_version_entry "$new_version") )
for version in ${old_versions[@]}; do
    entries+=( $(format_version_entry "$version") )
done

if [ "$dry_run" -eq 1 ]; then
    echo "$(echo ${entries[@]} | jq -s '.')"
else
    echo "Writing to versions.json"
    echo "$(echo ${entries[@]} | jq -s '.')" > "$VERSION_FILE"
fi
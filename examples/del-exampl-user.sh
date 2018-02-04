#!/bin/bash
ex_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
templ_dir="$ex_dir/templates"

echo '@Listing available templates'
# You can add additional directories to the template search path
# with --dir=/template/directory
isna ls temp --dir="$templ_dir" 

echo '@Listing variables in template delete-user.yml'
isna ls vars delete-user.yml

echo '@Deleting user woofdawg'
# stdin and --vars can also be json objects
echo '{"username": "woofdawg"}' | isna --sudo=root delete-user.yml


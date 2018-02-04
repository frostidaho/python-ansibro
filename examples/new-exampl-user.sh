#!/bin/bash
ex_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
templ_dir="$ex_dir/templates"

echo '@Listing available templates'
isna ls temp

echo '@Listing variables in template create-user.yml'
isna ls vars create-user.yml

echo '@Creating user woofdawg on localhost'
# There are three ways of passing template variables to isna
# 1.) --vars
# 2.) stdin
# 3.) prompting user if variable was not given in either 1.) or 2.)
isna --vars='username=woofdawg; is_admin=no' --sudo=root create-user.yml

echo "@Cloning a git repo into woofdawg's home dir"
echo 'username=woofdawg' | isna $templ_dir/git-simple.yml --sudo=woofdawg

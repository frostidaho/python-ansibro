#!/bin/bash
ex_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
templ_dir="$ex_dir/templates"

echo @Listing available templates
isna -lt

echo @Listing variables in template user-create.yml
isna -lv user-create.yml

echo @Creating user woofdawg
# You can either pass template variables with -e KEY VALUE
# or you will be prompted for them
isna user-create.yml -u -e username woofdawg -e is_admin no
# -u with no args is the same as -u root,sudo,no
# i.e., sudo to root & do not ask for the sudo password

echo "@Cloning a git repo into woofdawg's home dir"
isna $templ_dir/git-simple.yml -u -e username woofdawg

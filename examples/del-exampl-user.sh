#!/bin/bash
echo @Listing available templates
isna -lt

echo @Listing variables in template user-delete.yml
isna -lv user-delete.yml

echo @Deleting user woofdawg
isna user-delete.yml -u sudo,root,no -e username woofdawg
# -u with no args is the same as -u sudo,root,no
# i.e., sudo to root & do not ask for the sudo password


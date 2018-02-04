#!/bin/bash
ex_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
templ_dir="$ex_dir/templates"

gen_pw () {
    head /dev/urandom | tr -dc A-Za-z0-9 | head -c10
}

echo '@Listing available templates'
isna ls temp --dir="$templ_dir"

echo '@Listing variables in template create-user.yml'
isna ls vars create-user.yml

EXPW=$(gen_pw)
echo "@Creating user woofdawg on localhost with password: $EXPW"
# There are three ways of passing template variables to isna
# 1.) --vars
# 2.) stdin
# 3.) prompting user if variable was not given in either 1.) or 2.)
echo "username=woofdawg; new_usr_password=$EXPW" | isna --vars='is_admin=no' --sudo=root create-user.yml

echo "@Cloning multiple git repos into woofdawg's home dir"
# http://stackoverflow.com/a/23930212
isna $templ_dir/git-multiple.yml --sudo=woofdawg <<EOF
git_repos_to_clone=[ 
  { "repo": "https://github.com/githubtraining/github-games.git", "dest": "~/isna_exampls/github_games" },
  { "repo": "https://github.com/githubtraining/example-rebase-orphan-branch.git", "dest": "~/isna_exampls/orphan" }
]
EOF

xsel -b <<< "$EXPW"
echo "@Copied woofdawg's password $EXPW to clipboard"

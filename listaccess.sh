#!/usr/bin/env bash
gh run list --json databaseId --jq '.[].databaseId' --limit ${1:-20} |
    xargs -I % -P0 sh -c "gh run view --log % | grep Grant/revoke | tail -n+14 | cut -d$'\t' -f3-" |
    sort -rg

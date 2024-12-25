#!/bin/bash

set -eu

# How do I get the directory where a Bash script is located from within the script itself?
# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd ${SCRIPT_DIR}/..

# Looping through the content of a file in Bash
# https://stackoverflow.com/questions/1521462/looping-through-the-content-of-a-file-in-bash
while read language; do      
  python apps/scrape.py \
    --language   "${language}" \
    --date_range "daily" \
    --output     "./docs/feeds/${language}/daily.atom" \

  sleep 1 # 1s 

done < ./urls.txt

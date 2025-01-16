#!/bin/bash

set -u
set -e

# How do I get the directory where a Bash script is located from within the script itself?
# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd ${SCRIPT_DIR}/..

# Looping through the content of a file in Bash
# https://stackoverflow.com/questions/1521462/looping-through-the-content-of-a-file-in-bash
while read language; do      
  # urls.txtで各行冒頭『#』でコメントアウトできるようにした
  if [[ ! $language =~ ^# ]]; then

    set +e
    python apps/scrape.py \
      --language          "${language}" \
      --period            "monthly" \
      --atom-updated-date "$(date -I)T00:00:00" \
      --output            "./docs/feeds/${language}/monthly.atom"
    set -e

     sleep 1 # 1s 
  fi
done < ./urls.txt

#!/bin/bash

set -u
set -e

# How do I get the directory where a Bash script is located from within the script itself?
# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd ${SCRIPT_DIR}/..

# Looping through the content of a file in Bash
# https://stackoverflow.com/questions/1521462/looping-through-the-content-of-a-file-in-bash
while read language; do
	# languages.txtで各行冒頭『#』でコメントアウトできるようにした
	if [[ ! $language =~ ^# ]]; then
		mkdir -p "./docs/feeds/${language}/"

		# 一時的なエラーなどで取得が失敗すると、後続の取得まで全部できなくなるので、ここだけset -eを解除
		set +e
		uv run apps/scrape.py \
			--language "${language}" \
			--period "weekly" \
			--atom-updated-date "$(date -I)T00:00:00" \
			--output "./docs/feeds/${language}/weekly.atom"
		set -e

		sleep 1 # 1s
	fi
done <./languages.txt

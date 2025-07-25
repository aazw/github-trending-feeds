#!/bin/bash

set -u
set -e

# How do I get the directory where a Bash script is located from within the script itself?
# https://stackoverflow.com/questions/59895/how-do-i-get-the-directory-where-a-bash-script-is-located-from-within-the-script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd ${SCRIPT_DIR}/..

url_decode() {
	local encoded="$1"
	printf '%b' "${encoded//%/\\x}"
}

# Looping through the content of a file in Bash
# https://stackoverflow.com/questions/1521462/looping-through-the-content-of-a-file-in-bash
while read language; do
	# languages.txtで各行冒頭『#』でコメントアウトできるようにした
	if [[ ! $language =~ ^# ]]; then
		language_decoded=$(url_decode "$language")

		mkdir -p "./docs/feeds/${language_decoded}/"

		# 一時的なエラーなどで取得が失敗すると、後続の取得まで全部できなくなるので、ここだけset -eを解除
		set +e
		uv run src/scrape_trending.py \
			--language "${language}" \
			--period "daily" \
			--atom-updated-date "$(date -I)T00:00:00" \
			--output "./docs/feeds/${language_decoded}/daily.atom"
		set -e

		sleep 1 # 1s
	fi
done <./languages.txt

# github-trending-feeds

[English](README.md) | 日本語

## 概要

GitHub Trendingのページをスクレイピングして、RSSリーダー(Inoreader等)で読み込める**ATOM**を提供する.

データソース:  
GitHub Trending: <https://github.com/trending>

公開先:  
GitHub Pages: <https://aazw.github.io/github-trending-feeds-data/>

## 関連リポジトリ

### <https://github.com/aazw/github-trending-feeds>

- 本リポジトリ
- GitHub Trendingのページをスクレイピングし、ATOMを生成するスクリプトを管理
- 上記スクリプトをGitHub Actionsで動かして、ATOMを生成

### <https://github.com/aazw/github-trending-feeds-data>

- 上記リポジトリにてGitHub Actionsで生成したATOMを管理する
- Github Pages

## GitHub Actions

GitHub Actionsのscheduleで各言語のTrendingの最新情報を取得する.  

各種HPおよびInternet Archiveの履歴から、GitHub Trendsの更新は10:00〜11:00 UTC ごろと思われる.  
<https://web.archive.org/web/20250000000000*/https://github.com/trending>

この情報をもとに、以下のようなスケジュールでCron Jobを実行する.

### Cron Jobs

- Daily
  - 毎日 15:00 UTC
    - = 24:00 JST
  - なぜ11:00ではない？
    - 必ず11:00までに更新される保証はなく、11:00過ぎの可能性もある
    - 10:00 UTC = 20:00 JST でありあと少しで日付が変わるタイミングなので、だったら日付が変わったタイミングで実行しようとなった

- Weekly
  - 毎週月曜日 16:00 UTC
    - = 25:00 JST
  - 16:00 UTCなのは、Dailyの分と処理が重ならないようにするため

- Monthly
  - 毎月1日 17:00 UTC
    - = 26:00 JST
  - 17:00 UTCなのは、Dailyの分と、時にWeeklyの分とも処理が重ならないようにするため

## 利用方法

### 実行環境セットアップ

```bash
task uv_sync
```

### スクレイピング実行

```bash
uv run src/scrape_trending.py 
      --language   go \
      --period daily \
      --output     ./daily.atom
```

helpコマンド実行例.

```bash
$ uv run src/scrape_trending.py --help
2024-12-26 14:20:01,055 - /workspaces/github-trending-feeds/src/scrape_trending.py:176 - INFO - start app
Usage: scrape_trending.py [OPTIONS]

Options:
  --language TEXT                 [required]
  --period [daily|weekly|monthly]
                                  [required]
  --output TEXT
  --atom_updated_date TEXT
  --verbose
  --help                          Show this message and exit.
2024-12-26 14:20:01,056 - /workspaces/github-trending-feeds/src/scrape_trending.py:194 - INFO - app finished
```

ATOMの日時を上書きすることもできる.

```bash
uv run src/scrape_trending.py --language go --period "daily" --atom-updated-date "$(date -I)T00:00:00" --output test.atom
```

### 過去の全ATOMを走査し、過去登場したリポジトリのURL一覧をつくる

```bash
uv run src/unique_list.py --dir docs/feeds --output urls.txt
```

- `--dir`
  - 走査するディレクトリ
  - サブディレクトリも含め、*.atomなファイルを走査する
  - 通常は `docs`ディレクトリ
- `--output`
  - URL全一覧を出力する先

### 指定のATOMにて、過去にないリポジトリがあればそれのURLの一覧を取得する

```bash
uv run src/new_arrivals.py --atom docs/feeds/go/daily.atom --urls urls.txt

uv run src/new_arrivals.py --atom docs/feeds/go/daily.atom --urls urls.txt --format atom

uv run src/new_arrivals.py --atom docs/feeds/go/daily.atom --urls urls.txt --format atom --output docs/new-arrivals/go/daily.atom
```

- `--atom`
  - チェックするATOM
- `--urls`
  - 過去のURL全一覧
- `--format`
  - `--format=plain`: URL一覧だけを出力する
  - `--format=atom`: 新着URLだけのATOMを出力する
- `--output`
  - 出力先ファイルパス
  - 指定した場合のみ、ファイルに出力する
  - 指定しなかった場合、標準出力に出力する

### Return Code / Exit Status

- `-1`: Unknown Error
- `0`: 正常終了
- `11`: InvalidURL
- `12`: ConnectionError
- `13`: タイムアウト系 (Timeout, ConnectTimeout, ReadTimeout)
- `14`: TooManyRedirects
- `15`: ステータスコード 400系
- `16`: ステータスコード 500系
- `17`: ステータスコード 400系、500系以外
- `18`: そのほかrequests系のエラー
- `31`: FileNotFoundError
- `32`: IsADirectoryError
- `33`: PermissionError
- `34`: OSError

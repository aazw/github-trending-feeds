# github-trending-feeds

GitHub Trendingのページをスクレイピングして、RSSリーダー(Inoreader等)で読み込める**ATOM**を提供する.

* GitHub Trending: https://github.com/trending
* GitHub Pages: https://aazw.github.io/github-trending-feeds/

このプロジェクトは2024/12/24にスタートした。

## Actions

GitHub Actionsで各言語のTrendingの最新情報を取得する.

* Daily
  * 毎日 11:00 UTC
    * 20:00 JST

* Weekly
  * 毎週月曜日 12:00 UTC
    * 21:00 JST
  * 12:00 UTCなのは、Dailyの分と処理が重ならないようにするため

* Monthly
  * 毎月1日 13:00 UTC
    * 22:00 JST
  * 13:00 UTCなのは、Dailyの分と、時にWeeklyの分とも処理が重ならないようにするため


## Use

```bash
pip install -r requirements.txt
```

```bash
python apps/scrape.py 
      --language   go \
      --period daily \
      --output     ./daily.atom
```

```bash
$ python apps/scrape.py --help
2024-12-26 14:20:01,055 - /workspaces/github-trending-feeds/apps/scrape.py:176 - INFO - start app
Usage: scrape.py [OPTIONS]

Options:
  --language TEXT                 [required]
  --period [daily|weekly|monthly]
                                  [required]
  --output TEXT
  --atom_updated_date TEXT
  --verbose
  --help                          Show this message and exit.
2024-12-26 14:20:01,056 - /workspaces/github-trending-feeds/apps/scrape.py:194 - INFO - app finished
```

```bash
$ python apps/scrape.py --language go --period "daily" --atom-updated-date "$(date -I)T00:00:00" --output test.atom
```

## Return Code / Exit Status

* -1 ... Unknown Error
* 0 ... 正常終了
* 1 ... ConnectionError
* 2 ... HTTPError
* 3 ... タイムアウト系 (Timeout, ConnectTimeout, ReadTimeout)
* 4 ... InvalidURL
* 5 ... TooManyRedirects
* 11 ... ステータスコード 400系
* 12 ... ステータスコード 500系
* 13 ... ステータスコード 400系、500系以外
* 21 ... FileNotFoundError
* 22 ... IsADirectoryError
* 23 ... PermissionError
* 24 ... OSError

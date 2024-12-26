# github-trending-feeds

GitHub Trendingのページをスクレイピングして、RSSリーダー(Inoreader等)で読み込めるATOMを提供する.

* GitHub Trending: https://github.com/trending
* GitHub Pages: https://aazw.github.io/github-trending-feeds/


## Feed Format

Feed: ウェブサイトやブログが提供する更新情報の配信フォーマットのこと

* RSS
  * 1999年頃
  * 非公式標準
  * 複数のバージョンが存在
    * 1.0、2.0ほか
  * 現在の主流は RSS 2.0
  * 開発元は元々Netscapeが関与したが、後に複数の団体が関連
  * XMLベース
  * シンプルな構造
	* 基本的なメタデータを提供
    * タイトル、リンク、説明
	* 時間情報などのフィールドが限定されている
* Atom
  * 2003年
  * IETFの公式標準(RFC 4287)
    * https://www.ietf.org/rfc/rfc4287.txt
    * https://tex2e.github.io/rfc-translater/html/rfc4287.html
  * RSSの問題点(例えばバージョン管理の混乱)を解決するために設計
  * 一貫した設計思想が特徴
  * 2つの仕様がある
    * Atom配信フォーマット (Atom Syndication Format)
      * コンテンツを配信するためのフィードのフォーマットを規定
      * XMLベース
      * RSSよりも柔軟性が高く、データの表現力が豊富
	    * 名前空間(namespace)の使用が標準化される
      * ISO 8601形式のタイムスタンプ（日時）が標準で使用可能
	    * エントリごとに一意のID(<id>タグ)が必須
      * タグやリンクの記述に柔軟性があり、複数リンクをサポート
    * Atom出版プロトコル (Atom Publishing Protocol)
      * ウェブ上のコンテンツを編集するためのプロトコル
      * Atom APIまたはAtomPPなどとも
      * https://tex2e.github.io/rfc-translater/html/rfc5023.html


## Use

```bash
pip install -r requirements.txt
```

```bash
python apps/scrape.py 
      --language   go \
      --date_range daily \
      --output     ./daily.atom
```

```bash
 $ python apps/scrape.py --help
2024-12-26 14:20:01,055 - /workspaces/github-trending-feeds/apps/scrape.py:176 - INFO - start app
Usage: scrape.py [OPTIONS]

Options:
  --language TEXT                 [required]
  --date_range [daily|weekly|monthly]
                                  [required]
  --output TEXT
  --atom_updated_date TEXT
  --verbose
  --help                          Show this message and exit.
2024-12-26 14:20:01,056 - /workspaces/github-trending-feeds/apps/scrape.py:194 - INFO - app finished
```

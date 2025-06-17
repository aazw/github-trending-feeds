import sys
import traceback
import logging
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib3.util.retry import Retry
import warnings
from enum import Enum

import click
import dateparser
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (  # https://requests.readthedocs.io/en/latest/_modules/requests/exceptions/
    RequestException,
    HTTPError,
    ConnectionError,
    Timeout,
    ConnectTimeout,
    ReadTimeout,
    InvalidURL,
    TooManyRedirects,
)
from bs4 import BeautifulSoup


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup logging with proper handler management."""
    logger = logging.getLogger(__name__)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter("%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s")
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(level)
    
    return logger

appLogger = setup_logging()


class ReturnCode(Enum):
    UNKNOWN_ERROR = -1
    SUCCESS = 0
    INVALID_URL_ERROR = 11
    CONNECTION_ERROR = 12
    TIMEOUT_ERROR = 13
    TOO_MANY_REDIRECTS_ERROR = 14
    HTTP_400_ERROR = 15
    HTTP_500_ERROR = 16
    HTTP_ERROR = 17
    REQUESTS_ERROR = 18
    FILE_NOT_FOUND_ERROR = 31
    IS_DIRECTORY_ERROR = 32
    PERMISSION_ERROR = 33
    OS_ERROR = 34


@click.command()
@click.option("--language", type=str, required=True, help="")
@click.option("--period", type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=True), required=True, help="")
@click.option("--output", type=str, required=False, help="")
@click.option("--atom-updated-date", type=str, required=False, help="")
@click.option("--verbose", is_flag=True, default=False, show_default=True, help="")
@click.option("--timeout", type=int, default=10, hidden=True, help="")
def main(language: str, period: str, output: str, atom_updated_date: str, verbose: bool, timeout: int):
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --language = {language}")
    appLogger.info(f"command-line argument: --period = {period}")
    appLogger.info(f"command-line argument: --output = {output}")
    appLogger.info(f"command-line argument: --atom-updated-date = {atom_updated_date}")
    appLogger.info(f"command-line argument: --verbose = {verbose}")

    if verbose:
        appLogger.setLevel(logging.DEBUG)

    if not verbose:
        # https://stackoverflow.com/questions/879173/how-to-ignore-deprecation-warnings-in-python
        # 以下のような警告が出るのを防ぐ
        # ... : DeprecationWarning: Parsing dates involving a day of month without a year specified is ambiguious
        # and fails to parse leap day. The default behavior will change in Python 3.15
        # to either always raise an exception or to use a different default year (TBD).
        # To avoid trouble, add a specific year to the input & format.
        # See https://github.com/python/cpython/issues/70647.
        #   updated = dateparser.parse(atom_updated_date)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    ### initialize phase ##############################################################

    # url
    url = f"https://github.com/trending/{language}?since={period}"
    appLogger.info(f"generated: url = {url}")

    # atom_title
    atom_title = f"GitHub Trending - {language} ({period})"
    appLogger.info(f"generated: atom_title = {atom_title}")

    # atom_author
    atom_author = "aazw"
    appLogger.info(f"generated: atom_author = {atom_author}")

    # atom_advertise_url
    atom_advertise_url = f"https://aazw.github.io/github-trending-feeds/feeds/{language}/{period}.atom"
    appLogger.info(f"generated: atom_advertise_url = {atom_advertise_url}")

    # atom_advertise_alt_url
    atom_advertise_alt_url = f"https://aazw.github.io/github-trending-feeds/"
    appLogger.info(f"generated: atom_advertise_alt_url = {atom_advertise_alt_url}")

    # updated (drop milliseconds)
    updated = datetime.datetime.now(datetime.timezone.utc)
    if atom_updated_date:
        try:
            parsed_date = dateparser.parse(atom_updated_date)
            if parsed_date is None:
                appLogger.warning(f"Failed to parse atom_updated_date: {atom_updated_date}, using current time")
            else:
                updated = parsed_date
        except Exception as e:
            appLogger.warning(f"Error parsing atom_updated_date: {atom_updated_date}, using current time: {e}")

    appLogger.info(f"generated: updated = {updated}")

    ### fetch trending phase ##############################################################

    res = None
    try:
        # https://qiita.com/toshitanian/items/c28a65fe2f32884e067c
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        s = requests.Session()
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))

        # get page
        res = s.get(url, timeout=timeout)
        res.raise_for_status()  # HTTPError

    except HTTPError as e:
        # HTTPプロトコルに関連するエラー
        # HTTPステータスコードが 4xx または 5xx の場合に発生する
        status_code: int = e.response.status_code
        appLogger.error(f"requests http error ({status_code}): {e}")

        appLogger.error("app failed")
        if status_code >= 400 and status_code < 500:
            sys.exit(ReturnCode.HTTP_400_ERROR.value)
        elif status_code >= 500 and status_code < 600:
            sys.exit(ReturnCode.HTTP_500_ERROR.value)
        else:
            sys.exit(ReturnCode.HTTP_ERROR.value)

    except TooManyRedirects as e:  # リダイレクトが多すぎる場合に発生
        appLogger.error(f"requests too many redirects error {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.TOO_MANY_REDIRECTS_ERROR.value)

    except (Timeout, ConnectTimeout, ReadTimeout) as e:
        # ConnectTimeout: 接続確立中のタイムアウト
        # ReadTimeout: サーバーの応答読み取り中のタイムアウト
        # Timeout: ConnectTimeout または ReadTimeout の親クラス
        appLogger.error(f"requests timeout error {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.TIMEOUT_ERROR.value)

    except ConnectionError as e:  # サーバーへの接続に失敗した場合に発生
        appLogger.error(f"requests connection error: {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.CONNECTION_ERROR.value)

    except InvalidURL as e:  # URLが無効または不適切な形式の場合に発生
        appLogger.error(f"requests invalid url error {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.INVALID_URL_ERROR.value)

    except RequestException as e:  # requestsの例外の基底クラス
        appLogger.error(f"request error: {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.REQUESTS_ERROR.value)

    except Exception as e:  # Unknown Error
        appLogger.error(f"requests unknown error: {e}")
        appLogger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.UNKNOWN_ERROR.value)

    # parse DOM with error handling
    try:
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select("article.Box-row")
        if not items:
            appLogger.warning("No trending repositories found on the page")
    except Exception as e:
        appLogger.error(f"Error parsing HTML: {e}")
        appLogger.error("app failed")
        sys.exit(ReturnCode.UNKNOWN_ERROR.value)

    feeds: list[dict[str, str | None]] = []
    for item in reversed(items):
        try:
            # get repository path with error handling
            h2_link = item.select_one("h2 a")
            if h2_link is None:
                appLogger.warning("Repository link not found in item, skipping")
                continue
            
            repository_path = h2_link.get("href")
            if repository_path is None:
                appLogger.warning("Repository href not found in link, skipping")
                continue
            
            repository_url = f"https://github.com{repository_path}"

            # get description with error handling
            repository_description = None
            p = item.select_one("p")
            if p:
                repository_description = p.get_text()
                if repository_description:
                    repository_description = repository_description.strip()

            feeds.append(
                {
                    "repository_path": repository_path,
                    "repository_url": repository_url,
                    "repository_description": repository_description,
                }
            )
        except Exception as e:
            appLogger.warning(f"Error processing repository item: {e}")
            continue

    feeds = sorted(feeds, key=lambda x: x["repository_url"])

    ### build ATOM phase ##############################################################

    # 以下はATOMのサンプルをChatGPTで生成したもの
    #
    # <?xml version="1.0" encoding="utf-8"?>
    # <feed xmlns="http://www.w3.org/2005/Atom">
    #     <!-- 必須要素 -->
    #     <title>Example Feed</title>
    #     <id>http://example.org/feed</id>
    #     <updated>2024-12-28T18:30:02Z</updated>
    #
    #     <!-- オプション要素 -->
    #     <subtitle>This is an example of an Atom feed with all elements.</subtitle>
    #     <icon>http://example.org/icon.png</icon>
    #     <logo>http://example.org/logo.png</logo>
    #     <rights>Copyright 2024 Example Organization</rights>
    #     <generator uri="http://example.org/generator" version="1.0">Example Generator</generator>
    #     <link rel="self" href="http://example.org/feed" />
    #     <link rel="alternate" href="http://example.org/" />
    #     <author>
    #         <name>John Doe</name>
    #         <email>johndoe@example.org</email>
    #         <uri>http://example.org/authors/johndoe</uri>
    #     </author>
    #     <contributor>
    #         <name>Jane Smith</name>
    #     </contributor>
    #
    #     <!-- エントリ（記事） -->
    #     <entry>
    #         <!-- 必須要素 -->
    #         <title>Example Entry</title>
    #         <id>http://example.org/entry1</id>
    #         <updated>2024-12-28T18:30:02Z</updated>
    #
    #         <!-- オプション要素 -->
    #         <summary>This is a summary of the example entry.</summary>
    #         <content type="html">
    #             <![CDATA[
    #                 <p>This is the content of the example entry. It can include HTML.</p>
    #             ]]>
    #         </content>
    #         <link rel="alternate" href="http://example.org/entry1" />
    #         <author>
    #             <name>John Doe</name>
    #         </author>
    #         <contributor>
    #             <name>Jane Smith</name>
    #         </contributor>
    #         <category term="Technology" scheme="http://example.org/categories" label="Tech" />
    #         <published>2024-12-27T12:00:00Z</published>
    #         <rights>Copyright 2024 Example Organization</rights>
    #         <source>
    #             <id>http://example.org/source</id>
    #             <title>Source Feed</title>
    #             <updated>2024-12-28T12:00:00Z</updated>
    #         </source>
    #     </entry>
    # </feed>

    # new feed
    ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", ATOM_NAMESPACE)
    feed = ET.Element(f"{{{ATOM_NAMESPACE}}}feed", attrib={"xml:lang": "en"})

    # id
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}id").text = atom_advertise_url

    # title
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}title").text = atom_title

    # link (self)
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_url, "rel": "self"})

    # link (alternate)
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_alt_url, "rel": "alternate"})

    # icon
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}icon").text = "https://github.githubassets.com/favicons/favicon.svg"

    # updated
    ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}updated").text = updated.isoformat(timespec="seconds")

    # author
    author = ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}author")
    ET.SubElement(author, f"{{{ATOM_NAMESPACE}}}name").text = atom_author

    # entries
    for item in feeds:
        repository_path = item["repository_path"]
        repository_url = item["repository_url"]
        repository_description = item["repository_description"]

        # new entry
        entry = ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}entry")

        # id
        ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}id").text = f"{repository_url}#{int(updated.timestamp())}"

        # title
        ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}title").text = repository_url

        # link
        ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": repository_url})

        # updated
        ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}updated").text = updated.isoformat(timespec="seconds")

        # content
        content = ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}content", attrib={"type": "text"})
        content.text = repository_description

    # pretty print
    ET.indent(feed)

    # get xml
    feed_xml = ET.tostring(feed, encoding="utf-8", xml_declaration=True).decode("utf-8")

    # write to stdout
    if verbose:
        print(feed_xml)

    # write to file
    if output:
        # ファイルの絶対パスを指定
        file_path = Path(output)

        # ディレクトリ部分を抽出
        directory = file_path.parent

        # ディレクトリを作成
        directory.mkdir(parents=True, exist_ok=True)

        try:
            with file_path.open(mode="w", encoding="utf-8") as f:
                f.write(feed_xml)
        except FileNotFoundError as e:
            # 指定されたファイルやディレクトリが見つからない場合
            appLogger.error(f"file not found error: {e}")
            appLogger.error("app failed")
            sys.exit(ReturnCode.FILE_NOT_FOUND_ERROR.value)
        except IsADirectoryError as e:
            # 指定されたパスがディレクトリの場合
            appLogger.error(f"is a directory error: {e}")
            appLogger.error("app failed")
            sys.exit(ReturnCode.IS_DIRECTORY_ERROR.value)
        except PermissionError as e:
            # アクセス権限がない場合
            appLogger.error(f"permission error: {e}")
            appLogger.error("app failed")
            sys.exit(ReturnCode.PERMISSION_ERROR.value)
        except OSError as e:
            # その他のOS関連のエラー (例: I/Oエラー、デバイスエラーなど)
            appLogger.error(f"os error: {e}")
            appLogger.error("app failed")
            sys.exit(ReturnCode.OS_ERROR.value)
        except Exception as e:
            appLogger.error(f"unknown error: {e}")
            appLogger.error("app failed")
            sys.exit(ReturnCode.UNKNOWN_ERROR.value)

    appLogger.info("app finished")


if __name__ == "__main__":
    main()

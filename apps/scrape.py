import sys
import traceback
import logging
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

import click
import dateparser
import requests
from bs4 import BeautifulSoup


# Making Python loggers output all messages to stdout in addition to log file
# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file
formatter = logging.Formatter('%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s')

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

appLogger = logging.getLogger(__name__)
appLogger.setLevel(logging.INFO)
appLogger.addHandler(handler)


@click.command()
@click.option('--language',          type=str,                                                               required=True,                    help="")
@click.option('--date_range',        type=click.Choice(['daily', 'weekly', 'monthly'], case_sensitive=True), required=True,                    help="")
@click.option('--output',            type=str,                                                               required=False,                   help="")
@click.option("--atom_updated_date", type=str,                                                               required=False,                   help="")
@click.option("--verbose",           is_flag=True,                                                           default=False, show_default=True, help="")
def main(language: str, date_range: str, output: str, atom_updated_date: str, verbose: bool):
    appLogger.info(f"command-line argument: language = {language}")
    appLogger.info(f"command-line argument: date_range = {date_range}")
    appLogger.info(f"command-line argument: output = {output}")
    appLogger.info(f"command-line argument: atom_updated_date = {atom_updated_date}")
    appLogger.info(f"command-line argument: verbose = {verbose}")

    if verbose:
        appLogger.setLevel(logging.DEBUG)

    # url
    url = f"https://github.com/trending/{language}?since={date_range}"
    appLogger.info(f"generated: url = {url}")

    # atom_title
    atom_title = f"GitHub Treanding - {language} ({date_range})"
    appLogger.info(f"generated: atom_title = {atom_title}")

    # atom_author
    atom_author = "aazw"
    appLogger.info(f"generated: atom_author = {atom_author}")

    # atom_advertise_url
    atom_advertise_url = f"https://aazw.github.io/github-trending-feeds/feeds/{language}/{date_range}.atom"
    appLogger.info(f"generated: atom_advertise_url = {atom_advertise_url}")

    # atom_advertise_alt_url
    atom_advertise_alt_url = f"https://aazw.github.io/github-trending-feeds/feeds/{language}/"
    appLogger.info(f"generated: atom_advertise_alt_url = {atom_advertise_alt_url}")

    # updated (drop milliseconds)
    updated = datetime.datetime.now(datetime.timezone.utc)
    if atom_updated_date:
        updated = dateparser.parse(atom_updated_date)
    
    appLogger.info(f"generated: updated = {updated}")

    res = None
    try:
        # get page
        res = requests.get(url)
        res.raise_for_status()

        # new feed
        ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
        ET.register_namespace('', ATOM_NAMESPACE)
        feed = ET.Element(f"{{{ATOM_NAMESPACE}}}feed", attrib={"xml:lang": "en"})

        # id
        ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}id").text = atom_advertise_url

        # title
        ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}title").text = atom_title

        # link (self)
        ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_url, "rel": "self"})

        # link (alternate)
        ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_alt_url, "rel": "alternate"})

        # updated
        ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}updated").text = updated.isoformat(timespec="seconds")

        # author
        author = ET.SubElement(feed, f"{{{ATOM_NAMESPACE}}}author")
        ET.SubElement(author, f"{{{ATOM_NAMESPACE}}}name").text = atom_author

        # parse DOM
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('article.Box-row')

        for item in reversed(items):
            # get repository path
            repository_path = item.select_one('h2 a').get('href')
            repository_url = f"https://github.com{repository_path}"

            # get description
            repository_description = None
            p = item.select_one('p')
            if p:
                repository_description = p.get_text()
                if repository_description:
                    repository_description = repository_description.strip()

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
            content = ET.SubElement(entry, f"{{{ATOM_NAMESPACE}}}content", attrib={"type": "text"}).text = repository_description

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

            with file_path.open(mode="w", encoding="utf-8") as f:
                f.write(feed_xml)


    except Exception as e:
        appLogger.error(e)

        # PythonのException発生時のTracebackを綺麗に見る
        # https://vaaaaaanquish.hatenablog.com/entry/2017/12/14/183225
        t, v, tb = sys.exc_info()
        appLogger.error(traceback.format_exception(t,v,tb))
        appLogger.error(traceback.format_tb(e.__traceback__))

        if res:
            appLogger.error(f"request failed by status code {res.status_code}")

        raise e


if __name__ == '__main__':
    appLogger.info("start app")

    try:
        # python click usage of standalone_mode
        # https://stackoverflow.com/questions/34286165/python-click-usage-of-standalone-mode
        main(standalone_mode=False)
    except Exception as e:
        appLogger.error(e)

        # PythonのException発生時のTracebackを綺麗に見る
        # https://vaaaaaanquish.hatenablog.com/entry/2017/12/14/183225
        t, v, tb = sys.exc_info()
        appLogger.error(traceback.format_exception(t,v,tb))
        appLogger.error(traceback.format_tb(e.__traceback__))

        appLogger.error("app failed")
        sys.exit(1)

    appLogger.info("app finished")

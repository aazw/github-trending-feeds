import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

import click


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    # Making Python loggers output all messages to stdout in addition to log file
    # https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file
    formatter = logging.Formatter("%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


appLogger = setup_logging()
NS = {"a": "http://www.w3.org/2005/Atom"}


@click.command()
@click.option("--atom", "atomPath", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="Atomファイル")
@click.option("--urls", "urlsPath", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="URL一覧を読み込むテキストファイル")
@click.option("--format", "format", type=click.Choice(["plain", "atom"], case_sensitive=False), required=False, default="plain", help="書き出しフォーマット")
@click.option("--output", "outputPath", type=click.Path(dir_okay=False, writable=True, path_type=Path), required=False, help="新着一覧を書き出すファイル")
def main(atomPath: Path, urlsPath: Path, format: str, outputPath: Path) -> None:
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --atom = {atomPath}")
    appLogger.info(f"command-line argument: --urls = {urlsPath}")
    appLogger.info(f"command-line argument: --format = {format}")
    appLogger.info(f"command-line argument: --output = {outputPath}")

    # urlsからURL一覧を読み込み (このURL一覧は過去登場したURLの一覧)
    urls: set[str] = set()
    try:
        with urlsPath.open("r", encoding="utf-8") as fp:
            for line in fp:
                # 空行を無視
                url = line.strip()
                if not url:
                    continue
                urls.add(url)
    except OSError as e:
        appLogger.error(f"failed to read {urlsPath}: {e}")
        sys.exit(1)

    # atomを読み込んで、URL一覧取得
    newUrls: set[str] = set()
    root: ET.Element[str] = None
    try:
        root = ET.parse(atomPath).getroot()
    except ET.ParseError as e:
        appLogger.error(f"XML parse error in {atomPath}: {e}")
        sys.exit(1)

    for entry in root.findall("a:entry", NS):
        link = entry.find("a:link", NS)
        if link is None:
            continue

        if link.get("rel") == "self" or link.get("rel") == "alternate":
            continue

        href = link.get("href")
        if href:
            # atomに含まれるURLが完全新規かをチェック (過去URL一覧に含まれないか)
            if href not in urls:
                newUrls.add(href)
            else:
                root.remove(entry)

    appLogger.info(f"{len(newUrls)} urls is new")

    if format.lower() == "plain":
        if outputPath:
            try:
                with outputPath.open("w", encoding="utf-8") as f:
                    for url in sorted(newUrls):
                        f.write(url + "\n")
            except OSError as e:
                appLogger.error(f"cannot write to {outputPath}: {e}")
                sys.exit(1)
        else:
            for url in sorted(newUrls):
                print(url)
    elif format.lower() == "atom":
        # id
        id_elem = root.find("./a:id", NS)
        if id_elem is not None and id_elem.text:
            id_elem.text = id_elem.text.replace(
                "https://aazw.github.io/github-trending-feeds/feeds/",
                "https://aazw.github.io/github-trending-feeds/new-arrivals/",
            )

        # title
        title_elem = root.find("./a:title", NS)
        if title_elem is not None and title_elem.text:
            title_elem.text += " [new arrivals only]"

        # link (self)
        self_link = root.find("./a:link[@rel='self']", NS)
        if self_link is not None:
            self_link.set(
                "href",
                self_link.get("href").replace("https://aazw.github.io/github-trending-feeds/feeds/", "https://aazw.github.io/github-trending-feeds/new-arrivals/"),
            )

        # pretty print
        ET.indent(root)

        # get xml
        feed_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

        if outputPath:
            try:
                with outputPath.open("w", encoding="utf-8") as f:
                    f.write(feed_xml)
            except OSError as e:
                appLogger.error(f"cannot write to {outputPath}: {e}")
                sys.exit(1)
        else:
            print(feed_xml)


if __name__ == "__main__":
    main()

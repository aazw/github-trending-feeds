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
def main(atomPath: Path, urlsPath: Path) -> None:
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --atom = {atomPath}")
    appLogger.info(f"command-line argument: --urls = {urlsPath}")

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
    try:
        root = ET.parse(atomPath).getroot()
    except ET.ParseError as e:
        appLogger.error(f"XML parse error in {atomPath}: {e}")
        sys.exit(1)

    for link in root.findall(".//a:link", NS):
        href = link.get("href")
        if href:
            if link.get("rel") == "self" or link.get("rel") == "alternate":
                continue

            # atomに含まれるURLが完全新規かをチェック (過去URL一覧に含まれないか)
            if href not in urls:
                newUrls.add(href)

    appLogger.info(f"{len(newUrls)} urls is new")
    for url in newUrls:
        print(url)


if __name__ == "__main__":
    main()

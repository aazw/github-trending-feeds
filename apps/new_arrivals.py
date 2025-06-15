import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Iterator
import datetime
import re
from urllib.parse import unquote

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


def iter_atom_paths(root: Path, atomName: str) -> Iterator[Path]:
    # daily.atom を symlink ディレクトリを除いて再帰列挙
    yield from root.rglob(atomName, recurse_symlinks=False)


@click.command()
@click.option("--dir", "dirPath", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Atomファイルを再帰探索するディレクトリ")
@click.option("--period", type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=True), required=False, default="daily", help="")
@click.option("--urls", "urlsPath", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="URL一覧を読み込むテキストファイル")
@click.option("--format", "format", type=click.Choice(["plain", "atom"], case_sensitive=False), required=False, default="plain", help="書き出しフォーマット")
@click.option("--output", "outputPath", type=click.Path(dir_okay=False, writable=True, path_type=Path), required=False, help="新着一覧を書き出すファイル")
def main(dirPath: Path, period: str, urlsPath: Path, format: str, outputPath: Path) -> None:
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --dir = {dirPath}")
    appLogger.info(f"command-line argument: --period = {period}")
    appLogger.info(f"command-line argument: --urls = {urlsPath}")
    appLogger.info(f"command-line argument: --format = {format}")
    appLogger.info(f"command-line argument: --output = {outputPath}")

    # urlsからURL一覧を読み込み (このURL一覧は過去登場したURLの一覧)
    existingURLs: set[str] = set()
    try:
        with urlsPath.open("r", encoding="utf-8") as fp:
            for line in fp:
                # 空行を無視
                url = line.strip()
                if not url:
                    continue
                existingURLs.add(url)
    except OSError as e:
        appLogger.error(f"failed to read {urlsPath}: {e}")
        sys.exit(1)

    # atomを探索するディレクトリを探索
    appLogger.info(f"atom file searching in {dirPath}")
    newUrls: set[str] = set()
    newEntries: dict[str, ET.Element[str]] = {}

    for atom_path in iter_atom_paths(dirPath, f"{period}.atom"):
        appLogger.debug(f"reading {atom_path}")

        root: ET.Element[str] = None
        try:
            root = ET.parse(atom_path).getroot()
        except ET.ParseError as e:
            appLogger.warning(f"XML parse error in {atom_path}: {e}")
            continue

        # 言語情報抽出
        id = root.find("a:id", NS)
        language: str = None
        if id is not None:
            pattern = re.compile(
                r"^https://[^/]+/github-trending-feeds/feeds/"
                r"(?P<lang>[^/]+)/"  # ← 抽出したい部分
                r"(daily|weekly|monthly)\.atom$"
            )
            m = pattern.match(id.text)
            if m:
                language = m["lang"]

        # 各エントリ精査
        for entry in root.findall("a:entry", NS):
            link = entry.find("a:link", NS)
            if link is None:
                continue

            if link.get("rel") == "self" or link.get("rel") == "alternate":
                continue

            href = link.get("href")
            if href:
                # atomに含まれるURLが完全新規かをチェック (過去URL一覧に含まれないか)
                if href not in existingURLs:
                    newUrls.add(href)

                    if id is not None and id.text is not None:
                        content = entry.find("a:content", NS)
                        if content is not None:
                            content.text = f"[{unquote(language)}] " + (content.text or "")
                    newEntries[href] = entry

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
        atom_advertise_url = f"https://aazw.github.io/github-trending-feeds/new-arrivals/{period}.atom"
        atom_advertise_alt_url = f"https://aazw.github.io/github-trending-feeds/"
        atom_title = f"GitHub New Arrivals ({period})"
        atom_author = "aazw"
        updated = datetime.datetime.now(datetime.timezone.utc)

        ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
        ET.register_namespace("", ATOM_NAMESPACE)
        root = ET.Element(f"{{{ATOM_NAMESPACE}}}feed", attrib={"xml:lang": "en"})

        # id
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}id").text = atom_advertise_url

        # title
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}title").text = atom_title

        # link (self)
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_url, "rel": "self"})

        # link (alternate)
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}link", attrib={"href": atom_advertise_alt_url, "rel": "alternate"})

        # icon
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}icon").text = "https://github.githubassets.com/favicons/favicon.svg"

        # updated
        ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}updated").text = updated.isoformat(timespec="seconds")

        # author
        author = ET.SubElement(root, f"{{{ATOM_NAMESPACE}}}author")
        ET.SubElement(author, f"{{{ATOM_NAMESPACE}}}name").text = atom_author

        # entries
        for entry in newEntries.values():
            root.append(entry)

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

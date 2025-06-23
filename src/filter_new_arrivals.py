import sys
import logging
import datetime
import re
from pathlib import Path
from typing import Iterator
from urllib.parse import unquote

import click
from lxml import etree


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    # Making Python loggers output all messages to stdout in addition to log file
    # https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file
    formatter = logging.Formatter(
        "%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s"
    )

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
    """Iterate over atom files recursively, excluding symlinked directories."""
    try:
        yield from root.rglob(atomName, recurse_symlinks=False)
    except Exception as e:
        appLogger.error(f"Error iterating atom paths in {root}: {e}")
        appLogger.error("app failed")
        sys.exit(1)


@click.command()
@click.option(
    "--dir",
    "dirPath",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=False,
    help="Atomファイルを再帰探索するディレクトリ",
)
@click.option(
    "--atom",
    "atomPath",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
    help="単一のAtomファイルを処理",
)
@click.option(
    "--period",
    type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=True),
    required=False,
    default="daily",
    help="",
)
@click.option(
    "--urls",
    "urlsPath",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="URL一覧を読み込むテキストファイル",
)
@click.option(
    "--format",
    "format",
    type=click.Choice(["plain", "atom"], case_sensitive=False),
    required=False,
    default="plain",
    help="書き出しフォーマット",
)
@click.option(
    "--output",
    "outputPath",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=False,
    help="新着一覧を書き出すファイル",
)
def main(
    dirPath: Path,
    atomPath: Path,
    period: str,
    urlsPath: Path,
    format: str,
    outputPath: Path,
) -> None:
    appLogger.info("start app")

    # 引数検証: --dir または --atom のいずれかが必要
    if not dirPath and not atomPath:
        appLogger.error("Either --dir or --atom must be specified")
        appLogger.error("app failed")
        sys.exit(1)

    if dirPath and atomPath:
        appLogger.error("Cannot specify both --dir and --atom options")
        appLogger.error("app failed")
        sys.exit(1)

    appLogger.info(f"command-line argument: --dir = {dirPath}")
    appLogger.info(f"command-line argument: --atom = {atomPath}")
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
    except PermissionError as e:
        appLogger.error(f"Permission denied reading {urlsPath}: {e}")
        appLogger.error("app failed")
        sys.exit(1)
    except OSError as e:
        appLogger.error(f"OS error reading {urlsPath}: {e}")
        appLogger.error("app failed")
        sys.exit(1)
    except Exception as e:
        appLogger.error(f"Unexpected error reading {urlsPath}: {e}")
        appLogger.error("app failed")
        sys.exit(1)

    # atomファイルの処理
    newUrls: set[str] = set()
    newEntries: dict[str, etree._Element] = {}

    atom_paths: list[Path] = []
    if dirPath:
        appLogger.info(f"atom file searching in {dirPath}")
        atom_paths = list(iter_atom_paths(dirPath, f"{period}.atom"))
    else:
        appLogger.info(f"processing single atom file: {atomPath}")
        atom_paths = [atomPath]

    for atom_path in atom_paths:
        appLogger.debug(f"reading {atom_path}")

        root: etree._Element | None = None
        try:
            # Parse XML with security settings
            parser = etree.XMLParser()

            root = etree.parse(atom_path, parser).getroot()
        except etree.XMLSyntaxError as e:
            appLogger.warning(f"XML parse error in {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)
        except Exception as e:
            appLogger.error(f"Unexpected error reading {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)

        # 言語情報抽出
        id_element = root.find("a:id", NS)
        language: str | None = None
        if id_element is not None and id_element.text is not None:
            pattern = re.compile(
                r"^https://[^/]+/github-trending-feeds/feeds/"
                r"(?P<lang>[^/]+)/"  # ← 抽出したい部分
                r"(daily|weekly|monthly)\.atom$"
            )
            m = pattern.match(id_element.text)
            if m:
                language = m["lang"]

        # 各エントリ精査
        try:
            for entry in root.findall("a:entry", NS):
                link = entry.find("a:link", NS)
                if link is None:
                    continue

                rel = link.get("rel")
                if rel in ("self", "alternate"):
                    continue

                href = link.get("href")
                if href:
                    # atomに含まれるURLが完全新規かをチェック (過去URL一覧に含まれないか)
                    if href not in existingURLs:
                        newUrls.add(href)

                        if (
                            id_element is not None
                            and id_element.text is not None
                            and language is not None
                        ):
                            content = entry.find("a:content", NS)
                            if content is not None:
                                content.text = f"[{unquote(language)}] " + (
                                    content.text or ""
                                )
                        newEntries[href] = entry
        except Exception as e:
            appLogger.error(f"Error processing entries in {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)

    appLogger.info(f"{len(newUrls)} urls is new")

    if format.lower() == "plain":
        if outputPath:
            try:
                # Ensure parent directory exists
                outputPath.parent.mkdir(parents=True, exist_ok=True)

                with outputPath.open("w", encoding="utf-8") as f:
                    for url in sorted(newUrls):
                        f.write(url + "\n")
            except PermissionError as e:
                appLogger.error(f"Permission denied writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
            except OSError as e:
                appLogger.error(f"OS error writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
            except Exception as e:
                appLogger.error(f"Unexpected error writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
        else:
            for url in sorted(newUrls):
                print(url)
    elif format.lower() == "atom":
        atom_advertise_url = (
            f"https://aazw.github.io/github-trending-feeds/new-arrivals/{period}.atom"
        )
        atom_advertise_alt_url = "https://aazw.github.io/github-trending-feeds/"
        atom_title = f"GitHub New Arrivals ({period})"
        atom_author = "aazw"
        updated = datetime.datetime.now(datetime.timezone.utc)

        ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
        root = etree.Element(f"{{{ATOM_NAMESPACE}}}feed")
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "en")

        # id
        etree.SubElement(root, f"{{{ATOM_NAMESPACE}}}id").text = atom_advertise_url

        # title
        etree.SubElement(root, f"{{{ATOM_NAMESPACE}}}title").text = atom_title

        # link (self)
        etree.SubElement(
            root,
            f"{{{ATOM_NAMESPACE}}}link",
            attrib={"href": atom_advertise_url, "rel": "self"},
        )

        # link (alternate)
        etree.SubElement(
            root,
            f"{{{ATOM_NAMESPACE}}}link",
            attrib={"href": atom_advertise_alt_url, "rel": "alternate"},
        )

        # icon
        etree.SubElement(
            root, f"{{{ATOM_NAMESPACE}}}icon"
        ).text = "https://github.githubassets.com/favicons/favicon.svg"

        # updated
        etree.SubElement(root, f"{{{ATOM_NAMESPACE}}}updated").text = updated.isoformat(
            timespec="seconds"
        )

        # author
        author = etree.SubElement(root, f"{{{ATOM_NAMESPACE}}}author")
        etree.SubElement(author, f"{{{ATOM_NAMESPACE}}}name").text = atom_author

        # entries
        for entry in newEntries.values():
            root.append(entry)

        # pretty print
        etree.indent(root)

        # get xml
        feed_xml = etree.tostring(root, encoding="utf-8", xml_declaration=True).decode(
            "utf-8"
        )

        if outputPath:
            try:
                # Ensure parent directory exists
                outputPath.parent.mkdir(parents=True, exist_ok=True)

                with outputPath.open("w", encoding="utf-8") as f:
                    f.write(feed_xml)
            except PermissionError as e:
                appLogger.error(f"Permission denied writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
            except OSError as e:
                appLogger.error(f"OS error writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
            except Exception as e:
                appLogger.error(f"Unexpected error writing to {outputPath}: {e}")
                appLogger.error("app failed")
                sys.exit(1)
        else:
            print(feed_xml)


if __name__ == "__main__":
    main()

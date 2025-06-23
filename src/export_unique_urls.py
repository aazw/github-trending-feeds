import sys
import logging
from pathlib import Path
from typing import Iterator

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


def iter_atom_paths(root: Path, pattern: str) -> Iterator[Path]:
    """Iterate over files matching pattern recursively, excluding symlinked directories."""
    try:
        yield from root.rglob(pattern, recurse_symlinks=False)
    except Exception as e:
        appLogger.error(f"Error iterating paths in {root} with pattern {pattern}: {e}")
        appLogger.error("app failed")
        sys.exit(1)


@click.command()
@click.option(
    "--dir",
    "dirPath",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="ファイルを再帰探索するディレクトリ",
)
@click.option(
    "--output",
    "outputPath",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=True,
    help="URL一覧を書き出すテキストファイル",
)
@click.option(
    "--pattern",
    type=str,
    default="*.atom",
    help="検索するファイルパターン",
)
@click.option(
    "--incremental", is_flag=True, help="Only add new urls to existing output file"
)
def main(dirPath: Path, outputPath: Path, pattern: str, incremental: bool) -> None:
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --dir = {dirPath}")
    appLogger.info(f"command-line argument: --output = {outputPath}")
    appLogger.info(f"command-line argument: --pattern = {pattern}")
    appLogger.info(f"command-line argument: --incremental = {incremental}")

    # Validate input directory
    if not dirPath.is_dir():
        appLogger.error(f"Directory does not exist or is not a directory: {dirPath}")
        sys.exit(1)

    appLogger.info(f"file searching in {dirPath} with pattern {pattern}")
    urls: set[str] = set()

    # Load existing URLs if incremental mode is enabled
    if incremental and outputPath.exists():
        try:
            with outputPath.open("r", encoding="utf-8") as f:
                existing_urls = {line.strip() for line in f if line.strip()}
                urls.update(existing_urls)
                appLogger.info(
                    f"loaded {len(existing_urls)} existing URLs from {outputPath}"
                )
        except Exception as e:
            appLogger.error(f"Error reading existing URLs from {outputPath}: {e}")
            sys.exit(1)

    for atom_path in iter_atom_paths(dirPath, pattern):
        appLogger.debug(f"reading {atom_path}")
        try:
            # Parse XML with security settings
            parser = etree.XMLParser(
                dtd_validation=False,
                load_dtd=False,
                no_network=True,
                resolve_entities=False,
            )

            root = etree.parse(str(atom_path), parser)
        except etree.XMLSyntaxError as e:
            appLogger.warning(f"XML parse error in {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)
        except Exception as e:
            appLogger.error(f"Unexpected error reading {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)

        try:
            for link in root.xpath(".//a:link", namespaces=NS):
                href = link.get("href")
                if href:
                    rel = link.get("rel")
                    if rel in ("self", "alternate"):
                        continue
                    urls.add(href)
        except Exception as e:
            appLogger.warning(f"Error processing links in {atom_path}: {e}")
            appLogger.error("app failed")
            sys.exit(1)

    try:
        # Ensure parent directory exists
        outputPath.parent.mkdir(parents=True, exist_ok=True)

        with outputPath.open("w", encoding="utf-8") as f:
            for url in sorted(urls):
                f.write(url + "\n")
    except PermissionError as e:
        appLogger.error(f"Permission denied writing to {outputPath}: {e}")
        sys.exit(1)
    except OSError as e:
        appLogger.error(f"OS error writing to {outputPath}: {e}")
        sys.exit(1)
    except Exception as e:
        appLogger.error(f"Unexpected error writing to {outputPath}: {e}")
        sys.exit(1)

    appLogger.info(f"wrote {len(urls)} unique URLs to {outputPath}")


if __name__ == "__main__":
    main()

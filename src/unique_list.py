import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Iterator

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


def iter_atom_paths(root: Path) -> Iterator[Path]:
    """Iterate over .atom files recursively, excluding symlinked directories."""
    try:
        yield from root.rglob("*.atom", recurse_symlinks=False)
    except Exception as e:
        appLogger.error(f"Error iterating atom paths in {root}: {e}")
        return


@click.command()
@click.option("--dir", "dirPath", type=click.Path(exists=True, file_okay=False, path_type=Path), required=True, help="Atomファイルを再帰探索するディレクトリ")
@click.option("--output", "outputPath", type=click.Path(dir_okay=False, writable=True, path_type=Path), required=True, help="URL一覧を書き出すテキストファイル")
@click.option("--force", is_flag=True, help="出力ファイルを上書きする")
def main(dirPath: Path, outputPath: Path, force: bool) -> None:
    appLogger.info("start app")
    appLogger.info(f"command-line argument: --dir = {dirPath}")
    appLogger.info(f"command-line argument: --output = {outputPath}")

    if outputPath.exists() and not force:
        appLogger.error("output file already exists: %s (use --force to overwrite)", outputPath)
        sys.exit(1)
    
    # Validate input directory
    if not dirPath.is_dir():
        appLogger.error(f"Directory does not exist or is not a directory: {dirPath}")
        sys.exit(1)

    appLogger.info(f"atom file searching in {dirPath}")
    urls: set[str] = set()

    for atom_path in iter_atom_paths(dirPath):
        appLogger.debug(f"reading {atom_path}")
        try:
            # Parse XML with security settings
            parser = ET.XMLParser()
            parser.parser.DefaultHandler = lambda _: None  # Disable DTD processing
            
            root = ET.parse(atom_path, parser).getroot()
        except ET.ParseError as e:
            appLogger.warning(f"XML parse error in {atom_path}: {e}")
            continue
        except Exception as e:
            appLogger.error(f"Unexpected error reading {atom_path}: {e}")
            continue

        try:
            for link in root.findall(".//a:link", NS):
                href = link.get("href")
                if href:
                    rel = link.get("rel")
                    if rel in ("self", "alternate"):
                        continue
                    urls.add(href)
        except Exception as e:
            appLogger.warning(f"Error processing links in {atom_path}: {e}")
            continue

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

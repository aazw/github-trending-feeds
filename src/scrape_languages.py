import re
import logging
from typing import List, Match, Optional, Pattern, Union, cast
from pathlib import Path

import requests
import click
from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement


URL: str = "https://github.com/trending"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.command()
@click.option("--sort", is_flag=True, help="Sort languages in ascending order")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=False,
    help="Output file path for the language list",
)
@click.option(
    "--incremental", is_flag=True, help="Only add new languages to existing output file"
)
def scrape_languages(sort: bool, output: Optional[Path], incremental: bool) -> None:
    """Scrape GitHub trending languages and output them as a list."""

    try:
        response: requests.Response = requests.get(URL)
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

        # Find the div with data-filter-list attribute
        filter_list_div: Union[Tag, PageElement, None] = soup.find(
            "div", {"data-filter-list": True}
        )

        if not filter_list_div or not hasattr(filter_list_div, "find_all"):
            logging.error("Could not find data-filter-list div")
            raise SystemExit(1)

        # Find all a tags with href starting with "/trending/"
        href_pattern: Pattern[str] = re.compile(r"^/trending/")
        # Cast to Tag to ensure find_all is available
        tag_div = cast(Tag, filter_list_div)
        trending_links = tag_div.find_all("a", href=href_pattern)

        languages: List[str] = []
        seen: set[str] = set()
        for link in trending_links:
            if isinstance(link, Tag):
                href = link.get("href")
                if href and isinstance(href, str):
                    # Extract language between "/trending/" and "?"
                    match: Optional[Match[str]] = re.search(r"/trending/([^?]+)", href)
                    if match:
                        language: str = match.group(1)
                        if language not in seen:
                            seen.add(language)
                            languages.append(language)

        # Handle incremental mode
        if incremental and output and output.exists():
            # Read existing languages from file
            existing_languages: set[str] = set()
            with open(output, "r") as f:
                for line in f:
                    existing_languages.add(line.strip())

            # Add new languages to existing ones
            new_languages: List[str] = [lang for lang in languages]
            all_languages: List[str] = list(existing_languages) + [
                lang for lang in new_languages if lang not in existing_languages
            ]

            # Sort if requested
            if sort:
                all_languages.sort()

            final_languages: List[str] = all_languages
        else:
            # Normal mode - just use scraped languages
            final_languages = [lang for lang in languages]

            # Sort if requested
            if sort:
                final_languages.sort()

        # Output the list
        if output:
            with open(output, "w") as f:
                for language in final_languages:
                    f.write(f"{language}\n")
        else:
            for language in final_languages:
                click.echo(language)

    except requests.RequestException as e:
        logging.error(f"Error fetching URL: {e}")
    except Exception as e:
        logging.error(f"Error parsing content: {e}")


if __name__ == "__main__":
    scrape_languages()

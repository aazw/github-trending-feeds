#!/usr/bin/env python3

import click
from pathlib import Path
from urllib.parse import quote


def read_languages(languages_file: Path) -> list[str]:
    """Read languages from languages.txt file."""
    with open(languages_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def generate_html(languages: list[str]) -> str:
    """Generate HTML content from languages list."""
    html_template: str = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GitHub Trending Feeds</title>
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      
      body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #24292f;
        background-color: #ffffff;
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
      }}
      
      h2 {{
        color: #1f2328;
        margin-bottom: 1.5rem;
        font-size: 1.75rem;
        font-weight: 600;
      }}
      
      .info-section {{
        background-color: #f6f8fa;
        border: 1px solid #d1d9e0;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 2rem;
      }}
      
      .info-section div {{
        margin-bottom: 0.5rem;
      }}
      
      .info-section div:last-child {{
        margin-bottom: 0;
      }}
      
      a {{
        color: #0969da;
        text-decoration: none;
      }}
      
      a:hover {{
        text-decoration: underline;
      }}
      
      table {{
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff;
        border: 1px solid #d1d9e0;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      }}
      
      th, td {{
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 1px solid #d1d9e0;
      }}
      
      th:first-child, td:first-child {{
        width: auto;
      }}
      
      th:not(:first-child), td:not(:first-child) {{
        width: 120px;
      }}
      
      th {{
        background-color: #f6f8fa;
        font-weight: 600;
        color: #1f2328;
      }}
      
      tr:hover {{
        background-color: #f6f8fa;
      }}
      
      tr:last-child td {{
        border-bottom: none;
      }}
      
      .feed-link {{
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background-color: #f6f8fa;
        border: 1px solid #d1d9e0;
        border-radius: 4px;
        font-size: 0.875rem;
        margin-right: 0.25rem;
        transition: background-color 0.2s;
      }}
      
      .feed-link:hover {{
        background-color: #e1e4e8;
        text-decoration: none;
      }}
      
      @media (max-width: 768px) {{
        body {{
          padding: 1rem;
        }}
        
        table {{
          font-size: 0.875rem;
        }}
        
        th, td {{
          padding: 0.5rem;
        }}
      }}
    </style>
  </head>

  <body>
    <h2>GitHub Trending Feeds</h2>
    <div class="info-section">
      <div>
        <strong>Source:</strong>
        <a href="https://github.com/trending">https://github.com/trending</a>
      </div>
      <div>
        <strong>New arrivals:</strong>
        <a href="./new-arrivals/daily.atom" class="feed-link">Daily</a>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Language</th>
          <th>Daily</th>
          <th>Weekly</th>
          <th>Monthly</th>
        </tr>
      </thead>
      <tbody>
{table_rows}
      </tbody>
    </table>
  </body>
</html>"""

    table_rows: list[str] = []
    for lang in languages:
        row: str = f"""        <tr>
          <td><a href="https://github.com/trending/{quote(lang)}">{lang}</a></td>
          <td><a href="./feeds/{lang}/daily.atom" class="feed-link">Daily</a></td>
          <td><a href="./feeds/{lang}/weekly.atom" class="feed-link">Weekly</a></td>
          <td><a href="./feeds/{lang}/monthly.atom" class="feed-link">Monthly</a></td>
        </tr>"""
        table_rows.append(row)

    return html_template.format(table_rows="\n".join(table_rows))


@click.command()
@click.option(
    "--languages",
    type=click.Path(exists=True, readable=True, path_type=Path),
    required=True,
    help="Path to languages.txt file",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=True,
    help="Output HTML file path",
)
def main(languages: Path, output: Path) -> None:
    """Generate index.html from languages.txt"""
    languages_list: list[str] = read_languages(languages)
    html_content: str = generate_html(languages_list)

    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html_content)

    click.echo(f"Generated {output} with {len(languages_list)} languages")


if __name__ == "__main__":
    main()

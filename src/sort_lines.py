from pathlib import Path
from typing import List

import click


@click.command()
@click.argument(
    "filename",
    type=click.Path(exists=True, dir_okay=False, writable=True, path_type=Path),
)
def main(filename: Path) -> None:
    """Sort lines in a file and overwrite it."""
    try:
        with filename.open("r") as f:
            lines: List[str] = f.readlines()

        sorted_lines: List[str] = sorted(lines)

        with filename.open("w") as f:
            f.writelines(sorted_lines)

        click.echo(f"Sorted {filename}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()

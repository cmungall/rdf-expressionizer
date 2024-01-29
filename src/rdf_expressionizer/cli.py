"""Command line interface for rdf-expressionizer."""
import logging
from pathlib import Path

import click

from rdf_expressionizer import __version__
from rdf_expressionizer.main import file_replace, load_replacement_map

__all__ = [
    "main",
]

from rdf_expressionizer.mappings import MAPPING_DIR

logger = logging.getLogger(__name__)

exclude_subset_option = click.option(
    "--exclude-subset",
    "-x",
    multiple=True,
    help="Subsets to exclude.",
)
include_subset_option = click.option(
    "--include-subset",
    "-s",
    multiple=True,
    help="Subsets to include.",
)
mappings_option = click.option(
    "--mappings",
    "-m",
    default="bfo_xbfo_mappings",
    help="Path to mappings file.",
)
output_option = click.option(
    "--output",
    "-o",
    default=None,
    help="Path to output file.",
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
@click.version_option(__version__)
def main(verbose: int, quiet: bool):
    """
    CLI for rdf-expressionizer.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)


@main.command()
@exclude_subset_option
@mappings_option
@output_option
@click.argument("input_path")
def replace(input_path, exclude_subset, mappings, output):
    """Replace named entities with expressions in RDF file.

    Example:

        rdf-expressionizer replace -m bfo_xbfo_mappings -o xro.owl ro.owl

    To preserve a subset:

    Example:

        rdf-expressionizer replace -x COB -m bfo_xbfo_mappings -o xro.owl ro.owl

    """
    mappings_path = Path(MAPPING_DIR / f"{mappings}.csv")
    if not mappings_path.exists():
        mappings_path = Path(mappings)
    if not mappings_path.exists():
        raise FileNotFoundError(f"Could not find {mappings_path} directly or in {MAPPING_DIR}")
    if exclude_subset:
        subsets = list(exclude_subset)
        replacement_map = load_replacement_map(mappings_path, exclude_subsets=subsets)
    else:
        replacement_map = load_replacement_map(mappings_path)
    file_replace(input_path, replacement_map, replace=True, output_path=output)


@main.command()
@include_subset_option
@mappings_option
@output_option
@click.argument("input_path")
def augment(input_path, include_subset, mappings, output):
    """Augment occurrences of named entities with logical definitions.

    Example:

        rdf-expressionizer augment -m bfo_xbfo_mappings -o mcob.owl cob.owl
    """
    mappings_path = Path(MAPPING_DIR / f"{mappings}.csv")
    if not mappings_path.exists():
        mappings_path = Path(mappings)
    if not mappings_path.exists():
        raise FileNotFoundError(f"Could not find {mappings_path} directly or in {MAPPING_DIR}")
    if include_subset:
        subsets = list(include_subset)
        replacement_map = load_replacement_map(mappings_path, include_subsets=subsets)
    else:
        replacement_map = load_replacement_map(mappings_path)
    file_replace(input_path, replacement_map, replace=False, output_path=output)


if __name__ == "__main__":
    main()

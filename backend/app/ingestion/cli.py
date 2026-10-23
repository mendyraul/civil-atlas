"""Run with python -m app.ingestion.cli; never fetches or publishes source data."""

import argparse
import json
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.ingestion.cliopatria import CliopatriaAdapter
from app.ingestion.pipeline import import_bundle, prepare_import
from app.ingestion.pleiades import PleiadesAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("pleiades", "cliopatria"), default="pleiades")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument(
        "--id", "--place-id", action="append", dest="ids", default=[],
        help="Pleiades place ID (required) or Cliopatria Wikidata ID (optional; default: all mapped polities)",
    )
    parser.add_argument("--year", type=int, help="Cliopatria: import rows active in this year (negative for BCE)")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--retrieved-at", required=True, help="ISO 8601 timestamp with timezone")
    parser.add_argument("--actor", required=True)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.source == "cliopatria":
        if args.year is None:
            parser.error("--year is required for --source cliopatria")
        adapter = CliopatriaAdapter(args.year)
    else:
        if args.year is not None:
            parser.error("--year applies only to --source cliopatria")
        adapter = PleiadesAdapter()
    try:
        bundle = prepare_import(adapter, args.snapshot, args.ids, args.dataset_version, args.retrieved_at)
        result = import_bundle(bundle, args.artifact_dir, args.actor, dry_run=args.dry_run)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Import failed: {error}\n")
    except SQLAlchemyError:
        parser.exit(1, "Import failed: database transaction could not complete. Verify database availability and migrations; retry the same inputs.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

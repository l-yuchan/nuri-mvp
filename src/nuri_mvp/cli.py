"""Command line interface: train, evaluate and predict.

Examples:
    python -m nuri_mvp train
    python -m nuri_mvp evaluate
    python -m nuri_mvp predict --text "아이가 블록으로 높은 탑을 쌓고 ..."
    python -m nuri_mvp predict --file examples/inputs/parent_01_art.txt

"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nuri_mvp.model import AreaModel, evaluate, fit_areas, load_splits
from nuri_mvp.pipeline import Predictor

if TYPE_CHECKING:
    from collections.abc import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DEFAULT_MODEL_DIR = REPO_ROOT / "models"


def _dump(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _train(args: argparse.Namespace) -> int:
    train, val = load_splits(args.data_dir)
    model = fit_areas(train, data_dir=args.data_dir)
    path = model.save(args.model_dir)
    metrics = evaluate(model, val)
    metrics_path = args.model_dir / "metrics.json"
    _ = metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = {
        "trained_rows": len(train),
        "model_path": str(path),
        "metrics_path": str(metrics_path),
        "validation": {key: metrics[key] for key in ("accuracy", "macro_f1", "top2_accuracy")},
    }
    _dump(summary)
    return 0


def _evaluate(args: argparse.Namespace) -> int:
    model = AreaModel.load(args.model_dir)
    _, val = load_splits(args.data_dir)
    _dump(evaluate(model, val))
    return 0


def _predict(args: argparse.Namespace) -> int:
    if args.text is not None:
        text = args.text
    elif args.file is not None:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        print("--text or --file is required")
        return 2
    predictor = Predictor.from_dir(args.model_dir)
    _dump(predictor.predict(text))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the documented subcommands."""
    parser = argparse.ArgumentParser(prog="nuri-mvp", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, handler, help_text in (
        ("train", _train, "fit on data/train.csv, save the artifact, score val"),
        ("evaluate", _evaluate, "score the saved artifact on data/val.csv"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
        command.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
        command.set_defaults(handler=handler)

    predict = sub.add_parser("predict", help="score a description and print JSON")
    predict.add_argument("--text")
    predict.add_argument("--file", type=Path)
    predict.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    predict.set_defaults(handler=_predict)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand and return its exit code."""
    if hasattr(sys.stdout, "reconfigure"):
        # Windows consoles default to cp949, which cannot print the area names.
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return int(handler(args))
    except (FileNotFoundError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

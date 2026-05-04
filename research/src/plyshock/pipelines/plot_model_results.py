"""Plot model result artifacts from saved prediction CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from plyshock.evaluation.plots import plot_confusion_matrix_from_csv


def main(argv: Sequence[str] | None = None) -> None:
    """Run the model-results plotting pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="Input predictions CSV.")
    parser.add_argument("--model", required=True, help="Model name, such as svm.")
    parser.add_argument("--output", required=True, type=Path, help="Output confusion matrix PNG.")
    args = parser.parse_args(argv)

    plot_confusion_matrix_from_csv(
        predictions_path=args.predictions,
        model_name=args.model,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

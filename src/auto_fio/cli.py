"""Command-line entry point: ``auto-fio`` / ``python -m auto_fio``."""

from __future__ import annotations

import argparse
import json
import sys

from .hints import fio_missing_warning
from .profiler import _DEFAULT_FILE_SIZE, profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="auto-fio",
        description="Automated Flexible I/O tester — recommend an optimal I/O "
        "block size for your storage device.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="directory (or file) on the device to profile (default: cwd)",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "fio", "python"],
        default="auto",
        help="measurement backend (default: auto — fio if available, else python)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="fraction of peak throughput that counts as saturated (default: 0.95)",
    )
    parser.add_argument(
        "--file-size",
        type=int,
        default=_DEFAULT_FILE_SIZE,
        help="test-file size in bytes for the python backend (default: 1 GiB)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a table",
    )
    args = parser.parse_args(argv)

    result = profile(
        args.path,
        file_size=args.file_size,
        backend=args.backend,
        threshold=args.threshold,
    )

    # Nudge toward the gold-standard backend if we silently fell back off fio.
    # Always to stderr so machine-readable stdout (--json) stays clean.
    warning = fio_missing_warning(args.backend, result.backend)
    if warning is not None:
        print(warning, file=sys.stderr)

    if args.json:
        print(
            json.dumps(
                {
                    "optimal_block_size": result.optimal_block_size,
                    "peak_throughput_mbps": round(result.peak_throughput_mbps, 2),
                    "backend": result.backend,
                    "threshold": result.threshold,
                    "samples": [
                        {
                            "block_size": s.block_size,
                            "throughput_mbps": round(s.throughput_mbps, 2),
                        }
                        for s in result.samples
                    ],
                },
                indent=2,
            )
        )
    else:
        print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

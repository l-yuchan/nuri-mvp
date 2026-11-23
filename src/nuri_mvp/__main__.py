"""Allow ``python -m nuri_mvp`` with the same interface as the console script."""

from __future__ import annotations

from nuri_mvp.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

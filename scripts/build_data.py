"""Download the raw dataset (if needed) and build the processed table.  Run: python scripts/build_data.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexmargin.data_loader import build_processed  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(build_processed(), indent=2))

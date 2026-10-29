import json
import sys
from pathlib import Path

from .graph import CampusGraph


def validate_map_file(file_path: str | Path) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Map file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    graph = CampusGraph.from_json(path)
    boundary = data.get("boundary", [])
    if len(boundary) < 3:
        raise ValueError("Map boundary must contain at least three points.")
    if data.get("campus", {}).get("map_status") not in {"DEMO", "VERIFIED"}:
        raise ValueError("campus.map_status must be DEMO or VERIFIED.")
    if not data.get("campus", {}).get("source_note"):
        raise ValueError("campus.source_note is required for traceability.")
    return {
        "file": str(path),
        "locations": len(graph.locations),
        "roads": len(data.get("roads", [])),
        "map_status": data["campus"]["map_status"],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m backend.app.validate_map <map.json>")
        return 2
    try:
        result = validate_map_file(sys.argv[1])
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Map validation failed: {error}")
        return 1
    print(
        f"Map valid: {result['file']} | "
        f"{result['locations']} locations | {result['roads']} roads | "
        f"status={result['map_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

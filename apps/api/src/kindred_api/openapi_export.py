import argparse
import json
from pathlib import Path

from kindred_api.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the API's OpenAPI schema.")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.write_text(json.dumps(app.openapi(), indent=2) + "\n")


if __name__ == "__main__":
    main()

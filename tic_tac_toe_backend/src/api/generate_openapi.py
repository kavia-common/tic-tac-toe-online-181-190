import json
import os
import sys
from pathlib import Path

# Ensure this script can be run directly via `python -m src.api.generate_openapi` or `python src/api/generate_openapi.py`
# by adding the project root to sys.path when executed as a script.
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]  # points to tic-tac-toe-online-181-190/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Import the FastAPI app
    from src.api.main import app  # noqa: WPS433  (runtime import for script use)
except Exception as exc:  # pragma: no cover - script level robustness
    raise RuntimeError(f"Failed to import FastAPI app from src.api.main: {exc}") from exc


def generate_openapi(output_dir: str = "interfaces", filename: str = "openapi.json") -> str:
    # PUBLIC_INTERFACE
    """Generate and write the OpenAPI JSON for the FastAPI app.

    Args:
        output_dir: Relative or absolute directory where the openapi.json will be written.
        filename: Name of the OpenAPI output file.

    Returns:
        The absolute path to the written OpenAPI JSON file.
    """
    # Build OpenAPI schema
    openapi_schema = app.openapi()

    # Ensure target directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Write schema to file
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    return str(Path(output_path).resolve())


if __name__ == "__main__":  # pragma: no cover - CLI usage
    path = generate_openapi()
    print(f"OpenAPI schema written to: {path}")

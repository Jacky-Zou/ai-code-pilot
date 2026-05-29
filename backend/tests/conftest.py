import sys
import os
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Keep tests away from the developer's real persisted Chroma index. Individual
# tests may still delete or override VECTOR_STORE_PATH with monkeypatch when
# they need to verify Settings defaults, but the normal test suite gets an
# isolated process-local vector store by default.
os.environ.setdefault(
    "VECTOR_STORE_PATH",
    str(Path(tempfile.gettempdir()) / f"aicodepilot_pytest_vector_store_{os.getpid()}"),
)

"""Validation of single-instance IPC messages (another MNIME launch asking us to open files)."""

import json
from typing import List

import getpass
IPC_PIPE_NAME = f"MNIME_SingleInstance_IPC_Server_{getpass.getuser()}"
MAX_IPC_BYTES = 256 * 1024     # Anything larger is not a legitimate request
MAX_IPC_FILES = 100            # Cap on files accepted from a single request
MAX_PATH_CHARS = 4096


def build_open_request(file_paths: List[str]) -> bytes:
    return json.dumps({"action": "open", "files": list(file_paths)}).encode("utf-8")


def parse_open_request(raw: bytes) -> List[str]:
    """Return the list of path strings from an 'open' request.

    Raises ValueError for anything malformed, oversized or of the wrong shape.
    Existence and extension checks are done by the receiving window.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise ValueError("payload must be bytes")
    if not raw or len(raw) > MAX_IPC_BYTES:
        raise ValueError("payload empty or too large")

    try:
        msg = json.loads(bytes(raw).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"payload is not valid JSON: {e}") from e

    if not isinstance(msg, dict) or msg.get("action") != "open":
        raise ValueError("unsupported action")

    files = msg.get("files", [])
    if not isinstance(files, list):
        raise ValueError("'files' must be a list")

    result: List[str] = []
    for f in files[:MAX_IPC_FILES]:
        if isinstance(f, str) and f and len(f) <= MAX_PATH_CHARS and "\x00" not in f:
            result.append(f)
    return result

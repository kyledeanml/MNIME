import json
import pytest
from core.ipc import parse_open_request

def test_parse_ipc_payload_valid():
    payload = json.dumps({"action": "open", "files": ["test.pdf"]}).encode("utf-8")
    assert parse_open_request(payload) == ["test.pdf"]

def test_parse_ipc_payload_invalid_json():
    with pytest.raises(ValueError):
        parse_open_request(b"not json")

def test_parse_ipc_payload_missing_files():
    payload = json.dumps({"action": "open", "other": 1}).encode("utf-8")
    assert parse_open_request(payload) == []

def test_parse_ipc_payload_not_a_list():
    payload = json.dumps({"action": "open", "files": "test.pdf"}).encode("utf-8")
    with pytest.raises(ValueError):
        parse_open_request(payload)

def test_parse_ipc_payload_empty():
    payload = json.dumps({"action": "open", "files": []}).encode("utf-8")
    assert parse_open_request(payload) == []

def test_parse_ipc_payload_too_many_files():
    files = ["file{}.pdf".format(i) for i in range(101)]
    payload = json.dumps({"action": "open", "files": files}).encode("utf-8")
    assert parse_open_request(payload) == files[:100]

def test_parse_ipc_payload_unsupported_extensions():
    # It passes through all paths, caller checks extensions
    payload = json.dumps({"action": "open", "files": ["test.pdf", "test.exe", "test.txt", "test.docx"]}).encode("utf-8")
    assert parse_open_request(payload) == ["test.pdf", "test.exe", "test.txt", "test.docx"]

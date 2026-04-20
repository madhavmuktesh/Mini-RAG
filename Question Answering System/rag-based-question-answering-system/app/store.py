import json
import os
from typing import Dict, List

from app.config import INDEX_DIR

METADATA_PATH = os.path.join(INDEX_DIR, "metadata.json")
STATUS_PATH = os.path.join(INDEX_DIR, "status.json")


def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_metadata() -> List[Dict]:
    return _read_json(METADATA_PATH, [])


def save_metadata(records: List[Dict]):
    _write_json(METADATA_PATH, records)


def append_metadata(new_records: List[Dict]):
    records = load_metadata()
    records.extend(new_records)
    save_metadata(records)


def load_status() -> Dict:
    return _read_json(STATUS_PATH, {})


def update_status(document_id: str, payload: Dict):
    status = load_status()
    status[document_id] = payload
    _write_json(STATUS_PATH, status)


def get_status(document_id: str):
    return load_status().get(document_id)
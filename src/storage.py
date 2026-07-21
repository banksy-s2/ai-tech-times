"""アトミックなJSON永続化(Codexレビュー指摘1対応)

書き込みは .tmp → os.replace で原子的に行い、直前の正常版を .bak に残す。
読み込みは本体が壊れていたら .bak にフォールバックする。
"""
import json
import os
from pathlib import Path


def load_json(path: Path, default):
    for p in (path, path.with_name(path.name + ".bak")):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [storage] {p.name} 読込失敗({e})、フォールバック")
            continue
    return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    if path.exists():
        os.replace(path, path.with_name(path.name + ".bak"))
    os.replace(tmp, path)

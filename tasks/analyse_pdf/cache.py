import re
import json
import hashlib
import shutil

from typing import TypedDict
from pathlib import Path
from oocana import Context

class _State(TypedDict):
  pdf_path: str
  pdf_mtime: float
  pdf_hash: str

def get_or_prepare_cache_dir(context: Context, pdf_path: Path):
  cache_path = Path(context.tmp_pkg_dir) / "pdf-craft"
  json_path = cache_path / "state.json"
  state: _State | None = None
  if json_path.exists():
    with open(json_path , "r", encoding="utf-8") as file:
      state = json.loads(file.read())

  should_write_state = False
  should_clean_cache = False

  pdf_path_str = re.sub(r"/$", "", str(pdf_path))
  pdf_mtime = pdf_path.stat().st_mtime

  if state is None:
    should_write_state = True
    should_clean_cache = True
    state = {
      "pdf_path": pdf_path_str,
      "pdf_mtime": pdf_mtime,
      "pdf_hash": _calculate_sha512(pdf_path),
    }
  else:
    if pdf_path_str != state["pdf_path"] or pdf_mtime != state["pdf_mtime"]:
      state["pdf_path"] = pdf_path_str
      state["pdf_mtime"] = pdf_mtime
      should_write_state = True
      pdf_hash = _calculate_sha512(pdf_path)
      if pdf_hash != state["pdf_hash"]:
        state["pdf_hash"] = pdf_hash
        should_clean_cache = True

  if should_clean_cache:
    shutil.rmtree(cache_path, ignore_errors=True)
  cache_path.mkdir(parents=True, exist_ok=True)

  if should_write_state:
    with open(json_path, "w", encoding="utf-8") as file:
      file.write(json.dumps(state, ensure_ascii=False))

  return cache_path

def _calculate_sha512(file_path: Path):
  sha512_hash = hashlib.sha512()
  chunk_size = 16384
  with open(file_path, "rb") as f:
    while True:
      byte_block = f.read(chunk_size)
      if not byte_block:
        break
      sha512_hash.update(byte_block)
  return sha512_hash.hexdigest()
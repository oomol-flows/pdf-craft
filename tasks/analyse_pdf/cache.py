import os
import hashlib

from pathlib import Path
from oocana import Context


def get_analysing_dir(context: Context, pdf_path: Path) -> Path:
  cache_path = Path(context.tmp_pkg_dir) / context.node_id
  pdf_hash = _calculate_sha512(pdf_path)
  return cache_path / pdf_hash

def _calculate_sha512(file_path):
  sha512_hash = hashlib.sha512()
  chunk_size = 16384
  with open(file_path, "rb") as f:
    while True:
      byte_block = f.read(chunk_size)
      if not byte_block:
        break
      sha512_hash.update(byte_block)
  return sha512_hash.hexdigest()
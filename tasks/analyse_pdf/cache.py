import os
import hashlib

from oocana import Context


def get_analysing_dir(context: Context, pdf_path: str):
  cache_path = os.path.join(context.tmp_pkg_dir, context.node_id)
  pdf_hash = _calculate_sha512(pdf_path)
  return os.path.join(cache_path, pdf_hash)

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
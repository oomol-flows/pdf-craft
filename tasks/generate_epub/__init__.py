#region generated meta
import typing
class Inputs(typing.TypedDict):
  analysed_dir: str
  epub_file_path: typing.Optional[str]
class Outputs(typing.TypedDict):
  epub_file_path: str
#endregion

import os

from oocana import Context
from pdf_craft import generate_epub_file

def main(params: Inputs, context: Context) -> Outputs:
  analysed_dir = params["analysed_dir"]
  epub_file_path = params["epub_file_path"]

  if epub_file_path is None:
    epub_file_path = os.path.join(
      context.session_dir,
      f"{context.job_id}.epub",
    )
  generate_epub_file(
    from_dir_path=analysed_dir,
    epub_file_path=epub_file_path,
  )
  return { "epub_file_path": epub_file_path }

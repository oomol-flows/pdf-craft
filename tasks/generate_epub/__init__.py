#region generated meta
import typing
from oocana import Context
class Inputs(typing.TypedDict):
    analysed_dir: str
    render_latex: bool
    render_table: bool
    epub_file_path: str | None
class Outputs(typing.TypedDict):
    epub_file_path: str
#endregion

from pathlib import Path
from oocana import Context
from pdf_craft import generate_epub_file, LaTeXRender, TableRender

def main(params: Inputs, context: Context) -> Outputs:
  analysed_dir_path = Path(params["analysed_dir"])
  epub_file_path = params["epub_file_path"]

  latex_render: LaTeXRender = LaTeXRender.CLIPPING
  table_render: TableRender = TableRender.CLIPPING

  if params["render_latex"]:
    latex_render = LaTeXRender.MATHML
  if params["render_table"]:
    table_render = TableRender.HTML

  if epub_file_path is None:
    epub_file_path = Path(context.session_dir) / f"{context.job_id}.epub"
  else:
    epub_file_path = Path(epub_file_path)

  epub_file_path.parent.mkdir(parents=True, exist_ok=True)

  generate_epub_file(
    from_dir_path=analysed_dir_path,
    epub_file_path=epub_file_path,
    latex_render=latex_render,
    table_render=table_render,
  )
  return { "epub_file_path": str(epub_file_path) }

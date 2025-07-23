import os

from oocana import Context
from shared import build_extractor
from pdf_craft import PDFPageExtractor, MarkDownWriter, ExtractedTableFormat

#region generated meta
import typing
class Inputs(typing.TypedDict):
    pdf: str
    markdown: str | None
    device: typing.Literal["cpu", "cuda", "cloud"]
    ocr_level: typing.Literal["once", "once_per_layout"]
    extract_formula: bool
    extract_table: bool
    assets_dir_name: str
class Outputs(typing.TypedDict):
    saved_path: str
#endregion


def main(params: Inputs, context: Context) -> Outputs:
  pdf_path = params["pdf"]
  markdown_path = params["markdown"]
  assets_dir_name = params["assets_dir_name"]

  extract_table_format: ExtractedTableFormat
  if params["extract_table"]:
    extract_table_format = ExtractedTableFormat.MARKDOWN
  else:
    extract_table_format = ExtractedTableFormat.DISABLE

  if markdown_path is None:
    markdown_path = os.path.join(
      context.session_dir,
      f"{context.job_id}.md",
    )

  extractor: PDFPageExtractor = build_extractor(
    params=params,
    context=context,
    extract_table_format=extract_table_format,
  )

  with MarkDownWriter(
    md_path=markdown_path,
    assets_path=assets_dir_name,
    encoding="utf-8",
  ) as md:
    for block in extractor.extract(
      pdf=pdf_path,
      report_progress=lambda i, n: context.report_progress(100.0 * i / n)
    ):
      md.write(block)

  return { "saved_path": markdown_path }

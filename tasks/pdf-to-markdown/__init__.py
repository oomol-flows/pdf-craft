#region generated meta
import typing
class Inputs(typing.TypedDict):
  pdf: str
  device: typing.Literal["cpu", "cuda"]
  model_dir: typing.Optional[str]
  output_file: typing.Optional[str]
  assets_dir_name: str
class Outputs(typing.TypedDict):
  output_file: str
#endregion

import os

from oocana import Context
from tempfile import mkdtemp
from pdf_craft import PDFPageExtractor, MarkDownWriter

def main(params: Inputs, context: Context) -> Outputs:
  pdf_path = params["pdf"]
  model_dir = params["model_dir"]
  output_file = params["output_file"]
  assets_dir_name = params["assets_dir_name"]

  if model_dir is None:
    model_dir = mkdtemp()
  if output_file is None:
    output_file = os.path.join(
      context.session_dir,
      context.job_id,
    )

  extractor = PDFPageExtractor(
    device=params["device"],
    model_dir_path=model_dir,
  )
  with MarkDownWriter(
    md_path=output_file,
    assets_path=assets_dir_name,
    encoding="utf-8",
  ) as md:
    for block in extractor.extract(
      pdf=pdf_path,
      report_progress=lambda i, n: context.report_progress(100.0 * i / n)
    ):
      md.write(block)

  return { "output_file": output_file }

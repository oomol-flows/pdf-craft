#region generated meta
import typing
from oocana import LLMModelOptions
class Inputs(typing.TypedDict):
    pdf: str
    device: typing.Literal["cpu", "cuda", "cloud"]
    ocr_level: typing.Literal["once", "once_per_layout"]
    correction: typing.Literal["off", "once", "detailed"]
    extract_formula: bool
    extract_table: bool
    window_tokens: int | None
    threads_count: int
    retry_times: int
    retry_interval_seconds: float
    output_dir: str | None
    llm: LLMModelOptions
class Outputs(typing.TypedDict):
    output_dir: str
#endregion

from math import ceil
from pathlib import Path
from oocana import Context
from pdf_craft import (
  analyse,
  LLM,
  PDFPageExtractor,
  ExtractedTableFormat,
  CorrectionMode,
)
from shared import build_extractor
from .cache import get_or_prepare_cache_dir
from .reporter import Reporter


def main(params: Inputs, context: Context) -> Outputs:
  env = context.oomol_llm_env
  pdf_path = Path(params["pdf"])
  output_dir_path = params["output_dir"]
  llm_model = params["llm"]

  cache_dir_path = get_or_prepare_cache_dir(context, pdf_path)
  reporter = Reporter(context, cache_dir_path)

  extract_table_format: ExtractedTableFormat
  if params["extract_table"]:
    extract_table_format = ExtractedTableFormat.HTML
  else:
    extract_table_format = ExtractedTableFormat.DISABLE

  correction_mode: CorrectionMode
  correction = params["correction"]
  if correction == "once":
    correction_mode = CorrectionMode.ONCE
  elif correction == "detailed":
    correction_mode = CorrectionMode.DETAILED
  else:
    correction_mode = CorrectionMode.NO

  window_tokens = params["window_tokens"]
  if window_tokens is not None:
    window_tokens = ceil(window_tokens)

  threads_count: int = params["threads_count"]
  if threads_count is not None:
    threads_count = ceil(threads_count)

  if output_dir_path is None:
    output_dir_path = Path(context.session_dir) / context.job_id
    output_dir_path.mkdir(parents=True, exist_ok=True)
  else:
    output_dir_path = Path(output_dir_path)

  llm = LLM(
    key=env["api_key"],
    url=env["base_url_v1"],
    model=llm_model["model"],
    top_p=float(llm_model["top_p"]),
    temperature=float(llm_model["temperature"]),
    token_encoding="o200k_base",
    retry_times=int(params["retry_times"]),
    retry_interval_seconds=params["retry_interval_seconds"],
  )
  extractor: PDFPageExtractor = build_extractor(
    params=params,
    context=context,
    extract_table_format=extract_table_format,
  )
  analyse(
    llm=llm,
    pdf_path=pdf_path,
    pdf_page_extractor=extractor,
    analysing_dir_path=cache_dir_path / "analysing",
    output_dir_path=output_dir_path,
    correction_mode=correction_mode,
    window_tokens=window_tokens,
    threads_count=threads_count,
    report_step=reporter.report_step,
    report_progress=reporter.report_progress,
  )
  return { "output_dir": str(output_dir_path) }
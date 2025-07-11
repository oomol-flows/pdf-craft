#region generated meta
import typing
from oocana import LLMModelOptions
class Inputs(typing.TypedDict):
    pdf: str
    device: typing.Literal["cpu", "cuda", "cloud"]
    model_dir: str | None
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
  AnalysingStep,
  CorrectionMode,
)
from shared import build_extractor
from .cache import get_analysing_dir


def main(params: Inputs, context: Context) -> Outputs:
  env = context.oomol_llm_env
  pdf_path = Path(params["pdf"])
  output_dir_path = params["output_dir"]
  llm_model = params["llm"]

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

  reporter = _Reporter(context)
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
    analysing_dir_path=get_analysing_dir(context, pdf_path),
    output_dir_path=output_dir_path,
    correction_mode=correction_mode,
    window_tokens=window_tokens,
    threads_count=threads_count,
    report_step=reporter.report_step,
    report_progress=reporter.report_progress,
  )
  return { "output_dir": str(output_dir_path) }

def _calculate_steps(items: tuple[tuple[AnalysingStep, int], ...]):
  step2rate: dict[AnalysingStep, tuple[float, float]] = {}
  sum_weights: int = 0
  for _, weight in items:
    sum_weights += weight
  offset: float = 0.0
  for step, weight in items:
    rate = float(weight) / float(sum_weights)
    step2rate[step] = (rate, offset)
    offset += rate
  return step2rate

_STEP2RATE_AND_OFFSET: dict[AnalysingStep, tuple[float, float]] = _calculate_steps((
  (AnalysingStep.OCR, 10),
  (AnalysingStep.EXTRACT_SEQUENCE, 4),
  (AnalysingStep.VERIFY_TEXT_PARAGRAPH, 3),
  (AnalysingStep.VERIFY_FOOTNOTE_PARAGRAPH, 2),
  (AnalysingStep.CORRECT_TEXT, 7),
  (AnalysingStep.CORRECT_FOOTNOTE, 3),
  (AnalysingStep.EXTRACT_META, 2),
  (AnalysingStep.COLLECT_CONTENTS, 1),
  (AnalysingStep.ANALYSE_CONTENTS, 6),
  (AnalysingStep.MAPPING_CONTENTS, 1),
  (AnalysingStep.GENERATE_FOOTNOTES, 1),
))

class _Reporter:
  def __init__(self, context: Context) -> None:
    self._context: Context = context
    self._scale_and_offset: tuple[float, float] = (0.0, 0.0)
    self._progress: int = 0
    self._max_progress: int | None = None

  def report_step(self, step: AnalysingStep) -> None:
    self._scale_and_offset = _STEP2RATE_AND_OFFSET[step]
    self._progress = 0
    self._max_progress = None
    self._sync_progress()

  def report_progress(self, progress: int, max_progress: int | None) -> None:
    self._progress = progress
    self._max_progress = max_progress
    self._sync_progress()

  def _sync_progress(self):
    step_progress: float = 0.0
    if self._max_progress is not None:
      step_progress = float(self._progress) / float(self._max_progress)
      step_progress = min(1.0, max(0.0, step_progress))

    scale, offset = self._scale_and_offset
    progress = step_progress * scale + offset
    self._context.report_progress(100.0 * progress)
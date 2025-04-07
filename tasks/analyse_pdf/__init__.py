#region generated meta
from math import ceil
import typing
class LLMModelOptions(typing.TypedDict):
    model: str
    temperature: float
    top_p: float
    max_tokens: int
class Inputs(typing.TypedDict):
    pdf: str
    device: typing.Literal["cpu", "cuda"]
    model_dir: str | None
    ocr_level: typing.Literal["once", "once_per_layout"]
    window_tokens: int | None
    retry_times: int
    retry_interval_seconds: float
    output_dir: str | None
    llm: LLMModelOptions
class Outputs(typing.TypedDict):
    output_dir: str
#endregion

import os
import torch

from oocana import Context
from tempfile import mkdtemp
from pdf_craft import analyse, LLM, OCRLevel, PDFPageExtractor, AnalysingStep
from .cache import get_analysing_dir


def main(params: Inputs, context: Context) -> Outputs:
  env = context.oomol_llm_env
  pdf_path = params["pdf"]
  model_dir = params["model_dir"]
  ocr_level_value = params["ocr_level"]
  output_dir = params["output_dir"]
  llm_model = params["llm"]

  if model_dir is None:
    model_dir = mkdtemp()

  window_tokens = params["window_tokens"]
  if window_tokens is not None:
    window_tokens = ceil(window_tokens)

  if output_dir is None:
    output_dir = os.path.join(
      context.session_dir,
      context.job_id,
    )
    os.makedirs(output_dir, exist_ok=True)

  ocr_level: OCRLevel
  if ocr_level_value == "once":
    ocr_level = OCRLevel.Once
  elif ocr_level_value == "once_per_layout":
    ocr_level = OCRLevel.OncePerLayout
  else:
    raise ValueError(f"ocr_level: {ocr_level_value} is not supported")

  device = params["device"]
  if device == "cuda" and not torch.cuda.is_available():
    device = "cpu"
    print("Warn: cuda is not available, use cpu instead")

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
  pdf_page_extractor = PDFPageExtractor(
    device=device,
    ocr_level=ocr_level,
    model_dir_path=model_dir,
  )
  analyse(
    llm=llm,
    pdf_page_extractor=pdf_page_extractor,
    pdf_path=pdf_path,
    analysing_dir_path=get_analysing_dir(context, pdf_path),
    output_dir_path=output_dir,
    window_tokens=window_tokens,
    report_step=reporter.report_step,
    report_progress=reporter.report_progress,
  )
  return { "output_dir": output_dir }

class _Reporter:
  def __init__(self, context: Context) -> None:
    self._context: Context = context
    self._total: int = 0
    self._offset: float = 0.0
    self._delta: float = 0.0
    self._steps = (
      AnalysingStep.OCR,
      AnalysingStep.ANALYSE_PAGE,
      AnalysingStep.EXTRACT_INDEX,
      AnalysingStep.EXTRACT_CITATION,
      AnalysingStep.EXTRACT_MAIN_TEXT,
      AnalysingStep.MARK_POSITION,
      AnalysingStep.ANALYSE_META,
      AnalysingStep.GENERATE_CHAPTERS,
    )
    self._offset_progresses: list[float] = []
    self._delta_progresses: list[float] = []
    sum_weight: float = 0.0

    for step in self._steps:
      weight = self._weight(step)
      self._offset_progresses.append(sum_weight)
      self._delta_progresses.append(weight)
      sum_weight += weight

    for i in range(len(self._steps)):
      self._offset_progresses[i] /= sum_weight
      self._delta_progresses[i] /= sum_weight

  def _weight(self, step: AnalysingStep) -> float:
    if step == AnalysingStep.OCR:
      return 5
    elif step == AnalysingStep.ANALYSE_PAGE:
      return 5
    elif step == AnalysingStep.EXTRACT_INDEX:
      return 1
    elif step == AnalysingStep.EXTRACT_CITATION:
      return 2
    elif step == AnalysingStep.EXTRACT_MAIN_TEXT:
      return 3
    elif step == AnalysingStep.MARK_POSITION:
      return 2
    elif step == AnalysingStep.ANALYSE_META:
      return 1
    elif step == AnalysingStep.GENERATE_CHAPTERS:
      return 1

  def report_step(self, reported_step: AnalysingStep, count: int):
    index: int = -1
    for i, step in enumerate(self._steps):
      if step == reported_step:
        index = i
        break

    assert index >= 0
    self._total = count
    self._delta = self._delta_progresses[index]
    self._offset = self._offset_progresses[index]
    self.report_progress(0)

  def report_progress(self, completed_count: int):
    if self._total == 0:
      return
    rate = completed_count / self._total
    progress = rate * self._delta + self._offset
    self._context.report_progress(100.0 * progress)
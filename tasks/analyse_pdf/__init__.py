#region generated meta
import typing
class Inputs(typing.TypedDict):
  pdf: str
  device: typing.Literal["cpu", "cuda"]
  model_dir: typing.Optional[str]
  analysing_dir: typing.Optional[str]
  clean_analysing_dir: bool
  output_dir: typing.Optional[str]
class Outputs(typing.TypedDict):
  output_dir: str
#endregion

import os
import shutil

from oocana import Context
from tempfile import mkdtemp
from pdf_craft import analyse, LLM, PDFPageExtractor, AnalysingStep


def main(params: Inputs, context: Context) -> Outputs:
  env = context.oomol_llm_env
  key: str = env["api_key"]
  base_url: str = env["base_url"]
  model: str = "oomol-chat" # 临时方案，先写死
  model_dir = params["model_dir"]
  analysing_dir = params["analysing_dir"]
  output_dir = params["output_dir"]

  if model_dir is None:
    model_dir = mkdtemp()

  if analysing_dir is None:
    analysing_dir = mkdtemp()
  elif params["clean_analysing_dir"]:
    shutil.rmtree(analysing_dir)

  if output_dir is None:
    output_dir = os.path.join(
      context.session_dir,
      context.job_id,
    )
    os.makedirs(output_dir, exist_ok=True)

  reporter = _Reporter(context)
  llm = LLM(
    key=key,
    url=f"{base_url}/v1",
    model=model,
    token_encoding="o200k_base",
  )
  pdf_page_extractor = PDFPageExtractor(
    device=params["device"],
    model_dir_path=model_dir,
  )
  analyse(
    llm=llm,
    pdf_page_extractor=pdf_page_extractor,
    pdf_path=params["pdf"],
    analysing_dir_path=analysing_dir,
    output_dir_path=output_dir,
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
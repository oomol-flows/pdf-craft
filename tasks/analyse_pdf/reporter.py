import json

from pathlib import Path
from oocana import Context
from pdf_craft import AnalysingStep


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
  (AnalysingStep.OCR, 30),
  (AnalysingStep.EXTRACT_SEQUENCE, 10),
  (AnalysingStep.VERIFY_TEXT_PARAGRAPH, 7),
  (AnalysingStep.VERIFY_FOOTNOTE_PARAGRAPH, 5),
  (AnalysingStep.CORRECT_TEXT, 12),
  (AnalysingStep.CORRECT_FOOTNOTE, 7),
  (AnalysingStep.EXTRACT_META, 3),
  (AnalysingStep.COLLECT_CONTENTS, 1),
  (AnalysingStep.ANALYSE_CONTENTS, 1),
  (AnalysingStep.MAPPING_CONTENTS, 1),
  (AnalysingStep.GENERATE_FOOTNOTES, 1),
  (AnalysingStep.OUTPUT, 0),
))

class Reporter:
  def __init__(self, context: Context, cache_dir_path: Path) -> None:
    self._context: Context = context
    self._state_file: Path = cache_dir_path / "progress.json"
    self._scale_and_offset: tuple[float, float] = _STEP2RATE_AND_OFFSET[AnalysingStep.OCR]
    self._progress: int = 0
    self._percent: int = 0
    self._max_progress: int | None = None

    if self._state_file.exists():
      percent: int
      with open(self._state_file, "r", encoding="utf-8") as file:
        value = json.loads(file.read())
        if isinstance(value, int) or isinstance(value, float):
          percent = round(value)
      self._report_percent(percent)

  def report_step(self, step: AnalysingStep) -> None:
    if _STEP2RATE_AND_OFFSET[step] != self._scale_and_offset:
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
    self._report_percent(round(100.0 * progress))

  def _report_percent(self, percent: int):
    if percent <= self._percent:
      return
    self._percent = percent
    self._context.report_progress(percent)
    with open(self._state_file, "w", encoding="utf-8") as file:
      file.write(json.dumps(percent))
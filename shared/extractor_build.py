import torch

from typing import TypedDict, Literal
from tempfile import mkdtemp
from pdf_craft import OCRLevel, PDFPageExtractor


class BuildParams(TypedDict):
  device: Literal["cpu", "cuda"]
  model_dir: str | None
  ocr_level: Literal["once", "once_per_layout"]

def build_extractor(params: BuildParams) -> PDFPageExtractor:
  device = params["device"]
  model_dir: str | None = params["model_dir"]
  ocr_level_value = params["ocr_level"]

  if model_dir is None:
    model_dir = mkdtemp()

  ocr_level: OCRLevel
  if ocr_level_value == "once":
    ocr_level = OCRLevel.Once
  elif ocr_level_value == "once_per_layout":
    ocr_level = OCRLevel.OncePerLayout
  else:
    raise ValueError(f"ocr_level: {ocr_level_value} is not supported")

  if device == "cuda" and not torch.cuda.is_available():
    device = "cpu"
    print("Warn: cuda is not available, use cpu instead")

  return PDFPageExtractor(
    device=device,
    ocr_level=ocr_level,
    model_dir_path=model_dir,
  )
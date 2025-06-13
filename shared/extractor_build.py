import torch

from typing import TypedDict, Literal
from pathlib import Path
from tempfile import mkdtemp
from pdf_craft import create_pdf_page_extractor, OCRLevel, PDFPageExtractor, ExtractedTableFormat


class BuildParams(TypedDict):
  device: Literal["cpu", "cuda", "cloud"]
  model_dir: str | None
  ocr_level: Literal["once", "once_per_layout"]
  extract_formula: bool

def build_extractor(
    params: BuildParams,
    extract_table_format: ExtractedTableFormat | None = None,
  ) -> PDFPageExtractor:

  device = params["device"]
  model_dir: str | None = params["model_dir"]
  ocr_level_value = params["ocr_level"]
  extract_formula = params["extract_formula"]

  if model_dir is None:
    model_dir = mkdtemp()

  ocr_level: OCRLevel
  if ocr_level_value == "once":
    ocr_level = OCRLevel.Once
  elif ocr_level_value == "once_per_layout":
    ocr_level = OCRLevel.OncePerLayout
  else:
    raise ValueError(f"ocr_level: {ocr_level_value} is not supported")

  if device == "cloud":
    pass

  if device == "cuda" and not torch.cuda.is_available():
    device = "cpu"
    print("Warn: cuda is not available, use cpu instead")

  return create_pdf_page_extractor(
    device=device,
    ocr_level=ocr_level,
    model_dir_path=Path(model_dir),
    extract_formula=extract_formula,
    extract_table_format=extract_table_format,
  )

from typing import TypedDict, Literal
from tempfile import mkdtemp
from pdf_craft import OCRLevel, PDFPageExtractor, ExtractedTableFormat
from .cloud_extractor import CloudExtractor

class BuildParams(TypedDict):
  model_dir: str | None
  ocr_level: Literal["once", "once_per_layout"]
  extract_formula: bool


def build_extractor(
    params: BuildParams,
    api_base_url: str,
    api_key: str,
    extract_table_format: ExtractedTableFormat | None = None,
  ) -> PDFPageExtractor:

  model_dir: str | None = params["model_dir"]
  ocr_level_value = params["ocr_level"]
  extract_formula = params["extract_formula"]

  ocr_level: OCRLevel
  if ocr_level_value == "once":
    ocr_level = OCRLevel.Once
  elif ocr_level_value == "once_per_layout":
    ocr_level = OCRLevel.OncePerLayout
  else:
    raise ValueError(f"ocr_level: {ocr_level_value} is not supported")

  cloud_doc_extractor = CloudExtractor(
    base_url=api_base_url,
    api_key=api_key,
  )

  return PDFPageExtractor(
    device="cuda",
    ocr_level=ocr_level,
    extract_formula=extract_formula,
    extract_table_format=extract_table_format,
    doc_extractor=cloud_doc_extractor
  )

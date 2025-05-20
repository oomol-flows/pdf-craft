from dataclasses_json import dataclass_json
from doc_page_extractor import FormulaLayout, Rectangle, OCRFragment, BaseLayout, PlainLayout, TableLayout, LayoutClass, ExtractedResult

ExtendedRectangle = dataclass_json(Rectangle)
ExtendedOCRFragment = dataclass_json(OCRFragment)
ExtendedBaseLayout = dataclass_json(BaseLayout)
ExtendedPlainLayout = dataclass_json(PlainLayout)
ExtendedFormulaLayout = dataclass_json(FormulaLayout)
ExtendedTableLayout = dataclass_json(TableLayout)

def convert_data(result: dict) -> ExtractedResult:
    assert result is not None, "result is None"

    layouts = []
    for layout in result["layouts"]:
        cls = layout["cls"]
        cls = LayoutClass(cls)
        layout["cls"] = cls
    
        if cls == LayoutClass.ISOLATE_FORMULA:
            layout = ExtendedFormulaLayout.from_dict(layout)
        elif cls == LayoutClass.TABLE:
            layout = ExtendedTableLayout.from_dict(layout)
        else:
            layout = ExtendedPlainLayout.from_dict(layout)

        layouts.append(layout)
    
    return ExtractedResult(layouts=layouts, rotation=result["rotation"], extracted_image=None, adjusted_image=None)

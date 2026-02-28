"""
Export module for generating reports and data exports.

Supported exporters:
- PDFExporter: Insights PDF, Dashboard PDF, Full Report PDF
- DocxExporter: Insights DOCX with cover page and TOC
- ExcelExporter: Multi-sheet Excel workbooks
"""


__all__ = [
    "PDFExporter",
    "DocxExporter",
    "ExcelExporter",
]


def __getattr__(name: str):
    if name == "PDFExporter":
        from export.pdf_exporter import PDFExporter
        return PDFExporter
    if name == "DocxExporter":
        from export.docx_exporter import DocxExporter
        return DocxExporter
    if name == "ExcelExporter":
        from export.excel_exporter import ExcelExporter
        return ExcelExporter
    raise AttributeError(f"module 'export' has no attribute '{name}'")

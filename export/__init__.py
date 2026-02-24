"""
Export module for generating reports and data exports.
"""


__all__ = [
    "ExcelExporter",
    "PDFExporter",
    "CSVExporter",
]


def __getattr__(name: str):
    if name == "ExcelExporter":
        from export.excel_exporter import ExcelExporter
        return ExcelExporter
    if name == "PDFExporter":
        from export.pdf_exporter import PDFExporter
        return PDFExporter
    if name == "CSVExporter":
        from export.csv_exporter import CSVExporter
        return CSVExporter
    raise AttributeError(f"module 'export' has no attribute '{name}'")

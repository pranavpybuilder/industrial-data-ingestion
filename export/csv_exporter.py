"""
CSV Exporter — REMOVED.

CSV export has been removed from the Offline Industrial Intelligence Platform.
Use PDF, DOCX, Excel, or JSON exports instead.
"""


class CSVExporter:
    """CSV export is no longer supported. Use PDF, DOCX, or Excel."""

    def __init__(self, **kwargs):
        raise NotImplementedError(
            "CSV export removed. Use PDFExporter, DocxExporter, or ExcelExporter instead."
        )

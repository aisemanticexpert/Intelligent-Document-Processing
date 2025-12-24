"""Data Sources Module"""
from .base_source import BaseDataSource, FetchedDocument, DocumentMetadata, DataSourceType
from .sec_edgar import SECEdgarDataSource
from .fred_api import FREDDataSource
from .pdf_parser import PDFParser, ParsedPDF
from .company_registry import CompanyRegistry, Company, Sector, get_company_registry

__all__ = [
    "BaseDataSource", "FetchedDocument", "DocumentMetadata", "DataSourceType",
    "SECEdgarDataSource", "FREDDataSource",
    "PDFParser", "ParsedPDF",
    "CompanyRegistry", "Company", "Sector", "get_company_registry",
]

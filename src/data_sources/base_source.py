"""
Base Data Source Module
========================

Abstract base class for all data sources in the Financial IDR Pipeline.

Author: Rajesh Kumar Gupta
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""
    SEC_EDGAR = "sec_edgar"
    FRED = "fred"
    YAHOO_FINANCE = "yahoo_finance"
    LOCAL_FILE = "local_file"
    WEB_SCRAPE = "web_scrape"


@dataclass
class DocumentMetadata:
    """Metadata for a fetched document"""
    source_id: str
    source_type: DataSourceType
    document_type: str
    company_ticker: Optional[str] = None
    company_name: Optional[str] = None
    company_cik: Optional[str] = None
    filing_date: Optional[datetime] = None
    fiscal_year: Optional[int] = None
    fiscal_quarter: Optional[str] = None
    url: Optional[str] = None
    accession_number: Optional[str] = None
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "document_type": self.document_type,
            "company_ticker": self.company_ticker,
            "company_name": self.company_name,
            "company_cik": self.company_cik,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "fiscal_year": self.fiscal_year,
            "fiscal_quarter": self.fiscal_quarter,
            "url": self.url,
            "accession_number": self.accession_number,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "fetched_at": self.fetched_at.isoformat(),
            "extra": self.extra,
        }


@dataclass
class FetchedDocument:
    """A document fetched from a data source"""
    metadata: DocumentMetadata
    content: str
    raw_content: Optional[bytes] = None
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "metadata": self.metadata.to_dict(),
            "content": self.content,
            "sections": self.sections,
            "tables": self.tables,
        }


@dataclass
class EconomicDataPoint:
    """A single economic data point"""
    series_id: str
    series_name: str
    date: datetime
    value: float
    unit: str
    source: str
    frequency: str
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "series_id": self.series_id,
            "series_name": self.series_name,
            "date": self.date.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "frequency": self.frequency,
            "extra": self.extra,
        }


class BaseDataSource(ABC):
    """
    Abstract base class for data sources.
    
    All data sources must implement:
    - fetch(): Fetch data from the source
    - validate(): Validate the fetched data
    - get_source_info(): Return information about the source
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data source.
        
        Args:
            config: Configuration dictionary for the data source
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self._validate_config()
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the configuration"""
        pass
    
    @abstractmethod
    def fetch(self, **kwargs) -> Generator[FetchedDocument, None, None]:
        """
        Fetch documents from the data source.
        
        Yields:
            FetchedDocument instances
        """
        pass
    
    @abstractmethod
    def validate(self, document: FetchedDocument) -> bool:
        """
        Validate a fetched document.
        
        Args:
            document: The document to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about this data source.
        
        Returns:
            Dictionary with source information
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if this data source is enabled"""
        return self.enabled
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(enabled={self.enabled})"


class DataSourceRegistry:
    """Registry for managing data sources"""
    
    _sources: Dict[DataSourceType, type] = {}
    
    @classmethod
    def register(cls, source_type: DataSourceType):
        """Decorator to register a data source class"""
        def decorator(source_class: type):
            cls._sources[source_type] = source_class
            return source_class
        return decorator
    
    @classmethod
    def get(cls, source_type: DataSourceType) -> Optional[type]:
        """Get a data source class by type"""
        return cls._sources.get(source_type)
    
    @classmethod
    def create(cls, source_type: DataSourceType, config: Dict) -> Optional[BaseDataSource]:
        """Create a data source instance"""
        source_class = cls.get(source_type)
        if source_class:
            return source_class(config)
        return None
    
    @classmethod
    def list_sources(cls) -> List[DataSourceType]:
        """List all registered data source types"""
        return list(cls._sources.keys())

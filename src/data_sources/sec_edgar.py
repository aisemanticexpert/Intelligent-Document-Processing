"""
SEC EDGAR Data Source Module
=============================

Fetches 10-K, 10-Q, and 8-K filings from SEC EDGAR.

Author: Rajesh Kumar Gupta
"""

import re
import time
import hashlib
import logging
from typing import Dict, List, Any, Generator, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .base_source import (
    BaseDataSource, DataSourceType, DataSourceRegistry,
    FetchedDocument, DocumentMetadata
)

logger = logging.getLogger(__name__)


@dataclass
class SECFiling:
    """Represents an SEC filing"""
    accession_number: str
    filing_type: str
    filing_date: datetime
    document_url: str
    company_name: str
    cik: str
    ticker: Optional[str] = None


@DataSourceRegistry.register(DataSourceType.SEC_EDGAR)
class SECEdgarDataSource(BaseDataSource):
    """
    Data source for SEC EDGAR filings.
    
    Fetches 10-K, 10-Q, 8-K filings for specified companies.
    """
    
    # Section patterns for 10-K parsing
    SECTION_PATTERNS = {
        "item_1": r"(?:ITEM\s*1\.?\s*[-–—]?\s*BUSINESS|PART\s*I.*?ITEM\s*1)",
        "item_1a": r"ITEM\s*1A\.?\s*[-–—]?\s*RISK\s*FACTORS",
        "item_7": r"ITEM\s*7\.?\s*[-–—]?\s*MANAGEMENT['\u2019]?S\s*DISCUSSION",
        "item_8": r"ITEM\s*8\.?\s*[-–—]?\s*FINANCIAL\s*STATEMENTS",
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://www.sec.gov/cgi-bin/browse-edgar")
        self.api_url = config.get("api_url", "https://data.sec.gov")
        self.user_agent = config.get("user_agent", "SemanticExpertAI/1.0")
        self.rate_limit = config.get("rate_limit", 10)
        self.filing_types = config.get("filing_types", ["10-K", "10-Q", "8-K"])
        self._last_request_time = 0
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate configuration"""
        if not self.user_agent:
            raise ValueError("SEC EDGAR requires a user agent")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting"""
        elapsed = time.time() - self._last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, headers: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited request"""
        self._rate_limit()
        default_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        if headers:
            default_headers.update(headers)
        
        response = requests.get(url, headers=default_headers, timeout=30)
        response.raise_for_status()
        return response
    
    def get_company_filings(
        self, 
        cik: str, 
        filing_type: str = "10-K", 
        count: int = 10
    ) -> List[SECFiling]:
        """
        Get filings for a company.
        
        Args:
            cik: Company CIK number
            filing_type: Type of filing (10-K, 10-Q, 8-K)
            count: Number of filings to retrieve
            
        Returns:
            List of SECFiling objects
        """
        filings = []
        
        # Normalize CIK (remove leading zeros for API, keep for URLs)
        cik_normalized = cik.lstrip("0")
        cik_padded = cik.zfill(10)
        
        # Use the submissions API
        url = f"{self.api_url}/submissions/CIK{cik_padded}.json"
        
        try:
            response = self._make_request(url)
            data = response.json()
            
            company_name = data.get("name", "Unknown")
            recent_filings = data.get("filings", {}).get("recent", {})
            
            form_types = recent_filings.get("form", [])
            filing_dates = recent_filings.get("filingDate", [])
            accession_numbers = recent_filings.get("accessionNumber", [])
            primary_documents = recent_filings.get("primaryDocument", [])
            
            found = 0
            for i, form_type in enumerate(form_types):
                if found >= count:
                    break
                    
                if form_type == filing_type:
                    accession = accession_numbers[i].replace("-", "")
                    doc_url = (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik_normalized}/{accession}/{primary_documents[i]}"
                    )
                    
                    filing = SECFiling(
                        accession_number=accession_numbers[i],
                        filing_type=form_type,
                        filing_date=datetime.strptime(filing_dates[i], "%Y-%m-%d"),
                        document_url=doc_url,
                        company_name=company_name,
                        cik=cik,
                    )
                    filings.append(filing)
                    found += 1
                    
            logger.info(f"Found {len(filings)} {filing_type} filings for CIK {cik}")
            
        except Exception as e:
            logger.error(f"Error fetching filings for CIK {cik}: {e}")
        
        return filings
    
    def fetch_filing_content(self, filing: SECFiling) -> Optional[str]:
        """
        Fetch the content of a filing.
        
        Args:
            filing: SECFiling object
            
        Returns:
            Filing content as text
        """
        try:
            response = self._make_request(filing.document_url)
            content = response.text
            
            # Clean HTML if present
            if "<html" in content.lower() or "<body" in content.lower():
                soup = BeautifulSoup(content, "html.parser")
                
                # Remove script and style elements
                for element in soup(["script", "style", "meta", "link"]):
                    element.decompose()
                
                # Get text
                content = soup.get_text(separator="\n")
            
            # Clean up whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r' +', ' ', content)
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error fetching filing content: {e}")
            return None
    
    def extract_sections(self, content: str) -> Dict[str, str]:
        """
        Extract sections from a 10-K filing.
        
        Args:
            content: Filing content
            
        Returns:
            Dictionary of section name to content
        """
        sections = {}
        content_upper = content.upper()
        
        # Find section positions
        section_positions = []
        for section_name, pattern in self.SECTION_PATTERNS.items():
            matches = list(re.finditer(pattern, content_upper, re.IGNORECASE))
            for match in matches:
                section_positions.append((match.start(), section_name, match.end()))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[0])
        
        # Extract content between sections
        for i, (start, name, content_start) in enumerate(section_positions):
            if i + 1 < len(section_positions):
                end = section_positions[i + 1][0]
            else:
                end = min(start + 50000, len(content))  # Limit section size
            
            section_content = content[content_start:end].strip()
            sections[name] = section_content
        
        return sections
    
    def fetch(
        self, 
        companies: List[Dict[str, str]], 
        filing_types: Optional[List[str]] = None,
        count_per_company: int = 1,
        **kwargs
    ) -> Generator[FetchedDocument, None, None]:
        """
        Fetch filings for multiple companies.
        
        Args:
            companies: List of company dicts with 'cik', 'ticker', 'name'
            filing_types: List of filing types to fetch
            count_per_company: Number of filings per company
            
        Yields:
            FetchedDocument instances
        """
        filing_types = filing_types or self.filing_types
        
        for company in companies:
            cik = company.get("cik", "").lstrip("0").zfill(10)
            ticker = company.get("ticker", "")
            company_name = company.get("name", "")
            
            logger.info(f"Fetching filings for {company_name} ({ticker})")
            
            for filing_type in filing_types:
                filings = self.get_company_filings(cik, filing_type, count_per_company)
                
                for filing in filings:
                    content = self.fetch_filing_content(filing)
                    
                    if content:
                        # Extract sections for 10-K
                        sections = {}
                        if filing_type == "10-K":
                            sections = self.extract_sections(content)
                        
                        # Create metadata
                        metadata = DocumentMetadata(
                            source_id=f"sec_{filing.accession_number}",
                            source_type=DataSourceType.SEC_EDGAR,
                            document_type=filing_type,
                            company_ticker=ticker,
                            company_name=company_name,
                            company_cik=cik,
                            filing_date=filing.filing_date,
                            fiscal_year=filing.filing_date.year,
                            url=filing.document_url,
                            accession_number=filing.accession_number,
                            checksum=hashlib.md5(content.encode()).hexdigest(),
                        )
                        
                        doc = FetchedDocument(
                            metadata=metadata,
                            content=content,
                            sections=sections,
                        )
                        
                        yield doc
    
    def validate(self, document: FetchedDocument) -> bool:
        """Validate a fetched document"""
        if not document.content:
            return False
        if len(document.content) < 1000:
            return False
        if not document.metadata.accession_number:
            return False
        return True
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about this data source"""
        return {
            "name": "SEC EDGAR",
            "type": DataSourceType.SEC_EDGAR.value,
            "base_url": self.api_url,
            "filing_types": self.filing_types,
            "rate_limit": self.rate_limit,
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_financial_tables(content: str) -> List[Dict]:
    """
    Extract financial tables from filing content.
    
    This is a simplified implementation. In production, use
    specialized table extraction libraries.
    """
    tables = []
    
    # Simple pattern to find numerical data
    # In production, use more sophisticated table detection
    table_patterns = [
        r"(?:Revenue|Net\s+Sales|Total\s+Revenue)\s*\$?\s*([\d,]+(?:\.\d+)?)",
        r"(?:Net\s+Income|Net\s+Earnings)\s*\$?\s*([\d,]+(?:\.\d+)?)",
        r"(?:Total\s+Assets)\s*\$?\s*([\d,]+(?:\.\d+)?)",
        r"(?:Total\s+Liabilities)\s*\$?\s*([\d,]+(?:\.\d+)?)",
    ]
    
    for pattern in table_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            tables.append({
                "pattern": pattern,
                "values": matches[:5],  # Limit to first 5 matches
            })
    
    return tables


def get_fiscal_year_from_date(filing_date: datetime) -> int:
    """Determine fiscal year from filing date"""
    # 10-K filings are typically filed within 60-90 days of fiscal year end
    # Most companies have Dec 31 fiscal year end
    if filing_date.month <= 3:
        return filing_date.year - 1
    return filing_date.year

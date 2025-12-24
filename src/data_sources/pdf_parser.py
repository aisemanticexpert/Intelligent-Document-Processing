"""
PDF Document Parser Module
===========================

Parses PDF documents (10-K, 10-Q filings) and extracts structured content.
Supports multiple PDF libraries with fallback options.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Try to import PDF libraries
PDF_LIBRARY = None

try:
    import pdfplumber
    PDF_LIBRARY = "pdfplumber"
    logger.info("Using pdfplumber for PDF parsing")
except ImportError:
    pass

if not PDF_LIBRARY:
    try:
        from PyPDF2 import PdfReader
        PDF_LIBRARY = "pypdf2"
        logger.info("Using PyPDF2 for PDF parsing")
    except ImportError:
        pass

if not PDF_LIBRARY:
    try:
        import fitz  # PyMuPDF
        PDF_LIBRARY = "pymupdf"
        logger.info("Using PyMuPDF for PDF parsing")
    except ImportError:
        logger.warning("No PDF library available. Install: pip install pdfplumber")


@dataclass
class PDFPage:
    """Represents a single PDF page"""
    page_number: int
    text: str
    tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedPDF:
    """Result of PDF parsing"""
    filename: str
    total_pages: int
    pages: List[PDFPage]
    full_text: str
    metadata: Dict[str, Any]
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[Dict] = field(default_factory=list)
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get content of a specific section"""
        return self.sections.get(section_name)
    
    def to_dict(self) -> Dict:
        return {
            "filename": self.filename,
            "total_pages": self.total_pages,
            "metadata": self.metadata,
            "sections": list(self.sections.keys()),
            "table_count": len(self.tables),
            "text_length": len(self.full_text),
        }


class PDFParser:
    """
    PDF Document Parser for Financial Documents
    
    Features:
    - Multi-library support (pdfplumber, PyPDF2, PyMuPDF)
    - Table extraction
    - Section detection for 10-K/10-Q filings
    - Text cleaning and normalization
    """
    
    # 10-K Section patterns
    SECTION_10K_PATTERNS = {
        "cover_page": r"FORM\s+10-K",
        "item_1_business": r"ITEM\s*1\.?\s*[-–—]?\s*BUSINESS",
        "item_1a_risk_factors": r"ITEM\s*1A\.?\s*[-–—]?\s*RISK\s*FACTORS",
        "item_1b_unresolved_comments": r"ITEM\s*1B\.?\s*[-–—]?\s*UNRESOLVED\s*STAFF\s*COMMENTS",
        "item_2_properties": r"ITEM\s*2\.?\s*[-–—]?\s*PROPERTIES",
        "item_3_legal": r"ITEM\s*3\.?\s*[-–—]?\s*LEGAL\s*PROCEEDINGS",
        "item_4_mine_safety": r"ITEM\s*4\.?\s*[-–—]?\s*MINE\s*SAFETY",
        "item_5_market": r"ITEM\s*5\.?\s*[-–—]?\s*MARKET\s*FOR",
        "item_6_selected_financial": r"ITEM\s*6\.?\s*[-–—]?\s*(?:RESERVED|\[RESERVED\]|SELECTED\s*FINANCIAL)",
        "item_7_mda": r"ITEM\s*7\.?\s*[-–—]?\s*MANAGEMENT['\u2019]?S\s*DISCUSSION",
        "item_7a_market_risk": r"ITEM\s*7A\.?\s*[-–—]?\s*QUANTITATIVE\s*AND\s*QUALITATIVE",
        "item_8_financial_statements": r"ITEM\s*8\.?\s*[-–—]?\s*FINANCIAL\s*STATEMENTS",
        "item_9_disagreements": r"ITEM\s*9\.?\s*[-–—]?\s*CHANGES\s*IN\s*AND\s*DISAGREEMENTS",
        "item_9a_controls": r"ITEM\s*9A\.?\s*[-–—]?\s*CONTROLS\s*AND\s*PROCEDURES",
        "item_9b_other": r"ITEM\s*9B\.?\s*[-–—]?\s*OTHER\s*INFORMATION",
        "item_10_directors": r"ITEM\s*10\.?\s*[-–—]?\s*DIRECTORS",
        "item_11_compensation": r"ITEM\s*11\.?\s*[-–—]?\s*EXECUTIVE\s*COMPENSATION",
        "item_12_ownership": r"ITEM\s*12\.?\s*[-–—]?\s*SECURITY\s*OWNERSHIP",
        "item_13_relationships": r"ITEM\s*13\.?\s*[-–—]?\s*CERTAIN\s*RELATIONSHIPS",
        "item_14_fees": r"ITEM\s*14\.?\s*[-–—]?\s*PRINCIPAL\s*ACCOUNT",
        "item_15_exhibits": r"ITEM\s*15\.?\s*[-–—]?\s*EXHIBITS",
        "signatures": r"SIGNATURES",
    }
    
    # 10-Q Section patterns
    SECTION_10Q_PATTERNS = {
        "cover_page": r"FORM\s+10-Q",
        "part1_item1_financials": r"PART\s*I.*ITEM\s*1\.?\s*[-–—]?\s*FINANCIAL\s*STATEMENTS",
        "part1_item2_mda": r"ITEM\s*2\.?\s*[-–—]?\s*MANAGEMENT['\u2019]?S\s*DISCUSSION",
        "part1_item3_market_risk": r"ITEM\s*3\.?\s*[-–—]?\s*QUANTITATIVE",
        "part1_item4_controls": r"ITEM\s*4\.?\s*[-–—]?\s*CONTROLS",
        "part2_item1_legal": r"PART\s*II.*ITEM\s*1\.?\s*[-–—]?\s*LEGAL",
        "part2_item1a_risk": r"ITEM\s*1A\.?\s*[-–—]?\s*RISK\s*FACTORS",
        "part2_item6_exhibits": r"ITEM\s*6\.?\s*[-–—]?\s*EXHIBITS",
        "signatures": r"SIGNATURES",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF parser.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.extract_tables = self.config.get("extract_tables", True)
        self.max_pages = self.config.get("max_pages", None)
        
        if not PDF_LIBRARY:
            logger.warning("No PDF library available. PDF parsing will fail.")
        
        logger.info(f"PDFParser initialized (library: {PDF_LIBRARY})")
    
    def parse(self, source: Any, filename: str = "document.pdf") -> ParsedPDF:
        """
        Parse a PDF document.
        
        Args:
            source: File path (str/Path), bytes, or file-like object
            filename: Name of the file (for metadata)
            
        Returns:
            ParsedPDF object with extracted content
        """
        if not PDF_LIBRARY:
            raise RuntimeError("No PDF library available. Install: pip install pdfplumber")
        
        # Handle different input types
        if isinstance(source, (str, Path)):
            return self._parse_file(Path(source))
        elif isinstance(source, bytes):
            return self._parse_bytes(source, filename)
        else:
            # Assume file-like object
            return self._parse_fileobj(source, filename)
    
    def _parse_file(self, filepath: Path) -> ParsedPDF:
        """Parse PDF from file path"""
        if PDF_LIBRARY == "pdfplumber":
            return self._parse_with_pdfplumber(filepath)
        elif PDF_LIBRARY == "pypdf2":
            return self._parse_with_pypdf2(filepath)
        elif PDF_LIBRARY == "pymupdf":
            return self._parse_with_pymupdf(filepath)
        else:
            raise RuntimeError("No PDF library available")
    
    def _parse_bytes(self, data: bytes, filename: str) -> ParsedPDF:
        """Parse PDF from bytes"""
        buffer = io.BytesIO(data)
        return self._parse_fileobj(buffer, filename)
    
    def _parse_fileobj(self, fileobj: Any, filename: str) -> ParsedPDF:
        """Parse PDF from file-like object"""
        if PDF_LIBRARY == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(fileobj) as pdf:
                return self._extract_pdfplumber(pdf, filename)
        elif PDF_LIBRARY == "pypdf2":
            from PyPDF2 import PdfReader
            reader = PdfReader(fileobj)
            return self._extract_pypdf2(reader, filename)
        elif PDF_LIBRARY == "pymupdf":
            import fitz
            doc = fitz.open(stream=fileobj.read(), filetype="pdf")
            return self._extract_pymupdf(doc, filename)
        else:
            raise RuntimeError("No PDF library available")
    
    def _parse_with_pdfplumber(self, filepath: Path) -> ParsedPDF:
        """Parse using pdfplumber"""
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            return self._extract_pdfplumber(pdf, filepath.name)
    
    def _extract_pdfplumber(self, pdf: Any, filename: str) -> ParsedPDF:
        """Extract content using pdfplumber"""
        import pdfplumber
        
        pages = []
        all_text = []
        all_tables = []
        
        max_pages = self.max_pages or len(pdf.pages)
        
        for i, page in enumerate(pdf.pages[:max_pages]):
            # Extract text
            text = page.extract_text() or ""
            
            # Extract tables
            tables = []
            if self.extract_tables:
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables = page_tables
                        for table in page_tables:
                            all_tables.append({
                                "page": i + 1,
                                "data": table,
                            })
                except Exception as e:
                    logger.warning(f"Table extraction failed on page {i+1}: {e}")
            
            pdf_page = PDFPage(
                page_number=i + 1,
                text=text,
                tables=tables,
            )
            pages.append(pdf_page)
            all_text.append(text)
        
        full_text = "\n\n".join(all_text)
        
        # Extract metadata
        metadata = {
            "producer": pdf.metadata.get("Producer", "") if pdf.metadata else "",
            "creator": pdf.metadata.get("Creator", "") if pdf.metadata else "",
        }
        
        # Detect sections
        sections = self._detect_sections(full_text)
        
        return ParsedPDF(
            filename=filename,
            total_pages=len(pdf.pages),
            pages=pages,
            full_text=full_text,
            metadata=metadata,
            sections=sections,
            tables=all_tables,
        )
    
    def _parse_with_pypdf2(self, filepath: Path) -> ParsedPDF:
        """Parse using PyPDF2"""
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        return self._extract_pypdf2(reader, filepath.name)
    
    def _extract_pypdf2(self, reader: Any, filename: str) -> ParsedPDF:
        """Extract content using PyPDF2"""
        pages = []
        all_text = []
        
        max_pages = self.max_pages or len(reader.pages)
        
        for i, page in enumerate(reader.pages[:max_pages]):
            text = page.extract_text() or ""
            
            pdf_page = PDFPage(
                page_number=i + 1,
                text=text,
            )
            pages.append(pdf_page)
            all_text.append(text)
        
        full_text = "\n\n".join(all_text)
        
        # Extract metadata
        metadata = {}
        if reader.metadata:
            metadata = {
                "producer": reader.metadata.get("/Producer", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "title": reader.metadata.get("/Title", ""),
            }
        
        sections = self._detect_sections(full_text)
        
        return ParsedPDF(
            filename=filename,
            total_pages=len(reader.pages),
            pages=pages,
            full_text=full_text,
            metadata=metadata,
            sections=sections,
            tables=[],  # PyPDF2 doesn't extract tables
        )
    
    def _parse_with_pymupdf(self, filepath: Path) -> ParsedPDF:
        """Parse using PyMuPDF"""
        import fitz
        doc = fitz.open(filepath)
        return self._extract_pymupdf(doc, filepath.name)
    
    def _extract_pymupdf(self, doc: Any, filename: str) -> ParsedPDF:
        """Extract content using PyMuPDF"""
        pages = []
        all_text = []
        
        max_pages = self.max_pages or doc.page_count
        
        for i in range(min(max_pages, doc.page_count)):
            page = doc[i]
            text = page.get_text()
            
            pdf_page = PDFPage(
                page_number=i + 1,
                text=text,
            )
            pages.append(pdf_page)
            all_text.append(text)
        
        full_text = "\n\n".join(all_text)
        
        metadata = doc.metadata or {}
        sections = self._detect_sections(full_text)
        
        doc.close()
        
        return ParsedPDF(
            filename=filename,
            total_pages=doc.page_count,
            pages=pages,
            full_text=full_text,
            metadata=metadata,
            sections=sections,
            tables=[],
        )
    
    def _detect_sections(self, text: str) -> Dict[str, str]:
        """
        Detect and extract sections from 10-K/10-Q document.
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary of section name to content
        """
        sections = {}
        text_upper = text.upper()
        
        # Determine if 10-K or 10-Q
        patterns = self.SECTION_10K_PATTERNS
        if re.search(r"FORM\s+10-Q", text_upper):
            patterns = self.SECTION_10Q_PATTERNS
        
        # Find section positions
        section_positions = []
        for section_name, pattern in patterns.items():
            matches = list(re.finditer(pattern, text_upper))
            if matches:
                # Take the first match
                match = matches[0]
                section_positions.append((match.start(), section_name))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[0])
        
        # Extract content between sections
        for i, (start_pos, section_name) in enumerate(section_positions):
            # Find end position (start of next section or end of document)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = min(start_pos + 100000, len(text))  # Limit section size
            
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            
            # Clean up the content
            section_content = self._clean_section_text(section_content)
            
            if len(section_content) > 100:  # Only include substantial sections
                sections[section_name] = section_content
        
        logger.info(f"Detected {len(sections)} sections")
        return sections
    
    def _clean_section_text(self, text: str) -> str:
        """Clean and normalize section text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'Table of Contents', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_financial_tables(self, parsed_pdf: ParsedPDF) -> List[Dict]:
        """
        Extract and parse financial tables from PDF.
        
        Args:
            parsed_pdf: ParsedPDF object
            
        Returns:
            List of parsed financial tables
        """
        financial_tables = []
        
        for table_info in parsed_pdf.tables:
            table_data = table_info.get("data", [])
            if not table_data:
                continue
            
            # Check if it looks like a financial table
            if self._is_financial_table(table_data):
                parsed_table = self._parse_financial_table(table_data)
                if parsed_table:
                    parsed_table["page"] = table_info.get("page")
                    financial_tables.append(parsed_table)
        
        return financial_tables
    
    def _is_financial_table(self, table_data: List[List[str]]) -> bool:
        """Check if table contains financial data"""
        if not table_data or len(table_data) < 2:
            return False
        
        # Flatten table text
        flat_text = " ".join(" ".join(str(cell or "") for cell in row) for row in table_data)
        flat_text_lower = flat_text.lower()
        
        # Look for financial keywords
        financial_keywords = [
            "revenue", "sales", "income", "expense", "profit", "loss",
            "assets", "liabilities", "equity", "cash", "earnings",
            "fiscal", "quarter", "year ended", "december", "march",
        ]
        
        keyword_count = sum(1 for kw in financial_keywords if kw in flat_text_lower)
        
        # Look for dollar amounts
        dollar_pattern = r'\$[\d,]+(?:\.\d+)?|\d+(?:,\d{3})+(?:\.\d+)?'
        dollar_matches = re.findall(dollar_pattern, flat_text)
        
        return keyword_count >= 2 or len(dollar_matches) >= 3
    
    def _parse_financial_table(self, table_data: List[List[str]]) -> Optional[Dict]:
        """Parse a financial table into structured format"""
        if not table_data:
            return None
        
        # Try to identify header row
        headers = []
        data_rows = []
        
        for i, row in enumerate(table_data):
            if i == 0:
                headers = [str(cell or "").strip() for cell in row]
            else:
                data_rows.append([str(cell or "").strip() for cell in row])
        
        return {
            "headers": headers,
            "rows": data_rows,
            "row_count": len(data_rows),
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def download_and_parse_10k(url: str, parser: Optional[PDFParser] = None) -> Optional[ParsedPDF]:
    """
    Download and parse a 10-K PDF from URL.
    
    Args:
        url: URL to the PDF
        parser: Optional PDFParser instance
        
    Returns:
        ParsedPDF or None if failed
    """
    import requests
    
    parser = parser or PDFParser()
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Check if it's a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not url.endswith(".pdf"):
            logger.warning(f"URL may not be a PDF: {content_type}")
        
        return parser.parse(response.content, filename=url.split("/")[-1])
        
    except Exception as e:
        logger.error(f"Failed to download/parse PDF: {e}")
        return None


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Simple helper to extract text from PDF bytes"""
    parser = PDFParser()
    try:
        result = parser.parse(pdf_bytes)
        return result.full_text
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return ""

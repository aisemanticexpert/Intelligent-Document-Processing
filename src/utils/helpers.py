"""
Utility Functions for Financial IDR Pipeline
=============================================

Common utilities for text processing, file handling, and data transformation.

Author: Rajesh Kumar Gupta
"""

import re
import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\'\"\$\%\(\)]', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def normalize_company_name(name: str) -> str:
    """Normalize company name for matching"""
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove common suffixes
    suffixes = [
        r'\s+inc\.?$', r'\s+corp\.?$', r'\s+corporation$',
        r'\s+ltd\.?$', r'\s+llc$', r'\s+l\.?p\.?$',
        r'\s+company$', r'\s+co\.?$', r'\s+plc$',
        r',\s+inc\.?$', r',\s+corp\.?$',
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized


def extract_fiscal_period(text: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract fiscal year and quarter from text"""
    fiscal_year = None
    fiscal_quarter = None
    
    # Look for fiscal year
    year_match = re.search(r'(?:fiscal\s+)?(?:year|FY)\s*(\d{4})', text, re.IGNORECASE)
    if year_match:
        fiscal_year = int(year_match.group(1))
    
    # Look for quarter
    quarter_match = re.search(r'(?:Q|quarter)\s*([1-4])', text, re.IGNORECASE)
    if quarter_match:
        fiscal_quarter = f"Q{quarter_match.group(1)}"
    
    return fiscal_year, fiscal_quarter


def parse_monetary_value(text: str) -> Tuple[Optional[float], str]:
    """Parse monetary value from text"""
    if not text:
        return None, "USD"
    
    # Remove commas and whitespace
    clean = text.replace(',', '').strip()
    
    # Extract numeric value
    match = re.search(r'\$?\s*([\d.]+)\s*(billion|million|thousand|B|M|K)?', clean, re.IGNORECASE)
    
    if not match:
        return None, "USD"
    
    value = float(match.group(1))
    multiplier = match.group(2)
    
    if multiplier:
        multiplier_lower = multiplier.lower()
        if multiplier_lower in ['billion', 'b']:
            value *= 1_000_000_000
        elif multiplier_lower in ['million', 'm']:
            value *= 1_000_000
        elif multiplier_lower in ['thousand', 'k']:
            value *= 1_000
    
    return value, "USD"


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Try to end at sentence boundary
        if end < text_length:
            # Look for sentence ending
            for punct in ['. ', '! ', '? ', '\n']:
                last_punct = text.rfind(punct, start + chunk_size // 2, end)
                if last_punct != -1:
                    end = last_punct + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < text_length else text_length
    
    return chunks


# =============================================================================
# FILE UTILITIES
# =============================================================================

def ensure_directory(path: str) -> str:
    """Ensure directory exists and return path"""
    os.makedirs(path, exist_ok=True)
    return path


def compute_file_hash(content: bytes) -> str:
    """Compute MD5 hash of file content"""
    return hashlib.md5(content).hexdigest()


def save_json(data: Any, filepath: str, indent: int = 2) -> str:
    """Save data to JSON file"""
    ensure_directory(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
    return filepath


def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def is_valid_ticker(ticker: str) -> bool:
    """Validate stock ticker symbol"""
    if not ticker:
        return False
    return bool(re.match(r'^[A-Z]{1,5}$', ticker))


def is_valid_cik(cik: str) -> bool:
    """Validate SEC CIK number"""
    if not cik:
        return False
    clean_cik = cik.lstrip('0')
    return clean_cik.isdigit() and len(clean_cik) <= 10


def is_valid_accession(accession: str) -> bool:
    """Validate SEC accession number"""
    if not accession:
        return False
    return bool(re.match(r'^\d{10}-\d{2}-\d{6}$', accession))


# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """Setup logging configuration"""
    log_format = log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
    )
    
    # Add file handler if specified
    if log_file:
        ensure_directory(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    return logging.getLogger(__name__)


# =============================================================================
# DATA TRANSFORMATION UTILITIES
# =============================================================================

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


# =============================================================================
# SEC SPECIFIC UTILITIES
# =============================================================================

def format_cik(cik: str) -> str:
    """Format CIK to 10-digit padded format"""
    return cik.lstrip('0').zfill(10)


def parse_accession_number(accession: str) -> Dict[str, str]:
    """Parse SEC accession number"""
    # Format: 0000320193-23-000077
    parts = accession.split('-')
    if len(parts) == 3:
        return {
            "cik": parts[0],
            "year": f"20{parts[1]}" if len(parts[1]) == 2 else parts[1],
            "sequence": parts[2],
        }
    return {"raw": accession}


def build_sec_filing_url(cik: str, accession: str, filename: str) -> str:
    """Build SEC EDGAR filing URL"""
    cik_clean = cik.lstrip('0')
    accession_clean = accession.replace('-', '')
    return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{filename}"

"""
IDR Document Classifier Module
===============================

Classifies financial documents into predefined categories based on
content analysis and ontology-guided rules.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import sys
sys.path.append('..')
from ontology.namespaces import DocumentClass, SEI_DOC

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types for classification"""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    PROXY_STATEMENT = "DEF14A"
    EQUITY_RESEARCH = "equity_research"
    EARNINGS_CALL = "earnings_call"
    PRESS_RELEASE = "press_release"
    ECONOMIC_DATA = "economic_data"
    NEWS_ARTICLE = "news_article"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: DocumentType
    ontology_class: str
    confidence: float
    matched_patterns: List[str] = field(default_factory=list)
    sections_detected: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "document_type": self.document_type.value,
            "ontology_class": self.ontology_class,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "sections_detected": self.sections_detected,
            "metadata": self.metadata,
        }


class DocumentClassifier:
    """
    Intelligent Document Recognition (IDR) - Document Classifier
    
    Classifies documents using:
    1. Pattern matching for document type indicators
    2. Section detection for structural analysis
    3. Ontology-guided classification rules
    
    This is the first stage of the IDR pipeline.
    """
    
    # Document type patterns
    CLASSIFICATION_PATTERNS = {
        DocumentType.FORM_10K: {
            "patterns": [
                r"FORM\s+10-K",
                r"ANNUAL\s+REPORT\s+PURSUANT\s+TO\s+SECTION\s+13",
                r"For\s+the\s+fiscal\s+year\s+ended",
                r"UNITED\s+STATES\s+SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION.*10-K",
            ],
            "weight": 1.0,
            "required_sections": ["item_1", "item_1a", "item_7", "item_8"],
            "ontology_class": str(DocumentClass.FORM_10K.value),
        },
        DocumentType.FORM_10Q: {
            "patterns": [
                r"FORM\s+10-Q",
                r"QUARTERLY\s+REPORT\s+PURSUANT\s+TO\s+SECTION\s+13",
                r"For\s+the\s+quarterly\s+period\s+ended",
                r"UNITED\s+STATES\s+SECURITIES\s+AND\s+EXCHANGE\s+COMMISSION.*10-Q",
            ],
            "weight": 1.0,
            "required_sections": ["item_1", "item_2"],
            "ontology_class": str(DocumentClass.FORM_10Q.value),
        },
        DocumentType.FORM_8K: {
            "patterns": [
                r"FORM\s+8-K",
                r"CURRENT\s+REPORT\s+PURSUANT\s+TO\s+SECTION\s+13",
                r"Date\s+of\s+Report.*Date\s+of\s+earliest\s+event\s+reported",
            ],
            "weight": 1.0,
            "required_sections": [],
            "ontology_class": str(DocumentClass.FORM_8K.value),
        },
        DocumentType.PROXY_STATEMENT: {
            "patterns": [
                r"PROXY\s+STATEMENT",
                r"DEF\s*14A",
                r"SCHEDULE\s+14A",
                r"NOTICE\s+OF\s+ANNUAL\s+MEETING",
            ],
            "weight": 1.0,
            "required_sections": [],
            "ontology_class": str(DocumentClass.PROXY_STATEMENT.value),
        },
        DocumentType.EQUITY_RESEARCH: {
            "patterns": [
                r"(?:BUY|SELL|HOLD|NEUTRAL|OUTPERFORM|UNDERPERFORM)\s+(?:RATING|RECOMMENDATION)",
                r"PRICE\s+TARGET",
                r"INVESTMENT\s+THESIS",
                r"DCF\s+(?:ANALYSIS|VALUATION)",
                r"(?:COMPARABLE|COMPS)\s+ANALYSIS",
                r"(?:TARGET|FAIR)\s+VALUE",
            ],
            "weight": 0.8,
            "required_sections": [],
            "ontology_class": str(DocumentClass.EQUITY_RESEARCH.value),
        },
        DocumentType.EARNINGS_CALL: {
            "patterns": [
                r"EARNINGS\s+(?:CALL|CONFERENCE)",
                r"(?:Q[1-4]|FOURTH|FIRST|SECOND|THIRD)\s+(?:QUARTER|FISCAL)\s+\d{4}\s+(?:EARNINGS|RESULTS)",
                r"OPERATOR:.*(?:WELCOME|THANK\s+YOU\s+FOR\s+STANDING\s+BY)",
                r"QUESTION-?AND-?ANSWER\s+SESSION",
                r"(?:PREPARED\s+REMARKS|OPENING\s+REMARKS)",
            ],
            "weight": 0.8,
            "required_sections": [],
            "ontology_class": str(DocumentClass.EARNINGS_CALL.value),
        },
        DocumentType.PRESS_RELEASE: {
            "patterns": [
                r"PRESS\s+RELEASE",
                r"FOR\s+IMMEDIATE\s+RELEASE",
                r"(?:REPORTS|ANNOUNCES)\s+(?:Q[1-4]|QUARTERLY|ANNUAL)\s+(?:RESULTS|EARNINGS)",
                r"CONTACT:.*(?:INVESTOR\s+RELATIONS|MEDIA\s+RELATIONS)",
            ],
            "weight": 0.7,
            "required_sections": [],
            "ontology_class": str(DocumentClass.PRESS_RELEASE.value),
        },
        DocumentType.ECONOMIC_DATA: {
            "patterns": [
                r"FRED\s+(?:ECONOMIC|DATA)\s+SERIES",
                r"(?:GDP|UNEMPLOYMENT|INFLATION|CPI|INTEREST\s+RATE)\s+(?:DATA|SERIES)",
                r"FEDERAL\s+RESERVE",
                r"MACROECONOMIC\s+(?:DATA|INDICATOR)",
            ],
            "weight": 0.9,
            "required_sections": [],
            "ontology_class": str(SEI_DOC["Document"]),
        },
    }
    
    # Section detection patterns for 10-K/10-Q
    SECTION_PATTERNS = {
        "item_1": [
            r"ITEM\s*1[\.\s]*[-–—]?\s*BUSINESS",
            r"PART\s*I.*ITEM\s*1\b",
        ],
        "item_1a": [
            r"ITEM\s*1A[\.\s]*[-–—]?\s*RISK\s*FACTORS",
        ],
        "item_1b": [
            r"ITEM\s*1B[\.\s]*[-–—]?\s*UNRESOLVED\s*STAFF\s*COMMENTS",
        ],
        "item_2": [
            r"ITEM\s*2[\.\s]*[-–—]?\s*(?:PROPERTIES|MANAGEMENT['\u2019]?S\s*DISCUSSION)",
        ],
        "item_3": [
            r"ITEM\s*3[\.\s]*[-–—]?\s*LEGAL\s*PROCEEDINGS",
        ],
        "item_4": [
            r"ITEM\s*4[\.\s]*[-–—]?\s*MINE\s*SAFETY",
        ],
        "item_5": [
            r"ITEM\s*5[\.\s]*[-–—]?\s*MARKET\s*FOR",
        ],
        "item_6": [
            r"ITEM\s*6[\.\s]*[-–—]?\s*(?:RESERVED|SELECTED\s*FINANCIAL)",
        ],
        "item_7": [
            r"ITEM\s*7[\.\s]*[-–—]?\s*MANAGEMENT['\u2019]?S\s*DISCUSSION",
        ],
        "item_7a": [
            r"ITEM\s*7A[\.\s]*[-–—]?\s*QUANTITATIVE\s*AND\s*QUALITATIVE",
        ],
        "item_8": [
            r"ITEM\s*8[\.\s]*[-–—]?\s*FINANCIAL\s*STATEMENTS",
        ],
        "item_9": [
            r"ITEM\s*9[\.\s]*[-–—]?\s*CHANGES\s*IN\s*AND\s*DISAGREEMENTS",
        ],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the document classifier.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.5)
        self._compile_patterns()
        logger.info("DocumentClassifier initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance"""
        self._compiled_patterns: Dict[DocumentType, List[re.Pattern]] = {}
        
        for doc_type, config in self.CLASSIFICATION_PATTERNS.items():
            self._compiled_patterns[doc_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in config["patterns"]
            ]
        
        self._compiled_section_patterns: Dict[str, List[re.Pattern]] = {}
        for section, patterns in self.SECTION_PATTERNS.items():
            self._compiled_section_patterns[section] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
    
    def classify(self, content: str, metadata: Optional[Dict] = None) -> ClassificationResult:
        """
        Classify a document based on its content.
        
        Args:
            content: Document text content
            metadata: Optional metadata (e.g., from source)
            
        Returns:
            ClassificationResult with type, confidence, and details
        """
        metadata = metadata or {}
        
        # Check if document type is already known from metadata
        if metadata.get("document_type"):
            known_type = self._map_known_type(metadata["document_type"])
            if known_type != DocumentType.UNKNOWN:
                return ClassificationResult(
                    document_type=known_type,
                    ontology_class=self.CLASSIFICATION_PATTERNS.get(
                        known_type, {}
                    ).get("ontology_class", str(SEI_DOC["Document"])),
                    confidence=1.0,
                    matched_patterns=["metadata_provided"],
                    sections_detected=self._detect_sections(content),
                    metadata={"source": "metadata"},
                )
        
        # Perform pattern-based classification
        scores: Dict[DocumentType, Tuple[float, List[str]]] = {}
        content_upper = content[:50000].upper()  # Limit content for efficiency
        
        for doc_type, patterns in self._compiled_patterns.items():
            matched = []
            for pattern in patterns:
                if pattern.search(content_upper):
                    matched.append(pattern.pattern)
            
            if matched:
                weight = self.CLASSIFICATION_PATTERNS[doc_type]["weight"]
                score = (len(matched) / len(patterns)) * weight
                scores[doc_type] = (score, matched)
        
        # Detect sections (boosts confidence for SEC filings)
        sections_detected = self._detect_sections(content)
        
        # Boost score for documents with expected sections
        for doc_type in [DocumentType.FORM_10K, DocumentType.FORM_10Q]:
            if doc_type in scores:
                required = set(self.CLASSIFICATION_PATTERNS[doc_type]["required_sections"])
                detected = set(sections_detected)
                overlap = len(required & detected) / max(len(required), 1)
                scores[doc_type] = (
                    scores[doc_type][0] + (overlap * 0.3),
                    scores[doc_type][1]
                )
        
        # Select best classification
        if scores:
            best_type = max(scores, key=lambda x: scores[x][0])
            confidence = min(scores[best_type][0], 1.0)
            matched_patterns = scores[best_type][1]
        else:
            best_type = DocumentType.UNKNOWN
            confidence = 0.0
            matched_patterns = []
        
        # Get ontology class
        ontology_class = self.CLASSIFICATION_PATTERNS.get(
            best_type, {}
        ).get("ontology_class", str(SEI_DOC["Document"]))
        
        return ClassificationResult(
            document_type=best_type,
            ontology_class=ontology_class,
            confidence=confidence,
            matched_patterns=matched_patterns,
            sections_detected=sections_detected,
            metadata={
                "all_scores": {
                    k.value: v[0] for k, v in scores.items()
                }
            },
        )
    
    def _detect_sections(self, content: str) -> List[str]:
        """Detect sections in the document"""
        sections = []
        content_sample = content[:100000]  # Check first 100k chars
        
        for section, patterns in self._compiled_section_patterns.items():
            for pattern in patterns:
                if pattern.search(content_sample):
                    sections.append(section)
                    break
        
        return sections
    
    def _map_known_type(self, type_str: str) -> DocumentType:
        """Map a string document type to DocumentType enum"""
        type_mapping = {
            "10-K": DocumentType.FORM_10K,
            "10-Q": DocumentType.FORM_10Q,
            "8-K": DocumentType.FORM_8K,
            "DEF14A": DocumentType.PROXY_STATEMENT,
            "economic_data": DocumentType.ECONOMIC_DATA,
        }
        return type_mapping.get(type_str, DocumentType.UNKNOWN)
    
    def classify_batch(
        self, 
        documents: List[Tuple[str, Optional[Dict]]]
    ) -> List[ClassificationResult]:
        """
        Classify multiple documents.
        
        Args:
            documents: List of (content, metadata) tuples
            
        Returns:
            List of ClassificationResult objects
        """
        results = []
        for content, metadata in documents:
            result = self.classify(content, metadata)
            results.append(result)
        return results
    
    def get_document_type_info(self, doc_type: DocumentType) -> Dict[str, Any]:
        """Get information about a document type"""
        config = self.CLASSIFICATION_PATTERNS.get(doc_type, {})
        return {
            "type": doc_type.value,
            "ontology_class": config.get("ontology_class", ""),
            "pattern_count": len(config.get("patterns", [])),
            "required_sections": config.get("required_sections", []),
        }
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported document types"""
        return [dt.value for dt in DocumentType if dt != DocumentType.UNKNOWN]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_document_date(content: str) -> Optional[str]:
    """
    Extract document date from content.
    
    Args:
        content: Document text
        
    Returns:
        Date string if found, None otherwise
    """
    date_patterns = [
        r"(?:For\s+the\s+(?:fiscal\s+)?year\s+ended|Period\s+ended)\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(?:Filed|Filing\s+Date)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(?:Date\s+of\s+Report)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})",
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, content[:5000], re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_company_info(content: str) -> Dict[str, Optional[str]]:
    """
    Extract company information from document.
    
    Args:
        content: Document text
        
    Returns:
        Dictionary with company name, ticker, CIK
    """
    info = {
        "company_name": None,
        "ticker": None,
        "cik": None,
    }
    
    # Company name (usually in header)
    name_match = re.search(
        r"(?:REGISTRANT|COMPANY|ISSUER)[:\s]+([A-Z][A-Za-z\s,\.]+(?:INC\.|CORP\.|LLC|LTD\.))",
        content[:5000],
        re.IGNORECASE
    )
    if name_match:
        info["company_name"] = name_match.group(1).strip()
    
    # Ticker symbol
    ticker_match = re.search(
        r"(?:TICKER|TRADING)\s*(?:SYMBOL)?[:\s]+([A-Z]{1,5})\b",
        content[:5000],
        re.IGNORECASE
    )
    if ticker_match:
        info["ticker"] = ticker_match.group(1)
    
    # CIK number
    cik_match = re.search(
        r"(?:CIK|COMMISSION\s+FILE\s+NUMBER)[:\s#]+(\d{10}|\d+-\d+-\d+)",
        content[:5000],
        re.IGNORECASE
    )
    if cik_match:
        info["cik"] = cik_match.group(1).replace("-", "")
    
    return info

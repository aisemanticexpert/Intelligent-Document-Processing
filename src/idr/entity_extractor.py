"""
IDR Entity Extractor Module
============================

Extracts named entities from financial documents using pattern matching,
NLP models, and ontology-guided recognition.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import optional NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Using pattern-based extraction only.")


@dataclass
class ExtractedEntity:
    """Represents an extracted entity"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    ontology_class: Optional[str] = None
    normalized_text: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    source: str = "pattern"  # pattern, spacy, transformer
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "ontology_class": self.ontology_class,
            "normalized_text": self.normalized_text,
            "properties": self.properties,
            "source": self.source,
        }
    
    def __hash__(self):
        return hash((self.text.lower(), self.entity_type, self.start))
    
    def __eq__(self, other):
        if not isinstance(other, ExtractedEntity):
            return False
        return (
            self.text.lower() == other.text.lower() and
            self.entity_type == other.entity_type and
            abs(self.start - other.start) < 10
        )


class EntityExtractor:
    """
    Intelligent Document Recognition (IDR) - Entity Extractor
    
    Extracts entities using:
    1. Pattern-based extraction (regex)
    2. SpaCy NER (if available)
    3. Ontology-guided entity recognition
    
    Supports financial entities:
    - Companies, People, Products
    - Financial Metrics (Revenue, Net Income, etc.)
    - Risks (Supply Chain, Regulatory, etc.)
    - Dates, Amounts, Percentages
    """
    
    # Entity patterns organized by type
    ENTITY_PATTERNS = {
        # Company patterns
        "Company": [
            (r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(?:Inc\.|Corp\.|Corporation|Company|Co\.|Ltd\.|LLC|L\.P\.|LP|PLC)\b", 0.9),
            (r"\b(Apple|Google|Alphabet|Microsoft|Amazon|Meta|Tesla|NVIDIA|AMD|Intel|IBM|Oracle|Cisco|Salesforce|Adobe)\b", 0.95),
            (r"\b(JPMorgan|Goldman\s+Sachs|Morgan\s+Stanley|Bank\s+of\s+America|Citigroup|Wells\s+Fargo)\b", 0.95),
            (r"\b(Johnson\s*&\s*Johnson|Pfizer|Merck|AbbVie|Bristol[- ]Myers|Eli\s+Lilly)\b", 0.95),
            (r"\b(Walmart|Target|Costco|Home\s+Depot|Coca[- ]Cola|PepsiCo|Procter\s*&\s*Gamble)\b", 0.95),
            (r"\b(ExxonMobil|Chevron|ConocoPhillips|Shell|BP)\b", 0.95),
        ],
        
        # Person patterns (executives)
        "Person": [
            (r"\b(?:CEO|CFO|CTO|COO|Chairman|President|Director)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", 0.85),
            (r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:CEO|CFO|CTO|COO|Chairman|President|Director)\b", 0.85),
            (r"\b(Tim\s+Cook|Satya\s+Nadella|Sundar\s+Pichai|Andy\s+Jassy|Mark\s+Zuckerberg|Elon\s+Musk|Jamie\s+Dimon)\b", 0.95),
        ],
        
        # Product patterns
        "Product": [
            (r"\b(iPhone|iPad|Mac|MacBook|Apple\s+Watch|AirPods|Vision\s+Pro|App\s+Store|iCloud)\b", 0.9),
            (r"\b(Windows|Azure|Office\s+365|Microsoft\s+365|Xbox|Surface|LinkedIn|GitHub)\b", 0.9),
            (r"\b(Android|Chrome|Gmail|YouTube|Google\s+Cloud|Google\s+Search|Pixel)\b", 0.9),
            (r"\b(AWS|Amazon\s+Web\s+Services|Prime|Alexa|Kindle|Echo)\b", 0.9),
        ],
        
        # Revenue/Sales patterns
        "Revenue": [
            (r"(?:total\s+)?(?:net\s+)?(?:revenue|sales)\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M|thousand|K)?", 0.9),
            (r"\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?(?:total\s+)?(?:net\s+)?(?:revenue|sales)", 0.9),
            (r"(?:revenue|sales)\s+(?:increased|decreased|grew|declined)\s+(?:by\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?", 0.85),
        ],
        
        # Net Income patterns
        "NetIncome": [
            (r"(?:net\s+)?(?:income|earnings|profit)\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?", 0.9),
            (r"\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?(?:net\s+)?(?:income|earnings|profit)", 0.9),
        ],
        
        # EPS patterns
        "EarningsPerShare": [
            (r"(?:EPS|earnings\s+per\s+share)\s+(?:of\s+)?\$?([\d]+(?:\.\d+)?)", 0.9),
            (r"\$?([\d]+\.\d+)\s+(?:per\s+)?(?:diluted\s+)?(?:share|EPS)", 0.85),
        ],
        
        # Total Assets patterns
        "TotalAssets": [
            (r"total\s+assets\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?", 0.9),
            (r"\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?total\s+assets", 0.9),
        ],
        
        # Cash Flow patterns
        "CashFlow": [
            (r"(?:operating\s+)?cash\s+flow\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?", 0.85),
            (r"free\s+cash\s+flow\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?", 0.85),
        ],
        
        # Risk patterns
        "SupplyChainRisk": [
            (r"supply\s+chain\s+(?:risk|disruption|challenge|issue|concentration)", 0.85),
            (r"(?:manufacturing|production|logistics|distribution)\s+(?:risk|disruption|challenge)", 0.8),
            (r"(?:supplier|vendor)\s+(?:concentration|dependency|risk|disruption)", 0.8),
            (r"(?:single|sole|limited)\s+source\s+(?:supplier|manufacturing)", 0.85),
        ],
        
        "CurrencyRisk": [
            (r"(?:foreign\s+)?(?:currency|exchange\s+rate|fx)\s+(?:risk|exposure|fluctuation|volatility)", 0.85),
            (r"(?:foreign\s+exchange|currency)\s+(?:hedging|exposure|translation)", 0.8),
        ],
        
        "RegulatoryRisk": [
            (r"regulatory\s+(?:risk|compliance|change|uncertainty|environment|requirement)", 0.85),
            (r"(?:government|legal|legislative)\s+(?:risk|action|change|regulation)", 0.8),
            (r"(?:antitrust|data\s+privacy|environmental)\s+(?:regulation|compliance|law)", 0.85),
        ],
        
        "GeopoliticalRisk": [
            (r"geopolitical\s+(?:risk|tension|uncertainty|event|instability)", 0.85),
            (r"(?:trade\s+war|tariff|sanction|embargo|trade\s+restriction)", 0.85),
            (r"(?:political|economic)\s+(?:instability|uncertainty)\s+(?:in|of)\s+(?:\w+\s+)?(?:region|country|market)", 0.8),
        ],
        
        "CompetitiveRisk": [
            (r"competit(?:ive|ion)\s+(?:risk|pressure|threat|landscape|environment)", 0.85),
            (r"(?:intense|increasing|significant)\s+competition", 0.8),
            (r"market\s+(?:share|position)\s+(?:loss|decline|pressure)", 0.8),
        ],
        
        "CybersecurityRisk": [
            (r"(?:cyber(?:security)?|information\s+security|data\s+security)\s+(?:risk|threat|breach|incident)", 0.85),
            (r"(?:data|security)\s+breach", 0.85),
            (r"(?:ransomware|malware|phishing|hacking)\s+(?:attack|threat|risk)", 0.85),
        ],
        
        "TechnologyRisk": [
            (r"technolog(?:y|ical)\s+(?:risk|change|disruption|obsolescence)", 0.85),
            (r"(?:digital|technology)\s+transformation\s+(?:risk|challenge)", 0.8),
            (r"(?:rapid|accelerating)\s+technological\s+change", 0.8),
        ],
        
        # Date patterns
        "Date": [
            (r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b", 0.95),
            (r"\b(\d{1,2}/\d{1,2}/\d{4})\b", 0.9),
            (r"\b(Q[1-4]\s*\d{4}|FY\s*\d{4}|\d{4}\s*Q[1-4])\b", 0.9),
            (r"\b(?:fiscal\s+)?(?:year|quarter)\s+(?:ended|ending)\s+(\w+\s+\d{1,2},?\s+\d{4})", 0.9),
        ],
        
        # Percentage patterns
        "Percentage": [
            (r"(\d+(?:\.\d+)?)\s*%", 0.9),
            (r"(\d+(?:\.\d+)?)\s+percent", 0.85),
        ],
        
        # Monetary Amount patterns
        "MonetaryAmount": [
            (r"\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|B|M|K)?", 0.9),
            (r"([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|B|M|K)?\s*(?:dollars|USD)", 0.85),
        ],
    }
    
    # Ontology class mapping
    ONTOLOGY_MAPPING = {
        "Company": "http://www.semanticdataservices.com/ontology/company#PublicCompany",
        "Person": "http://www.semanticdataservices.com/ontology/company#Person",
        "Product": "http://www.semanticdataservices.com/ontology/company#Product",
        "Revenue": "http://www.semanticdataservices.com/ontology/financial#Revenue",
        "NetIncome": "http://www.semanticdataservices.com/ontology/financial#NetIncome",
        "EarningsPerShare": "http://www.semanticdataservices.com/ontology/financial#EarningsPerShare",
        "TotalAssets": "http://www.semanticdataservices.com/ontology/financial#TotalAssets",
        "CashFlow": "http://www.semanticdataservices.com/ontology/financial#CashFlow",
        "SupplyChainRisk": "http://www.semanticdataservices.com/ontology/risk#SupplyChainRisk",
        "CurrencyRisk": "http://www.semanticdataservices.com/ontology/risk#CurrencyRisk",
        "RegulatoryRisk": "http://www.semanticdataservices.com/ontology/risk#RegulatoryRisk",
        "GeopoliticalRisk": "http://www.semanticdataservices.com/ontology/risk#GeopoliticalRisk",
        "CompetitiveRisk": "http://www.semanticdataservices.com/ontology/risk#CompetitiveRisk",
        "CybersecurityRisk": "http://www.semanticdataservices.com/ontology/risk#CybersecurityRisk",
        "TechnologyRisk": "http://www.semanticdataservices.com/ontology/risk#TechnologyRisk",
        "Date": "http://www.w3.org/2001/XMLSchema#date",
        "Percentage": "http://www.w3.org/2001/XMLSchema#decimal",
        "MonetaryAmount": "http://www.semanticdataservices.com/ontology/financial#MonetaryAmount",
    }
    
    # Entity normalization
    COMPANY_ALIASES = {
        "alphabet": "Alphabet Inc.",
        "google": "Alphabet Inc.",
        "apple": "Apple Inc.",
        "microsoft": "Microsoft Corporation",
        "amazon": "Amazon.com Inc.",
        "meta": "Meta Platforms Inc.",
        "facebook": "Meta Platforms Inc.",
        "tesla": "Tesla Inc.",
        "nvidia": "NVIDIA Corporation",
        "jpmorgan": "JPMorgan Chase & Co.",
        "jp morgan": "JPMorgan Chase & Co.",
        "goldman sachs": "The Goldman Sachs Group, Inc.",
        "johnson & johnson": "Johnson & Johnson",
        "j&j": "Johnson & Johnson",
        "coca-cola": "The Coca-Cola Company",
        "coke": "The Coca-Cola Company",
        "exxonmobil": "Exxon Mobil Corporation",
        "exxon mobil": "Exxon Mobil Corporation",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the entity extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.use_spacy = self.config.get("use_spacy", True) and SPACY_AVAILABLE
        
        self._compile_patterns()
        self._load_spacy_model()
        
        logger.info(f"EntityExtractor initialized (spaCy: {self.use_spacy})")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns"""
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            self._compiled_patterns[entity_type] = [
                (re.compile(pattern, re.IGNORECASE), confidence)
                for pattern, confidence in patterns
            ]
    
    def _load_spacy_model(self) -> None:
        """Load spaCy model if available"""
        self._nlp = None
        if self.use_spacy:
            try:
                model_name = self.config.get("spacy_model", "en_core_web_sm")
                self._nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}")
                self.use_spacy = False
    
    def extract(self, text: str, entity_types: Optional[List[str]] = None) -> List[ExtractedEntity]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            entity_types: Optional list of entity types to extract
            
        Returns:
            List of ExtractedEntity objects
        """
        entities: List[ExtractedEntity] = []
        
        # Pattern-based extraction
        pattern_entities = self._extract_with_patterns(text, entity_types)
        entities.extend(pattern_entities)
        
        # SpaCy-based extraction
        if self.use_spacy and self._nlp:
            spacy_entities = self._extract_with_spacy(text)
            entities.extend(spacy_entities)
        
        # Deduplicate and merge
        entities = self._deduplicate_entities(entities)
        
        # Filter by confidence
        entities = [e for e in entities if e.confidence >= self.confidence_threshold]
        
        # Sort by position
        entities.sort(key=lambda x: x.start)
        
        return entities
    
    def _extract_with_patterns(
        self, 
        text: str, 
        entity_types: Optional[List[str]] = None
    ) -> List[ExtractedEntity]:
        """Extract entities using regex patterns"""
        entities = []
        types_to_extract = entity_types or list(self._compiled_patterns.keys())
        
        for entity_type in types_to_extract:
            if entity_type not in self._compiled_patterns:
                continue
            
            for pattern, confidence in self._compiled_patterns[entity_type]:
                for match in pattern.finditer(text):
                    # Get the matched text (full match or first group)
                    entity_text = match.group(1) if match.lastindex else match.group(0)
                    entity_text = entity_text.strip()
                    
                    if not entity_text or len(entity_text) < 2:
                        continue
                    
                    # Extract properties for financial metrics
                    properties = self._extract_entity_properties(
                        entity_type, entity_text, match
                    )
                    
                    # Normalize text
                    normalized = self._normalize_entity(entity_type, entity_text)
                    
                    entity = ExtractedEntity(
                        text=entity_text,
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                        ontology_class=self.ONTOLOGY_MAPPING.get(entity_type),
                        normalized_text=normalized,
                        properties=properties,
                        source="pattern",
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_with_spacy(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using spaCy NER"""
        entities = []
        
        # Process text (limit length for performance)
        doc = self._nlp(text[:100000])
        
        # Map spaCy entity types to our types
        type_mapping = {
            "ORG": "Company",
            "PERSON": "Person",
            "DATE": "Date",
            "MONEY": "MonetaryAmount",
            "PERCENT": "Percentage",
            "PRODUCT": "Product",
            "GPE": "Location",
        }
        
        for ent in doc.ents:
            entity_type = type_mapping.get(ent.label_)
            if not entity_type:
                continue
            
            # Skip short entities
            if len(ent.text.strip()) < 2:
                continue
            
            entity = ExtractedEntity(
                text=ent.text,
                entity_type=entity_type,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.8,  # Base confidence for spaCy
                ontology_class=self.ONTOLOGY_MAPPING.get(entity_type),
                normalized_text=self._normalize_entity(entity_type, ent.text),
                source="spacy",
            )
            entities.append(entity)
        
        return entities
    
    def _extract_entity_properties(
        self, 
        entity_type: str, 
        text: str, 
        match: re.Match
    ) -> Dict[str, Any]:
        """Extract additional properties from entity match"""
        properties = {}
        
        # For financial metrics, extract numeric values
        if entity_type in ["Revenue", "NetIncome", "TotalAssets", "CashFlow", "MonetaryAmount"]:
            # Parse numeric value
            value_str = text.replace(",", "").replace("$", "")
            try:
                value = float(re.search(r"[\d.]+", value_str).group())
                
                # Apply multiplier
                full_match = match.group(0).lower()
                if "billion" in full_match or full_match.endswith("b"):
                    value *= 1_000_000_000
                elif "million" in full_match or full_match.endswith("m"):
                    value *= 1_000_000
                elif "thousand" in full_match or full_match.endswith("k"):
                    value *= 1_000
                
                properties["value"] = value
                properties["currency"] = "USD"
            except (ValueError, AttributeError):
                pass
        
        elif entity_type == "EarningsPerShare":
            try:
                value = float(re.search(r"[\d.]+", text).group())
                properties["value"] = value
                properties["currency"] = "USD"
            except (ValueError, AttributeError):
                pass
        
        elif entity_type == "Percentage":
            try:
                value = float(re.search(r"[\d.]+", text).group())
                properties["value"] = value
            except (ValueError, AttributeError):
                pass
        
        return properties
    
    def _normalize_entity(self, entity_type: str, text: str) -> str:
        """Normalize entity text"""
        if entity_type == "Company":
            text_lower = text.lower().strip()
            return self.COMPANY_ALIASES.get(text_lower, text)
        return text.strip()
    
    def _deduplicate_entities(
        self, 
        entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping highest confidence"""
        unique: Dict[Tuple[str, str], ExtractedEntity] = {}
        
        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            
            if key not in unique:
                unique[key] = entity
            else:
                # Keep higher confidence or pattern-based (more specific)
                existing = unique[key]
                if entity.confidence > existing.confidence:
                    unique[key] = entity
                elif entity.source == "pattern" and existing.source != "pattern":
                    unique[key] = entity
        
        return list(unique.values())
    
    def extract_from_section(
        self, 
        text: str, 
        section_name: str
    ) -> List[ExtractedEntity]:
        """
        Extract entities from a specific document section with
        context-aware entity types.
        
        Args:
            text: Section text
            section_name: Name of the section (e.g., "item_1a")
            
        Returns:
            List of entities with section context
        """
        # Define section-specific entity types
        section_entity_types = {
            "item_1": ["Company", "Product", "Person", "Date"],
            "item_1a": [
                "Company", "SupplyChainRisk", "CurrencyRisk", "RegulatoryRisk",
                "GeopoliticalRisk", "CompetitiveRisk", "CybersecurityRisk",
                "TechnologyRisk", "Percentage"
            ],
            "item_7": [
                "Company", "Revenue", "NetIncome", "EarningsPerShare",
                "MonetaryAmount", "Percentage", "Date"
            ],
            "item_8": [
                "Revenue", "NetIncome", "TotalAssets", "CashFlow",
                "MonetaryAmount", "Date"
            ],
        }
        
        entity_types = section_entity_types.get(section_name)
        entities = self.extract(text, entity_types)
        
        # Add section context to entities
        for entity in entities:
            entity.properties["source_section"] = section_name
        
        return entities
    
    def get_entity_statistics(
        self, 
        entities: List[ExtractedEntity]
    ) -> Dict[str, Any]:
        """
        Get statistics about extracted entities.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_entities": len(entities),
            "by_type": defaultdict(int),
            "by_source": defaultdict(int),
            "avg_confidence": 0.0,
            "unique_texts": set(),
        }
        
        for entity in entities:
            stats["by_type"][entity.entity_type] += 1
            stats["by_source"][entity.source] += 1
            stats["unique_texts"].add(entity.text.lower())
        
        if entities:
            stats["avg_confidence"] = sum(e.confidence for e in entities) / len(entities)
        
        stats["unique_texts"] = len(stats["unique_texts"])
        stats["by_type"] = dict(stats["by_type"])
        stats["by_source"] = dict(stats["by_source"])
        
        return stats

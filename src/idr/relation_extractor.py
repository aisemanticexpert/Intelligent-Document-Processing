"""
IDR Relation Extractor Module
==============================

Extracts relationships between entities using dependency parsing,
pattern matching, and ontology-guided rules.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .entity_extractor import ExtractedEntity

logger = logging.getLogger(__name__)


@dataclass
class ExtractedRelation:
    """Represents an extracted relation (triple)"""
    subject: ExtractedEntity
    predicate: str
    object: ExtractedEntity
    confidence: float
    ontology_property: Optional[str] = None
    source_text: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject.to_dict(),
            "predicate": self.predicate,
            "object": self.object.to_dict(),
            "confidence": self.confidence,
            "ontology_property": self.ontology_property,
            "source_text": self.source_text[:200] if self.source_text else "",
            "properties": self.properties,
        }
    
    def to_triple_string(self) -> str:
        """Return triple as string"""
        return f"({self.subject.text}) --[{self.predicate}]--> ({self.object.text})"


class RelationExtractor:
    """
    Intelligent Document Recognition (IDR) - Relation Extractor
    
    Extracts relations between entities using:
    1. Pattern-based extraction (verb phrases)
    2. Co-occurrence analysis
    3. Ontology-guided relation constraints
    
    Generates Subject-Predicate-Object triples for knowledge graph.
    """
    
    # Relation patterns: (pattern, relation_type, subject_type, object_type, confidence)
    RELATION_PATTERNS = {
        # Company relationships
        "COMPETES_WITH": [
            (r"(\w+)\s+(?:competes?|competing)\s+(?:with|against)\s+(\w+)", "Company", "Company", 0.85),
            (r"(\w+)\s+(?:is\s+)?(?:a\s+)?(?:major\s+)?competitor\s+(?:of|to)\s+(\w+)", "Company", "Company", 0.85),
            (r"competition\s+(?:from|with)\s+(\w+)", "Company", "Company", 0.8),
        ],
        "PARTNERS_WITH": [
            (r"(\w+)\s+(?:partners?|partnering|partnered)\s+with\s+(\w+)", "Company", "Company", 0.85),
            (r"partnership\s+(?:with|between)\s+(\w+)\s+and\s+(\w+)", "Company", "Company", 0.85),
            (r"(\w+)\s+(?:and|&)\s+(\w+)\s+(?:announced|formed)\s+(?:a\s+)?partnership", "Company", "Company", 0.8),
        ],
        "ACQUIRED": [
            (r"(\w+)\s+(?:acquired|acquires|acquiring|bought|purchased)\s+(\w+)", "Company", "Company", 0.9),
            (r"acquisition\s+of\s+(\w+)\s+by\s+(\w+)", "Company", "Company", 0.9),
            (r"(\w+)\s+(?:was|is\s+being)\s+acquired\s+by\s+(\w+)", "Company", "Company", 0.9),
        ],
        "SUBSIDIARY_OF": [
            (r"(\w+),?\s+(?:a\s+)?(?:wholly[- ]owned\s+)?subsidiary\s+of\s+(\w+)", "Company", "Company", 0.9),
            (r"(\w+)\s+(?:owns?|owned)\s+(\w+)", "Company", "Company", 0.8),
        ],
        
        # Company to Financial Metric
        "REPORTED": [
            (r"(\w+)\s+reported\s+(?:.*?)(\$[\d,\.]+\s*(?:billion|million|B|M)?)", "Company", "FinancialMetric", 0.85),
            (r"(\w+)['']?s?\s+(?:revenue|sales|income|earnings)\s+(?:was|were|of)\s+(\$[\d,\.]+)", "Company", "FinancialMetric", 0.85),
        ],
        "GENERATED": [
            (r"(\w+)\s+generated\s+(\$[\d,\.]+\s*(?:billion|million)?)\s+(?:in\s+)?(?:revenue|sales)", "Company", "Revenue", 0.85),
        ],
        
        # Company to Risk
        "FACES_RISK": [
            (r"(\w+)\s+(?:faces?|facing|confronts?)\s+(?:.*?)((?:supply\s+chain|regulatory|currency|competitive|cybersecurity|geopolitical)\s+risk)", "Company", "Risk", 0.85),
            (r"(\w+)\s+(?:is\s+)?(?:exposed|vulnerable|susceptible)\s+to\s+(.*?risk)", "Company", "Risk", 0.8),
            (r"(risk|threat|challenge)\s+(?:to|for)\s+(\w+)", "Risk", "Company", 0.75),
        ],
        
        # Company to Product
        "MANUFACTURES": [
            (r"(\w+)\s+(?:manufactures?|produces?|makes?|builds?)\s+(?:the\s+)?(\w+)", "Company", "Product", 0.8),
        ],
        "SELLS": [
            (r"(\w+)\s+(?:sells?|markets?|offers?|provides?)\s+(?:the\s+)?(\w+)", "Company", "Product", 0.8),
        ],
        
        # Person to Company
        "CEO_OF": [
            (r"(\w+\s+\w+),?\s+(?:the\s+)?CEO\s+of\s+(\w+)", "Person", "Company", 0.9),
            (r"(\w+)\s+CEO\s+(\w+\s+\w+)", "Company", "Person", 0.9),
        ],
        "WORKS_AT": [
            (r"(\w+\s+\w+),?\s+(?:.*?)\s+(?:at|of)\s+(\w+)", "Person", "Company", 0.7),
        ],
        
        # Economic indicators
        "IMPACTED_BY": [
            (r"(\w+)\s+(?:is\s+)?(?:impacted|affected|influenced)\s+by\s+(.*?(?:rate|inflation|GDP|unemployment))", "Company", "EconomicIndicator", 0.8),
        ],
    }
    
    # Ontology property mapping
    ONTOLOGY_PROPERTIES = {
        "COMPETES_WITH": "http://www.semanticexpert.ai/ontology/company#competesWith",
        "PARTNERS_WITH": "http://www.semanticexpert.ai/ontology/company#partnersWith",
        "ACQUIRED": "http://www.semanticexpert.ai/ontology/company#acquired",
        "SUBSIDIARY_OF": "http://www.semanticexpert.ai/ontology/company#isSubsidiaryOf",
        "REPORTED": "http://www.semanticexpert.ai/ontology/financial#reportedIn",
        "GENERATED": "http://www.semanticexpert.ai/ontology/financial#hasFinancialMetric",
        "FACES_RISK": "http://www.semanticexpert.ai/ontology/risk#facesRisk",
        "MANUFACTURES": "http://www.semanticexpert.ai/ontology/company#manufactures",
        "SELLS": "http://www.semanticexpert.ai/ontology/company#sells",
        "CEO_OF": "http://www.semanticexpert.ai/ontology/company#isCEOOf",
        "WORKS_AT": "http://www.semanticexpert.ai/ontology/company#worksAt",
        "IMPACTED_BY": "http://www.semanticexpert.ai/ontology/economic#impactedBy",
    }
    
    # Valid entity type pairs for each relation
    VALID_TYPE_PAIRS = {
        "COMPETES_WITH": [("Company", "Company")],
        "PARTNERS_WITH": [("Company", "Company")],
        "ACQUIRED": [("Company", "Company")],
        "SUBSIDIARY_OF": [("Company", "Company")],
        "REPORTED": [("Company", "Revenue"), ("Company", "NetIncome"), ("Company", "MonetaryAmount")],
        "GENERATED": [("Company", "Revenue"), ("Company", "MonetaryAmount")],
        "FACES_RISK": [
            ("Company", "SupplyChainRisk"), ("Company", "CurrencyRisk"),
            ("Company", "RegulatoryRisk"), ("Company", "GeopoliticalRisk"),
            ("Company", "CompetitiveRisk"), ("Company", "CybersecurityRisk"),
            ("Company", "TechnologyRisk"),
        ],
        "MANUFACTURES": [("Company", "Product")],
        "SELLS": [("Company", "Product")],
        "CEO_OF": [("Person", "Company")],
        "WORKS_AT": [("Person", "Company")],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the relation extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_sentence_length = self.config.get("max_sentence_length", 500)
        
        self._compile_patterns()
        logger.info("RelationExtractor initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns"""
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern, str, str, float]]] = {}
        
        for relation_type, patterns in self.RELATION_PATTERNS.items():
            self._compiled_patterns[relation_type] = [
                (re.compile(pattern, re.IGNORECASE), subj_type, obj_type, conf)
                for pattern, subj_type, obj_type, conf in patterns
            ]
    
    def extract(
        self, 
        text: str, 
        entities: List[ExtractedEntity]
    ) -> List[ExtractedRelation]:
        """
        Extract relations between entities.
        
        Args:
            text: Source text
            entities: List of extracted entities
            
        Returns:
            List of ExtractedRelation objects
        """
        relations = []
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Build entity lookup by position
        entity_by_text = self._build_entity_lookup(entities)
        
        for sentence in sentences:
            # Find entities in this sentence
            sentence_entities = self._find_entities_in_text(sentence, entities)
            
            if len(sentence_entities) < 2:
                continue
            
            # Extract pattern-based relations
            pattern_relations = self._extract_pattern_relations(
                sentence, sentence_entities, entity_by_text
            )
            relations.extend(pattern_relations)
            
            # Extract co-occurrence relations
            cooccurrence_relations = self._extract_cooccurrence_relations(
                sentence, sentence_entities
            )
            relations.extend(cooccurrence_relations)
        
        # Deduplicate
        relations = self._deduplicate_relations(relations)
        
        # Filter by confidence
        relations = [r for r in relations if r.confidence >= self.confidence_threshold]
        
        return relations
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter and limit length
        filtered = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and len(sent) < self.max_sentence_length:
                filtered.append(sent)
        
        return filtered
    
    def _build_entity_lookup(
        self, 
        entities: List[ExtractedEntity]
    ) -> Dict[str, ExtractedEntity]:
        """Build lookup dictionary for entities by text"""
        lookup = {}
        for entity in entities:
            lookup[entity.text.lower()] = entity
            if entity.normalized_text:
                lookup[entity.normalized_text.lower()] = entity
        return lookup
    
    def _find_entities_in_text(
        self, 
        text: str, 
        entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Find which entities appear in the text"""
        text_lower = text.lower()
        found = []
        
        for entity in entities:
            if entity.text.lower() in text_lower:
                found.append(entity)
            elif entity.normalized_text and entity.normalized_text.lower() in text_lower:
                found.append(entity)
        
        return found
    
    def _extract_pattern_relations(
        self,
        sentence: str,
        entities: List[ExtractedEntity],
        entity_lookup: Dict[str, ExtractedEntity]
    ) -> List[ExtractedRelation]:
        """Extract relations using pattern matching"""
        relations = []
        
        for relation_type, patterns in self._compiled_patterns.items():
            for pattern, expected_subj_type, expected_obj_type, base_conf in patterns:
                for match in pattern.finditer(sentence):
                    # Get matched text components
                    if match.lastindex and match.lastindex >= 2:
                        subj_text = match.group(1).strip()
                        obj_text = match.group(2).strip()
                    else:
                        continue
                    
                    # Find matching entities
                    subject = entity_lookup.get(subj_text.lower())
                    obj = entity_lookup.get(obj_text.lower())
                    
                    # Also try partial matching
                    if not subject:
                        subject = self._find_best_entity_match(subj_text, entities)
                    if not obj:
                        obj = self._find_best_entity_match(obj_text, entities)
                    
                    if not subject or not obj:
                        continue
                    
                    # Validate entity types
                    if not self._validate_type_pair(relation_type, subject, obj):
                        continue
                    
                    relation = ExtractedRelation(
                        subject=subject,
                        predicate=relation_type,
                        object=obj,
                        confidence=base_conf,
                        ontology_property=self.ONTOLOGY_PROPERTIES.get(relation_type),
                        source_text=sentence,
                    )
                    relations.append(relation)
        
        return relations
    
    def _extract_cooccurrence_relations(
        self,
        sentence: str,
        entities: List[ExtractedEntity]
    ) -> List[ExtractedRelation]:
        """Extract relations based on entity co-occurrence and context"""
        relations = []
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.entity_type].append(entity)
        
        # Company-Risk co-occurrence
        for company in entities_by_type.get("Company", []):
            for risk_type in ["SupplyChainRisk", "CurrencyRisk", "RegulatoryRisk", 
                            "GeopoliticalRisk", "CompetitiveRisk", "CybersecurityRisk"]:
                for risk in entities_by_type.get(risk_type, []):
                    if self._entities_near_each_other(company.text, risk.text, sentence):
                        relation = ExtractedRelation(
                            subject=company,
                            predicate="FACES_RISK",
                            object=risk,
                            confidence=0.7,
                            ontology_property=self.ONTOLOGY_PROPERTIES.get("FACES_RISK"),
                            source_text=sentence,
                        )
                        relations.append(relation)
        
        # Company-Revenue co-occurrence
        for company in entities_by_type.get("Company", []):
            for metric_type in ["Revenue", "NetIncome", "MonetaryAmount"]:
                for metric in entities_by_type.get(metric_type, []):
                    if self._entities_near_each_other(company.text, metric.text, sentence, max_distance=100):
                        relation = ExtractedRelation(
                            subject=company,
                            predicate="REPORTED",
                            object=metric,
                            confidence=0.65,
                            ontology_property=self.ONTOLOGY_PROPERTIES.get("REPORTED"),
                            source_text=sentence,
                        )
                        relations.append(relation)
        
        return relations
    
    def _find_best_entity_match(
        self, 
        text: str, 
        entities: List[ExtractedEntity]
    ) -> Optional[ExtractedEntity]:
        """Find best matching entity for text"""
        text_lower = text.lower()
        
        for entity in entities:
            # Exact match
            if entity.text.lower() == text_lower:
                return entity
            
            # Substring match
            if text_lower in entity.text.lower() or entity.text.lower() in text_lower:
                return entity
        
        return None
    
    def _validate_type_pair(
        self, 
        relation_type: str, 
        subject: ExtractedEntity, 
        obj: ExtractedEntity
    ) -> bool:
        """Validate that entity types are valid for relation"""
        valid_pairs = self.VALID_TYPE_PAIRS.get(relation_type)
        
        if not valid_pairs:
            return True  # No constraint
        
        # Check if types match any valid pair
        subj_type = subject.entity_type
        obj_type = obj.entity_type
        
        # Also check parent types (e.g., SupplyChainRisk is a Risk)
        risk_types = {"SupplyChainRisk", "CurrencyRisk", "RegulatoryRisk", 
                     "GeopoliticalRisk", "CompetitiveRisk", "CybersecurityRisk", "TechnologyRisk"}
        
        for valid_subj, valid_obj in valid_pairs:
            subj_match = (subj_type == valid_subj or 
                         (valid_subj == "Risk" and subj_type in risk_types))
            obj_match = (obj_type == valid_obj or 
                        (valid_obj == "Risk" and obj_type in risk_types))
            
            if subj_match and obj_match:
                return True
        
        return False
    
    def _entities_near_each_other(
        self, 
        text1: str, 
        text2: str, 
        sentence: str,
        max_distance: int = 150
    ) -> bool:
        """Check if two entity texts are near each other in sentence"""
        sent_lower = sentence.lower()
        
        pos1 = sent_lower.find(text1.lower())
        pos2 = sent_lower.find(text2.lower())
        
        if pos1 == -1 or pos2 == -1:
            return False
        
        distance = abs(pos1 - pos2)
        return distance < max_distance
    
    def _deduplicate_relations(
        self, 
        relations: List[ExtractedRelation]
    ) -> List[ExtractedRelation]:
        """Remove duplicate relations"""
        seen = set()
        unique = []
        
        for relation in relations:
            key = (
                relation.subject.text.lower(),
                relation.predicate,
                relation.object.text.lower()
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(relation)
        
        return unique
    
    def get_relation_statistics(
        self, 
        relations: List[ExtractedRelation]
    ) -> Dict[str, Any]:
        """Get statistics about extracted relations"""
        stats = {
            "total_relations": len(relations),
            "by_predicate": defaultdict(int),
            "avg_confidence": 0.0,
            "unique_subjects": set(),
            "unique_objects": set(),
        }
        
        for relation in relations:
            stats["by_predicate"][relation.predicate] += 1
            stats["unique_subjects"].add(relation.subject.text.lower())
            stats["unique_objects"].add(relation.object.text.lower())
        
        if relations:
            stats["avg_confidence"] = sum(r.confidence for r in relations) / len(relations)
        
        stats["unique_subjects"] = len(stats["unique_subjects"])
        stats["unique_objects"] = len(stats["unique_objects"])
        stats["by_predicate"] = dict(stats["by_predicate"])
        
        return stats

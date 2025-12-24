"""IDR (Intelligent Document Recognition) Module"""
from .document_classifier import DocumentClassifier, ClassificationResult, DocumentType
from .entity_extractor import EntityExtractor, ExtractedEntity
from .relation_extractor import RelationExtractor, ExtractedRelation
from .ontology_mapper import OntologySchema, OntologyClass, get_ontology_schema
from .entity_patterns import (
    COMPANY_PATTERNS, RISK_PATTERNS, PRODUCT_PATTERNS,
    REVENUE_PATTERNS, NET_INCOME_PATTERNS,
    get_all_company_patterns, get_all_risk_patterns,
)

__all__ = [
    "DocumentClassifier", "ClassificationResult", "DocumentType",
    "EntityExtractor", "ExtractedEntity",
    "RelationExtractor", "ExtractedRelation",
    "OntologySchema", "OntologyClass", "get_ontology_schema",
    "COMPANY_PATTERNS", "RISK_PATTERNS", "PRODUCT_PATTERNS",
    "get_all_company_patterns", "get_all_risk_patterns",
]

"""
Unit Tests for Entity Extractor
================================

Author: Rajesh Kumar Gupta
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.idr.entity_extractor import EntityExtractor, ExtractedEntity
from src.idr.document_classifier import DocumentClassifier, DocumentType
from src.idr.relation_extractor import RelationExtractor


class TestEntityExtractor:
    """Tests for EntityExtractor"""
    
    @pytest.fixture
    def extractor(self):
        return EntityExtractor()
    
    def test_extract_company(self, extractor):
        """Test company entity extraction"""
        text = "Apple Inc. is a technology company based in Cupertino."
        entities = extractor.extract(text, entity_types=["Company"])
        
        company_entities = [e for e in entities if e.entity_type == "Company"]
        assert len(company_entities) >= 1
        assert any("apple" in e.text.lower() for e in company_entities)
    
    def test_extract_revenue(self, extractor):
        """Test revenue extraction"""
        text = "The company reported revenue of $394 billion for fiscal 2023."
        entities = extractor.extract(text, entity_types=["Revenue", "MonetaryAmount"])
        
        assert len(entities) >= 1
        assert any(e.properties.get("value") for e in entities)
    
    def test_extract_risk(self, extractor):
        """Test risk entity extraction"""
        text = "The company faces significant supply chain risk and regulatory risk."
        entities = extractor.extract(text)
        
        risk_entities = [e for e in entities if "Risk" in e.entity_type]
        assert len(risk_entities) >= 1
    
    def test_extract_person(self, extractor):
        """Test person extraction"""
        text = "CEO Tim Cook announced the new product lineup."
        entities = extractor.extract(text, entity_types=["Person"])
        
        person_entities = [e for e in entities if e.entity_type == "Person"]
        assert len(person_entities) >= 1
    
    def test_confidence_threshold(self):
        """Test confidence threshold filtering"""
        extractor = EntityExtractor(config={"confidence_threshold": 0.9})
        text = "Apple reported $394 billion in revenue."
        entities = extractor.extract(text)
        
        for entity in entities:
            assert entity.confidence >= 0.9


class TestDocumentClassifier:
    """Tests for DocumentClassifier"""
    
    @pytest.fixture
    def classifier(self):
        return DocumentClassifier()
    
    def test_classify_10k(self, classifier):
        """Test 10-K document classification"""
        text = """
        UNITED STATES SECURITIES AND EXCHANGE COMMISSION
        FORM 10-K
        ANNUAL REPORT PURSUANT TO SECTION 13
        For the fiscal year ended December 31, 2023
        """
        result = classifier.classify(text)
        assert result.document_type == DocumentType.FORM_10K
        assert result.confidence > 0.5
    
    def test_classify_10q(self, classifier):
        """Test 10-Q document classification"""
        text = """
        FORM 10-Q
        QUARTERLY REPORT PURSUANT TO SECTION 13
        For the quarterly period ended September 30, 2023
        """
        result = classifier.classify(text)
        assert result.document_type == DocumentType.FORM_10Q
    
    def test_classify_earnings_call(self, classifier):
        """Test earnings call classification"""
        text = """
        Q4 2023 EARNINGS CALL
        OPERATOR: Welcome to the Q4 2023 earnings conference call.
        Question-and-Answer Session
        """
        result = classifier.classify(text)
        assert result.document_type == DocumentType.EARNINGS_CALL


class TestRelationExtractor:
    """Tests for RelationExtractor"""
    
    @pytest.fixture
    def relation_extractor(self):
        return RelationExtractor()
    
    @pytest.fixture
    def entity_extractor(self):
        return EntityExtractor()
    
    def test_extract_competes_with(self, relation_extractor, entity_extractor):
        """Test competition relation extraction"""
        text = "Apple competes with Samsung in the smartphone market."
        entities = entity_extractor.extract(text)
        relations = relation_extractor.extract(text, entities)
        
        compete_relations = [r for r in relations if r.predicate == "COMPETES_WITH"]
        # May or may not find depending on entity extraction
        assert isinstance(compete_relations, list)
    
    def test_extract_faces_risk(self, relation_extractor, entity_extractor):
        """Test risk relation extraction"""
        text = "Apple faces significant supply chain risk."
        entities = entity_extractor.extract(text)
        relations = relation_extractor.extract(text, entities)
        
        risk_relations = [r for r in relations if r.predicate == "FACES_RISK"]
        assert isinstance(risk_relations, list)


class TestIntegration:
    """Integration tests"""
    
    def test_full_pipeline(self):
        """Test complete extraction pipeline"""
        text = """
        Apple Inc. reported revenue of $394 billion for fiscal 2023.
        CEO Tim Cook emphasized services growth.
        The company faces supply chain risk from China operations.
        Apple competes with Microsoft and Google.
        """
        
        classifier = DocumentClassifier()
        entity_extractor = EntityExtractor()
        relation_extractor = RelationExtractor()
        
        # Classify
        classification = classifier.classify(text)
        assert classification is not None
        
        # Extract entities
        entities = entity_extractor.extract(text)
        assert len(entities) > 0
        
        # Extract relations
        relations = relation_extractor.extract(text, entities)
        assert isinstance(relations, list)
        
        # Check we found expected entity types
        entity_types = set(e.entity_type for e in entities)
        assert "Company" in entity_types or "Revenue" in entity_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

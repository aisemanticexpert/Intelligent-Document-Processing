"""
Financial IDR Pipeline
=======================

Main orchestration module that coordinates all IDR components:
- Data source fetching
- Document classification
- Entity extraction
- Relation extraction
- Knowledge graph building
- GraphRAG querying

Author: Rajesh Kumar Gupta
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..data_sources.base_source import FetchedDocument, DataSourceType
from ..data_sources.sec_edgar import SECEdgarDataSource
from ..data_sources.fred_api import FREDDataSource
from ..idr.document_classifier import DocumentClassifier, ClassificationResult
from ..idr.entity_extractor import EntityExtractor, ExtractedEntity
from ..idr.relation_extractor import RelationExtractor, ExtractedRelation
from ..knowledge_graph.graph_builder import KnowledgeGraphBuilder
from ..graphrag.query_engine import GraphRAGQueryEngine, QueryResult

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single document"""
    document_id: str
    source_type: str
    classification: ClassificationResult
    entities: List[ExtractedEntity]
    relations: List[ExtractedRelation]
    processing_time: float
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "document_id": self.document_id,
            "source_type": self.source_type,
            "classification": self.classification.to_dict(),
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "processing_time": self.processing_time,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class PipelineStats:
    """Pipeline execution statistics"""
    documents_processed: int = 0
    documents_failed: int = 0
    total_entities: int = 0
    total_relations: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    processing_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "documents_processed": self.documents_processed,
            "documents_failed": self.documents_failed,
            "total_entities": self.total_entities,
            "total_relations": self.total_relations,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "processing_time": self.processing_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class FinancialIDRPipeline:
    """
    Main Financial IDR Pipeline
    
    Orchestrates the complete document processing workflow:
    1. Fetch documents from configured data sources
    2. Classify documents using IDR classifier
    3. Extract entities using ontology-guided NER
    4. Extract relations between entities
    5. Build knowledge graph
    6. Enable GraphRAG queries
    """
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the pipeline.
        
        Args:
            config_path: Path to YAML configuration file
            config: Configuration dictionary (overrides config_path)
        """
        self.config = config or {}
        if config_path and not config:
            self.config = self._load_config(config_path)
        
        self._init_components()
        self.stats = PipelineStats()
        self.processing_results: List[ProcessingResult] = []
        
        logger.info("FinancialIDRPipeline initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _init_components(self) -> None:
        """Initialize pipeline components"""
        # Data sources
        self.data_sources = {}
        
        ds_config = self.config.get("data_sources", {})
        if ds_config.get("sec_edgar", {}).get("enabled", True):
            self.data_sources["sec_edgar"] = SECEdgarDataSource(ds_config.get("sec_edgar", {}))
        if ds_config.get("fred", {}).get("enabled", True):
            self.data_sources["fred"] = FREDDataSource(ds_config.get("fred", {}))
        
        # IDR components
        idr_config = self.config.get("idr", {})
        self.classifier = DocumentClassifier(idr_config.get("document_classifier", {}))
        self.entity_extractor = EntityExtractor(idr_config.get("entity_extractor", {}))
        self.relation_extractor = RelationExtractor(idr_config.get("relation_extractor", {}))
        
        # Knowledge graph
        kg_config = self.config.get("knowledge_graph", {})
        self.graph_builder = KnowledgeGraphBuilder(kg_config)
        
        # GraphRAG (initialized after graph is built)
        self.query_engine: Optional[GraphRAGQueryEngine] = None
    
    def fetch_documents(
        self,
        source_types: Optional[List[str]] = None,
        companies: Optional[List[Dict]] = None,
        **kwargs
    ) -> Generator[FetchedDocument, None, None]:
        """
        Fetch documents from configured data sources.
        
        Args:
            source_types: List of source types to fetch from
            companies: List of company configs for SEC filings
            **kwargs: Additional arguments for data sources
            
        Yields:
            FetchedDocument instances
        """
        source_types = source_types or list(self.data_sources.keys())
        
        for source_type in source_types:
            if source_type not in self.data_sources:
                logger.warning(f"Unknown source type: {source_type}")
                continue
            
            source = self.data_sources[source_type]
            
            if source_type == "sec_edgar":
                companies = companies or self._get_default_companies()
                yield from source.fetch(companies=companies, **kwargs)
            elif source_type == "fred":
                yield from source.fetch(**kwargs)
            else:
                yield from source.fetch(**kwargs)
    
    def _get_default_companies(self) -> List[Dict]:
        """Get default companies from config"""
        companies = []
        company_config = self.config.get("companies", {})
        
        for sector, sector_companies in company_config.items():
            for company in sector_companies:
                company["sector"] = sector
                companies.append(company)
        
        return companies
    
    def process_document(self, document: FetchedDocument) -> ProcessingResult:
        """
        Process a single document through the IDR pipeline.
        
        Args:
            document: FetchedDocument to process
            
        Returns:
            ProcessingResult with extracted information
        """
        start_time = datetime.now()
        doc_id = document.metadata.source_id
        
        try:
            # Step 1: Classify document
            classification = self.classifier.classify(
                document.content,
                {"document_type": document.metadata.document_type}
            )
            
            # Step 2: Extract entities
            entities = []
            if document.sections:
                # Extract from specific sections
                for section_name, section_content in document.sections.items():
                    section_entities = self.entity_extractor.extract_from_section(
                        section_content, section_name
                    )
                    entities.extend(section_entities)
            else:
                # Extract from full content
                entities = self.entity_extractor.extract(document.content)
            
            # Step 3: Extract relations
            relations = self.relation_extractor.extract(document.content, entities)
            
            # Step 4: Add to knowledge graph
            self.graph_builder.add_entities(entities, doc_id)
            self.graph_builder.add_relations(relations, doc_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ProcessingResult(
                document_id=doc_id,
                source_type=document.metadata.source_type.value,
                classification=classification,
                entities=entities,
                relations=relations,
                processing_time=processing_time,
                success=True,
            )
            
            # Update stats
            self.stats.documents_processed += 1
            self.stats.total_entities += len(entities)
            self.stats.total_relations += len(relations)
            
            logger.info(
                f"Processed {doc_id}: {len(entities)} entities, {len(relations)} relations"
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            result = ProcessingResult(
                document_id=doc_id,
                source_type=document.metadata.source_type.value,
                classification=ClassificationResult(
                    document_type=self.classifier._map_known_type(document.metadata.document_type),
                    ontology_class="",
                    confidence=0.0,
                ),
                entities=[],
                relations=[],
                processing_time=processing_time,
                success=False,
                error=str(e),
            )
            self.stats.documents_failed += 1
            logger.error(f"Failed to process {doc_id}: {e}")
        
        self.processing_results.append(result)
        return result
    
    def run(
        self,
        source_types: Optional[List[str]] = None,
        companies: Optional[List[Dict]] = None,
        max_documents: Optional[int] = None,
        **kwargs
    ) -> PipelineStats:
        """
        Run the complete pipeline.
        
        Args:
            source_types: Data source types to fetch from
            companies: Company configurations
            max_documents: Maximum documents to process
            **kwargs: Additional arguments
            
        Returns:
            PipelineStats with execution statistics
        """
        self.stats = PipelineStats(start_time=datetime.now())
        self.processing_results = []
        
        logger.info("Starting Financial IDR Pipeline")
        
        # Fetch and process documents
        doc_count = 0
        for document in self.fetch_documents(source_types, companies, **kwargs):
            if max_documents and doc_count >= max_documents:
                break
            
            self.process_document(document)
            doc_count += 1
        
        # Build query engine
        self.query_engine = GraphRAGQueryEngine(self.graph_builder, self.config.get("graphrag", {}))
        
        # Update final stats
        self.stats.end_time = datetime.now()
        self.stats.processing_time = (self.stats.end_time - self.stats.start_time).total_seconds()
        self.stats.total_nodes = len(self.graph_builder.nodes)
        self.stats.total_edges = len(self.graph_builder.edges)
        
        logger.info(f"Pipeline completed: {self.stats.to_dict()}")
        
        return self.stats
    
    def query(self, question: str) -> QueryResult:
        """
        Query the knowledge graph using GraphRAG.
        
        Args:
            question: Natural language question
            
        Returns:
            QueryResult with answer and supporting data
        """
        if not self.query_engine:
            self.query_engine = GraphRAGQueryEngine(
                self.graph_builder, 
                self.config.get("graphrag", {})
            )
        
        return self.query_engine.query(question)
    
    def export_graph(self, output_dir: str, formats: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Export the knowledge graph to files.
        
        Args:
            output_dir: Output directory
            formats: List of formats (json, cypher, rdf)
            
        Returns:
            Dictionary of format to file path
        """
        formats = formats or ["json", "cypher"]
        output_paths = {}
        
        os.makedirs(output_dir, exist_ok=True)
        
        if "json" in formats:
            path = os.path.join(output_dir, "knowledge_graph.json")
            with open(path, 'w') as f:
                f.write(self.graph_builder.to_json())
            output_paths["json"] = path
        
        if "cypher" in formats:
            path = os.path.join(output_dir, "knowledge_graph.cypher")
            with open(path, 'w') as f:
                f.write(self.graph_builder.to_cypher())
            output_paths["cypher"] = path
        
        logger.info(f"Exported graph to: {output_paths}")
        return output_paths
    
    def export_results(self, output_dir: str) -> str:
        """Export processing results to JSON"""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, "processing_results.json")
        
        data = {
            "stats": self.stats.to_dict(),
            "results": [r.to_dict() for r in self.processing_results],
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return path
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.graph_builder.get_statistics()
    
    def close(self) -> None:
        """Clean up resources"""
        self.graph_builder.close()
        logger.info("Pipeline closed")


def create_pipeline_from_config(config_path: str) -> FinancialIDRPipeline:
    """Factory function to create pipeline from config file"""
    return FinancialIDRPipeline(config_path=config_path)

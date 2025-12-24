"""
REST API Server Module
=======================

Provides REST API endpoints for the Financial IDR Pipeline.
Built with Flask for simplicity and easy deployment.

Author: Rajesh Kumar Gupta
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Flask
try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask not available. Install: pip install flask flask-cors")


# =============================================================================
# API RESPONSE HELPERS
# =============================================================================

def api_response(data: Any = None, message: str = "Success", status: int = 200) -> tuple:
    """Create standardized API response"""
    response = {
        "status": "success" if status < 400 else "error",
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status


def error_response(message: str, status: int = 400) -> tuple:
    """Create error response"""
    return api_response(None, message, status)


# =============================================================================
# API SERVER CLASS
# =============================================================================

class IDRAPIServer:
    """
    REST API Server for Financial IDR Pipeline
    
    Endpoints:
    - POST /api/classify - Classify document type
    - POST /api/extract/entities - Extract entities from text
    - POST /api/extract/relations - Extract relations from text
    - POST /api/process - Process full document through pipeline
    - GET /api/graph/stats - Get knowledge graph statistics
    - POST /api/query - Query the knowledge graph (GraphRAG)
    - GET /api/companies - List registered companies
    - GET /api/health - Health check
    """
    
    def __init__(
        self, 
        pipeline: Optional[Any] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize API server.
        
        Args:
            pipeline: FinancialIDRPipeline instance
            config: Configuration dictionary
        """
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask not available. Install: pip install flask flask-cors")
        
        self.config = config or {}
        self.pipeline = pipeline
        
        # Create Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configure
        self.app.config['JSON_SORT_KEYS'] = False
        self.app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
        
        # Register routes
        self._register_routes()
        
        logger.info("IDRAPIServer initialized")
    
    def _register_routes(self) -> None:
        """Register API routes"""
        
        # Health check
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return api_response({
                "status": "healthy",
                "version": "1.0.0",
                "pipeline_ready": self.pipeline is not None,
            })
        
        # Document classification
        @self.app.route('/api/classify', methods=['POST'])
        def classify():
            try:
                data = request.get_json()
                if not data or 'text' not in data:
                    return error_response("Missing 'text' field", 400)
                
                text = data['text']
                
                # Import and use classifier
                from ..idr.document_classifier import DocumentClassifier
                classifier = DocumentClassifier()
                result = classifier.classify(text)
                
                return api_response({
                    "document_type": result.document_type.value,
                    "confidence": result.confidence,
                    "sections_detected": result.sections_detected,
                    "ontology_class": result.ontology_class,
                })
            except Exception as e:
                logger.error(f"Classification error: {e}")
                return error_response(str(e), 500)
        
        # Entity extraction
        @self.app.route('/api/extract/entities', methods=['POST'])
        def extract_entities():
            try:
                data = request.get_json()
                if not data or 'text' not in data:
                    return error_response("Missing 'text' field", 400)
                
                text = data['text']
                entity_types = data.get('entity_types', None)
                
                from ..idr.entity_extractor import EntityExtractor
                extractor = EntityExtractor()
                entities = extractor.extract(text, entity_types=entity_types)
                
                return api_response({
                    "entity_count": len(entities),
                    "entities": [
                        {
                            "text": e.text,
                            "type": e.entity_type,
                            "confidence": e.confidence,
                            "ontology_class": e.ontology_class,
                            "properties": e.properties,
                        }
                        for e in entities
                    ],
                })
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")
                return error_response(str(e), 500)
        
        # Relation extraction
        @self.app.route('/api/extract/relations', methods=['POST'])
        def extract_relations():
            try:
                data = request.get_json()
                if not data or 'text' not in data:
                    return error_response("Missing 'text' field", 400)
                
                text = data['text']
                
                from ..idr.entity_extractor import EntityExtractor
                from ..idr.relation_extractor import RelationExtractor
                
                entity_extractor = EntityExtractor()
                relation_extractor = RelationExtractor()
                
                entities = entity_extractor.extract(text)
                relations = relation_extractor.extract(text, entities)
                
                return api_response({
                    "relation_count": len(relations),
                    "relations": [
                        {
                            "subject": r.subject.text,
                            "subject_type": r.subject.entity_type,
                            "predicate": r.predicate,
                            "object": r.object.text,
                            "object_type": r.object.entity_type,
                            "confidence": r.confidence,
                        }
                        for r in relations
                    ],
                })
            except Exception as e:
                logger.error(f"Relation extraction error: {e}")
                return error_response(str(e), 500)
        
        # Full document processing
        @self.app.route('/api/process', methods=['POST'])
        def process_document():
            try:
                data = request.get_json()
                if not data or 'text' not in data:
                    return error_response("Missing 'text' field", 400)
                
                text = data['text']
                document_id = data.get('document_id', 'api_doc')
                
                from ..idr.document_classifier import DocumentClassifier
                from ..idr.entity_extractor import EntityExtractor
                from ..idr.relation_extractor import RelationExtractor
                from ..knowledge_graph.graph_builder import KnowledgeGraphBuilder
                
                # Process through pipeline
                classifier = DocumentClassifier()
                entity_extractor = EntityExtractor()
                relation_extractor = RelationExtractor()
                
                classification = classifier.classify(text)
                entities = entity_extractor.extract(text)
                relations = relation_extractor.extract(text, entities)
                
                # Build graph
                graph = KnowledgeGraphBuilder()
                graph.add_entities(entities, document_id)
                graph.add_relations(relations, document_id)
                
                stats = graph.get_statistics()
                
                return api_response({
                    "document_id": document_id,
                    "classification": {
                        "type": classification.document_type.value,
                        "confidence": classification.confidence,
                    },
                    "extraction": {
                        "entity_count": len(entities),
                        "relation_count": len(relations),
                    },
                    "graph": stats,
                    "cypher": graph.to_cypher()[:5000],  # Truncate for response
                })
            except Exception as e:
                logger.error(f"Document processing error: {e}")
                return error_response(str(e), 500)
        
        # Knowledge graph query (GraphRAG)
        @self.app.route('/api/query', methods=['POST'])
        def query_graph():
            try:
                data = request.get_json()
                if not data or 'question' not in data:
                    return error_response("Missing 'question' field", 400)
                
                question = data['question']
                
                if self.pipeline and self.pipeline.query_engine:
                    result = self.pipeline.query(question)
                    return api_response({
                        "question": result.question,
                        "answer": result.answer,
                        "cypher_query": result.cypher_query,
                        "confidence": result.confidence,
                        "retrieved_nodes": len(result.retrieved_nodes),
                        "retrieved_edges": len(result.retrieved_edges),
                    })
                else:
                    return error_response("Pipeline not initialized or no graph available", 503)
                    
            except Exception as e:
                logger.error(f"Query error: {e}")
                return error_response(str(e), 500)
        
        # Graph statistics
        @self.app.route('/api/graph/stats', methods=['GET'])
        def graph_stats():
            try:
                if self.pipeline:
                    stats = self.pipeline.get_graph_statistics()
                    return api_response(stats)
                else:
                    return error_response("Pipeline not initialized", 503)
            except Exception as e:
                return error_response(str(e), 500)
        
        # List companies
        @self.app.route('/api/companies', methods=['GET'])
        def list_companies():
            try:
                from ..data_sources.company_registry import get_company_registry
                registry = get_company_registry()
                
                sector = request.args.get('sector')
                
                if sector:
                    from ..data_sources.company_registry import Sector
                    try:
                        sector_enum = Sector(sector)
                        companies = registry.get_by_sector(sector_enum)
                    except ValueError:
                        return error_response(f"Invalid sector: {sector}", 400)
                else:
                    companies = registry.get_all()
                
                return api_response({
                    "count": len(companies),
                    "companies": [c.to_dict() for c in companies],
                })
            except Exception as e:
                return error_response(str(e), 500)
        
        # Get company by ticker
        @self.app.route('/api/companies/<ticker>', methods=['GET'])
        def get_company(ticker: str):
            try:
                from ..data_sources.company_registry import get_company_registry
                registry = get_company_registry()
                
                company = registry.get(ticker.upper())
                if company:
                    return api_response(company.to_dict())
                else:
                    return error_response(f"Company not found: {ticker}", 404)
            except Exception as e:
                return error_response(str(e), 500)
        
        # Ontology info
        @self.app.route('/api/ontology', methods=['GET'])
        def ontology_info():
            try:
                from ..idr.ontology_mapper import get_ontology_schema
                schema = get_ontology_schema()
                
                return api_response({
                    "entity_types": schema.get_all_entity_types(),
                    "relation_types": schema.get_all_relation_types(),
                })
            except Exception as e:
                return error_response(str(e), 500)
        
        # Export graph
        @self.app.route('/api/graph/export', methods=['GET'])
        def export_graph():
            try:
                format_type = request.args.get('format', 'json')
                
                if self.pipeline:
                    graph_data = self.pipeline.graph_builder.to_dict()
                    
                    if format_type == 'json':
                        return api_response(graph_data)
                    elif format_type == 'cypher':
                        cypher = self.pipeline.graph_builder.to_cypher()
                        return api_response({"cypher": cypher})
                    else:
                        return error_response(f"Unsupported format: {format_type}", 400)
                else:
                    return error_response("Pipeline not initialized", 503)
            except Exception as e:
                return error_response(str(e), 500)
    
    def set_pipeline(self, pipeline: Any) -> None:
        """Set the pipeline instance"""
        self.pipeline = pipeline
        logger.info("Pipeline attached to API server")
    
    def run(
        self, 
        host: str = "0.0.0.0", 
        port: int = 5000, 
        debug: bool = False,
    ) -> None:
        """Run the API server"""
        logger.info(f"Starting IDR API Server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_api_server(
    pipeline: Optional[Any] = None,
    config: Optional[Dict] = None,
) -> IDRAPIServer:
    """Factory function to create API server"""
    return IDRAPIServer(pipeline=pipeline, config=config)


# =============================================================================
# CLI RUNNER
# =============================================================================

def run_api_server():
    """Run API server from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial IDR API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    server = create_api_server()
    server.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    run_api_server()

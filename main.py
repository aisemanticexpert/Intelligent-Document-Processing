#!/usr/bin/env python3
"""
Financial IDR Pipeline - Main Entry Point
==========================================

Run the Financial IDR pipeline from command line.

Usage:
    python main.py --config config/config.yaml
    python main.py --demo
    python main.py --query "What risks does Apple face?"
    python main.py --api --port 5000

Author: Rajesh Kumar Gupta
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline.idr_pipeline import FinancialIDRPipeline
from src.idr.document_classifier import DocumentClassifier
from src.idr.entity_extractor import EntityExtractor
from src.idr.relation_extractor import RelationExtractor
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.graphrag.query_engine import GraphRAGQueryEngine


def setup_logging(level: str = "INFO") -> None:
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_demo() -> None:
    """Run a demonstration of the IDR pipeline"""
    print("=" * 80)
    print("FINANCIAL IDR PIPELINE - DEMONSTRATION")
    print("=" * 80)
    
    # Sample 10-K excerpt
    sample_document = """
    UNITED STATES SECURITIES AND EXCHANGE COMMISSION
    Washington, D.C. 20549
    FORM 10-K
    
    APPLE INC.
    
    ITEM 1. BUSINESS
    
    Apple Inc. designs, manufactures, and markets smartphones, personal computers,
    tablets, wearables and accessories, and sells a variety of related services.
    The Company's products include iPhone, Mac, iPad, and wearables, home and accessories.
    
    Apple's CEO Tim Cook has emphasized the company's focus on services growth.
    The Company reported revenue of $394.3 billion for fiscal 2023.
    iPhone generated revenue of $200.6 billion, representing 51% of total revenue.
    
    ITEM 1A. RISK FACTORS
    
    The Company faces significant supply chain risk due to its heavy reliance on
    manufacturing in China. Geopolitical tensions between the US and China pose
    ongoing challenges to the Company's operations.
    
    Apple is exposed to currency risk given its global operations. Approximately
    60% of the Company's revenue is generated outside the United States.
    
    The Company faces intense competition from Samsung, Google, and Microsoft
    in various product categories. Competitive pressure could impact market share.
    
    Regulatory risk continues to grow as governments worldwide implement new
    data privacy regulations and antitrust measures affecting technology companies.
    
    The Company faces cybersecurity risk as a high-profile target for malicious actors.
    
    ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
    
    Total net sales increased 8% or $28.5 billion during 2023. Services revenue
    reached $85.2 billion, an increase of 14% compared to fiscal 2022.
    
    Net income was $97.0 billion for fiscal 2023, compared to $94.7 billion for 2022.
    Earnings per share was $6.13, up from $5.89 in the prior year.
    
    The Company generated operating cash flow of $110.5 billion during 2023.
    """
    
    print("\n📄 Processing Sample 10-K Document...")
    print("-" * 40)
    
    # Step 1: Document Classification
    print("\n[STAGE 1] Document Classification")
    classifier = DocumentClassifier()
    classification = classifier.classify(sample_document)
    print(f"  Document Type: {classification.document_type.value}")
    print(f"  Confidence: {classification.confidence:.2%}")
    print(f"  Sections Detected: {classification.sections_detected}")
    
    # Step 2: Entity Extraction
    print("\n[STAGE 2] Entity Extraction")
    extractor = EntityExtractor()
    entities = extractor.extract(sample_document)
    
    print(f"  Total Entities: {len(entities)}")
    
    # Group by type
    entities_by_type = {}
    for e in entities:
        if e.entity_type not in entities_by_type:
            entities_by_type[e.entity_type] = []
        entities_by_type[e.entity_type].append(e)
    
    for entity_type, type_entities in sorted(entities_by_type.items()):
        print(f"\n  {entity_type} ({len(type_entities)}):")
        for e in type_entities[:3]:
            conf = f"{e.confidence:.0%}"
            extra = ""
            if "value" in e.properties:
                extra = f" [${e.properties['value']:,.0f}]"
            print(f"    - {e.text} ({conf}){extra}")
        if len(type_entities) > 3:
            print(f"    ... and {len(type_entities) - 3} more")
    
    # Step 3: Relation Extraction
    print("\n[STAGE 3] Relation Extraction")
    relation_extractor = RelationExtractor()
    relations = relation_extractor.extract(sample_document, entities)
    
    print(f"  Total Relations: {len(relations)}")
    for r in relations[:10]:
        print(f"    ({r.subject.text}) --[{r.predicate}]--> ({r.object.text})")
    
    # Step 4: Knowledge Graph Building
    print("\n[STAGE 4] Knowledge Graph Construction")
    graph_builder = KnowledgeGraphBuilder()
    graph_builder.add_entities(entities, "demo_10k")
    graph_builder.add_relations(relations, "demo_10k")
    
    stats = graph_builder.get_statistics()
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    print(f"  Nodes by Type: {json.dumps(stats['nodes_by_type'], indent=4)}")
    print(f"  Edges by Type: {json.dumps(stats['edges_by_type'], indent=4)}")
    
    # Step 5: GraphRAG Query
    print("\n[STAGE 5] GraphRAG Query Engine")
    query_engine = GraphRAGQueryEngine(graph_builder)
    
    questions = [
        "What are the key risks facing Apple?",
        "What is Apple's revenue?",
        "Who are Apple's competitors?",
    ]
    
    for question in questions:
        print(f"\n  ❓ Question: {question}")
        result = query_engine.query(question)
        print(f"  📊 Retrieved: {len(result.retrieved_nodes)} nodes, {len(result.retrieved_edges)} edges")
        print(f"  💡 Answer: {result.answer[:200]}...")
    
    # Export Cypher
    print("\n[STAGE 6] Export to Neo4j Cypher")
    cypher = graph_builder.to_cypher()
    print(f"  Generated {cypher.count('MERGE')} MERGE statements")
    print("\n  Sample Cypher:")
    for line in cypher.split('\n')[:10]:
        if line.strip():
            print(f"    {line}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


def run_pipeline(config_path: str, max_docs: int = 5) -> None:
    """Run the full pipeline"""
    print(f"Running pipeline with config: {config_path}")
    
    pipeline = FinancialIDRPipeline(config_path=config_path)
    stats = pipeline.run(max_documents=max_docs)
    
    print("\nPipeline Statistics:")
    print(json.dumps(stats.to_dict(), indent=2))
    
    # Export results
    pipeline.export_graph("data/graphs")
    pipeline.export_results("data/reports")
    
    print("\nResults exported to data/ directory")


def run_query(question: str, config_path: str = None) -> None:
    """Run a query on existing graph"""
    print(f"Query: {question}")
    run_demo()  # Build demo graph first


def run_api_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
    """Run the REST API server"""
    try:
        from src.api.server import create_api_server
        
        print(f"Starting Financial IDR API Server on {host}:{port}")
        print("Available endpoints:")
        print("  POST /api/classify - Classify document type")
        print("  POST /api/extract/entities - Extract entities")
        print("  POST /api/extract/relations - Extract relations")
        print("  POST /api/process - Full document processing")
        print("  POST /api/query - GraphRAG query")
        print("  GET  /api/companies - List companies")
        print("  GET  /api/health - Health check")
        
        server = create_api_server()
        server.run(host=host, port=port, debug=debug)
    except ImportError as e:
        print(f"Error: Flask not installed. Run: pip install flask flask-cors")
        print(f"Details: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Financial IDR Pipeline - Intelligent Document Recognition for Finance"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run demonstration with sample document"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query the knowledge graph"
    )
    
    parser.add_argument(
        "--max-docs", "-m",
        type=int,
        default=5,
        help="Maximum documents to process"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Run REST API server"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="API server port"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if args.api:
        run_api_server(args.host, args.port)
    elif args.demo:
        run_demo()
    elif args.query:
        run_query(args.query, args.config)
    else:
        run_pipeline(args.config, args.max_docs)


if __name__ == "__main__":
    main()

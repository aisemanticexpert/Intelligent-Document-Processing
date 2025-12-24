#!/usr/bin/env python3
"""
Example: Process Multiple 10-K Filings
======================================

This example demonstrates how to:
1. Fetch 10-K filings from SEC EDGAR
2. Process documents through IDR pipeline
3. Build knowledge graph
4. Query using GraphRAG

Author: Rajesh Kumar Gupta
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.idr_pipeline import FinancialIDRPipeline
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.graphrag.query_engine import GraphRAGQueryEngine


def main():
    """Run example pipeline"""
    
    print("=" * 60)
    print("Financial IDR Pipeline - Example")
    print("=" * 60)
    
    # Define companies to process
    companies = [
        {"ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193", "sector": "Technology"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "cik": "0000789019", "sector": "Technology"},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "cik": "0000019617", "sector": "Financial"},
    ]
    
    # Configuration
    config = {
        "data_sources": {
            "sec_edgar": {
                "enabled": True,
                "user_agent": "FinancialIDR/1.0 (demo@example.com)",
                "rate_limit": 10,
                "filing_types": ["10-K"],
            }
        },
        "idr": {
            "entity_extractor": {
                "confidence_threshold": 0.7,
            }
        },
        "knowledge_graph": {
            "backend": "memory",
        },
    }
    
    # Initialize pipeline
    print("\n📦 Initializing pipeline...")
    pipeline = FinancialIDRPipeline(config=config)
    
    # Note: In a real scenario, this would fetch from SEC EDGAR
    # For this demo, we'll use sample content
    print("\n📥 Processing sample documents...")
    
    # Sample 10-K excerpts (in production, these come from SEC EDGAR)
    sample_documents = [
        {
            "company": "Apple Inc.",
            "content": """
            Apple Inc. designs and sells consumer electronics including iPhone, iPad, and Mac.
            The company reported revenue of $383 billion for fiscal year 2023.
            Tim Cook serves as CEO of Apple.
            Apple faces supply chain risk due to manufacturing concentration in China.
            The company competes with Samsung, Google, and Microsoft.
            """
        },
        {
            "company": "Microsoft Corporation",
            "content": """
            Microsoft Corporation develops software, cloud services, and hardware.
            Azure cloud services generated $80 billion in revenue.
            Satya Nadella is the CEO of Microsoft.
            Microsoft faces regulatory risk from antitrust investigations.
            The company competes with Amazon AWS and Google Cloud.
            """
        },
        {
            "company": "JPMorgan Chase",
            "content": """
            JPMorgan Chase is a leading financial services company.
            The bank reported net income of $48 billion in 2023.
            Jamie Dimon serves as CEO of JPMorgan.
            JPMorgan faces credit risk from commercial real estate loans.
            The company competes with Goldman Sachs and Bank of America.
            """
        },
    ]
    
    # Process each document
    from src.data_sources.base_source import FetchedDocument, DocumentMetadata, DataSourceType
    from datetime import datetime
    
    for i, doc in enumerate(sample_documents):
        metadata = DocumentMetadata(
            source_id=f"sample_{i}",
            source_type=DataSourceType.SEC_EDGAR,
            document_type="10-K",
            company_name=doc["company"],
        )
        fetched_doc = FetchedDocument(
            metadata=metadata,
            content=doc["content"],
        )
        
        result = pipeline.process_document(fetched_doc)
        print(f"  ✓ {doc['company']}: {len(result.entities)} entities, {len(result.relations)} relations")
    
    # Get statistics
    print("\n📊 Knowledge Graph Statistics:")
    stats = pipeline.get_graph_statistics()
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    print(f"  Nodes by Type: {stats['nodes_by_type']}")
    print(f"  Edges by Type: {stats['edges_by_type']}")
    
    # Query the graph
    print("\n🔍 GraphRAG Queries:")
    
    questions = [
        "What risks do technology companies face?",
        "What is Apple's revenue?",
        "Who are the CEOs mentioned?",
        "What companies compete with each other?",
    ]
    
    for question in questions:
        print(f"\n  ❓ {question}")
        result = pipeline.query(question)
        print(f"  💡 {result.answer[:200]}...")
    
    # Export graph
    print("\n💾 Exporting knowledge graph...")
    output_paths = pipeline.export_graph("data/output", formats=["json", "cypher"])
    for fmt, path in output_paths.items():
        print(f"  ✓ {fmt}: {path}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

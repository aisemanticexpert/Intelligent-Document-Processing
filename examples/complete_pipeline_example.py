#!/usr/bin/env python3
"""
Complete Pipeline Example
=========================

Demonstrates the full Financial IDR pipeline:
1. Company Registry with multi-sector companies
2. PDF parsing capabilities
3. Ontology-guided entity extraction
4. Knowledge graph construction
5. GraphRAG querying

Author: Rajesh Kumar Gupta
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_sources.company_registry import (
    get_company_registry, Sector, get_sample_companies
)
from src.idr.document_classifier import DocumentClassifier
from src.idr.entity_extractor import EntityExtractor
from src.idr.relation_extractor import RelationExtractor
from src.idr.ontology_mapper import get_ontology_schema, OntologyNamespace
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.graphrag.query_engine import GraphRAGQueryEngine


def print_section(title: str) -> None:
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def demo_company_registry() -> None:
    """Demonstrate company registry"""
    print_section("COMPANY REGISTRY - Multi-Sector Companies")
    
    registry = get_company_registry()
    
    print(f"\n📊 Total Companies Registered: {len(registry)}")
    
    for sector in Sector:
        companies = registry.get_by_sector(sector)
        if companies:
            print(f"\n{sector.value} ({len(companies)} companies):")
            for c in companies[:3]:
                print(f"  • {c.ticker}: {c.name}")
                print(f"      CIK: {c.cik} | Industry: {c.industry}")
            if len(companies) > 3:
                print(f"      ... and {len(companies) - 3} more")
    
    # Show sample config for pipeline
    print("\n📋 Sample Pipeline Configuration:")
    sample = get_sample_companies(per_sector=1)
    for company in sample[:5]:
        print(f"  - ticker: \"{company['ticker']}\", cik: \"{company['cik']}\", sector: \"{company['sector']}\"")


def demo_ontology_schema() -> None:
    """Demonstrate ontology schema"""
    print_section("ONTOLOGY SCHEMA - Semantic Expert AI Namespaces")
    
    schema = get_ontology_schema()
    
    print("\n🏷️  Namespaces:")
    for ns in OntologyNamespace:
        print(f"  {ns.name}: {ns.value}")
    
    print("\n📦 Entity Type Mappings:")
    entity_types = schema.get_all_entity_types()
    for entity_type in sorted(entity_types)[:15]:
        uri = schema.map_entity_type(entity_type)
        local_name = uri.split("#")[-1] if uri and "#" in uri else (uri.split("/")[-1] if uri else "N/A")
        print(f"  {entity_type:25} → {local_name}")
    
    print("\n🔗 Relation Type Mappings:")
    relation_types = schema.get_all_relation_types()
    for rel_type in sorted(relation_types)[:10]:
        uri = schema.map_relation_type(rel_type)
        local_name = uri.split("#")[-1] if uri and "#" in uri else (uri.split("/")[-1] if uri else "N/A")
        print(f"  {rel_type:25} → {local_name}")


def demo_idr_processing() -> None:
    """Demonstrate IDR processing stages"""
    print_section("IDR PROCESSING - 6-Stage Pipeline")
    
    # Sample 10-K content (multiple companies)
    sample_documents = {
        "Apple": """
        Apple Inc. (AAPL) designs, manufactures, and markets smartphones, 
        personal computers, tablets, wearables and accessories.
        
        For fiscal 2024, Apple reported total revenue of $383.3 billion.
        iPhone revenue was $200.6 billion, representing 52% of total revenue.
        Services revenue reached $85.2 billion, growing 14% year-over-year.
        
        Tim Cook, CEO of Apple, stated that the company continues to invest
        in AI and machine learning capabilities.
        
        RISK FACTORS:
        The company faces significant supply chain risk due to concentration
        of manufacturing in China and Taiwan. Geopolitical tensions pose
        ongoing challenges. Apple is exposed to currency risk with 60% of
        revenue from international markets. Intense competition from Samsung,
        Google, and Microsoft affects market share. Regulatory risk from
        antitrust investigations in the EU and US remains a concern.
        """,
        
        "JPMorgan": """
        JPMorgan Chase & Co. (JPM) is a leading global financial services firm.
        
        For fiscal 2024, JPMorgan reported net revenue of $158.1 billion.
        Net income reached $48.3 billion with earnings per share of $16.23.
        Total assets exceeded $3.9 trillion.
        
        Jamie Dimon, CEO of JPMorgan, highlighted the bank's strong capital position.
        
        RISK FACTORS:
        The company faces credit risk from commercial real estate exposure.
        Interest rate risk affects net interest income. Regulatory risk from
        Basel III requirements impacts capital planning. Cybersecurity risk
        remains a top priority given the sensitive financial data handled.
        JPMorgan competes with Goldman Sachs, Morgan Stanley, and Bank of America.
        """,
        
        "ExxonMobil": """
        Exxon Mobil Corporation (XOM) is an integrated oil and gas company.
        
        For fiscal 2024, ExxonMobil reported revenue of $344.6 billion.
        Net income was $36.0 billion. Operating cash flow reached $59.1 billion.
        
        Darren Woods serves as CEO of ExxonMobil.
        
        RISK FACTORS:
        The company faces commodity price risk from oil and gas price volatility.
        Environmental risk from climate change regulations affects operations.
        Geopolitical risk in key producing regions like the Middle East.
        ExxonMobil competes with Chevron, Shell, and BP.
        """
    }
    
    # Initialize IDR components
    classifier = DocumentClassifier()
    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()
    schema = get_ontology_schema()
    graph_builder = KnowledgeGraphBuilder()
    
    all_entities = []
    all_relations = []
    
    for company_name, content in sample_documents.items():
        print(f"\n📄 Processing: {company_name}")
        print("-" * 40)
        
        # Stage 1: Classification
        classification = classifier.classify(content)
        print(f"  [1] Classification: {classification.document_type.value} ({classification.confidence:.0%})")
        
        # Stage 2: Entity Extraction
        entities = entity_extractor.extract(content)
        print(f"  [2] Entities Extracted: {len(entities)}")
        
        # Show entities by type
        entity_counts = {}
        for e in entities:
            entity_counts[e.entity_type] = entity_counts.get(e.entity_type, 0) + 1
        for etype, count in sorted(entity_counts.items()):
            print(f"      - {etype}: {count}")
        
        # Stage 3: Ontology Mapping
        mapped_count = 0
        for entity in entities:
            ontology_class = schema.map_entity_type(entity.entity_type)
            if ontology_class:
                entity.ontology_class = ontology_class
                mapped_count += 1
        print(f"  [3] Ontology Mapped: {mapped_count}/{len(entities)} entities")
        
        # Stage 4: Relation Extraction
        relations = relation_extractor.extract(content, entities)
        print(f"  [4] Relations Extracted: {len(relations)}")
        
        # Map relations to ontology
        for rel in relations:
            rel.ontology_property = schema.map_relation_type(rel.predicate)
        
        # Stage 5: Knowledge Graph Building
        doc_id = f"{company_name.lower()}_10k"
        graph_builder.add_entities(entities, doc_id)
        graph_builder.add_relations(relations, doc_id)
        print(f"  [5] Added to Knowledge Graph")
        
        all_entities.extend(entities)
        all_relations.extend(relations)
    
    # Stage 6: Graph Statistics
    print_section("KNOWLEDGE GRAPH STATISTICS")
    
    stats = graph_builder.get_statistics()
    print(f"\n📊 Graph Size:")
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    
    print(f"\n📦 Nodes by Type:")
    for node_type, count in sorted(stats['nodes_by_type'].items(), key=lambda x: -x[1]):
        print(f"  {node_type:25}: {count}")
    
    print(f"\n🔗 Edges by Type:")
    for edge_type, count in sorted(stats['edges_by_type'].items(), key=lambda x: -x[1]):
        print(f"  {edge_type:25}: {count}")
    
    # Sample relations
    print(f"\n📋 Sample Extracted Relations:")
    for rel in all_relations[:10]:
        print(f"  ({rel.subject.text}) --[{rel.predicate}]--> ({rel.object.text})")
    
    return graph_builder


def demo_graphrag_queries(graph_builder: KnowledgeGraphBuilder) -> None:
    """Demonstrate GraphRAG querying"""
    print_section("GRAPHRAG QUERY ENGINE")
    
    query_engine = GraphRAGQueryEngine(graph_builder)
    
    questions = [
        "What risks does Apple face?",
        "What is JPMorgan's revenue?",
        "Who are the CEOs mentioned?",
        "What companies compete with each other?",
        "What cybersecurity risks are disclosed?",
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        result = query_engine.query(question)
        print(f"   Retrieved: {len(result.retrieved_nodes)} nodes, {len(result.retrieved_edges)} edges")
        
        # Show truncated answer
        answer = result.answer
        if len(answer) > 200:
            answer = answer[:200] + "..."
        print(f"   💡 {answer}")


def demo_cypher_export(graph_builder: KnowledgeGraphBuilder) -> None:
    """Demonstrate Cypher export"""
    print_section("NEO4J CYPHER EXPORT")
    
    cypher = graph_builder.to_cypher()
    
    # Count statements
    merge_count = cypher.count("MERGE")
    match_count = cypher.count("MATCH")
    
    print(f"\n📝 Generated Cypher Script:")
    print(f"  MERGE statements: {merge_count}")
    print(f"  MATCH statements: {match_count}")
    
    print(f"\n📄 Sample Cypher (first 20 lines):")
    for line in cypher.split("\n")[:20]:
        if line.strip():
            print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
    
    # Save to file
    output_path = Path(__file__).parent.parent / "data" / "output" / "knowledge_graph.cypher"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(cypher)
    print(f"\n💾 Full Cypher saved to: {output_path}")


def main():
    """Run complete demonstration"""
    print("\n" + "=" * 70)
    print("  FINANCIAL IDR PIPELINE - COMPLETE DEMONSTRATION")
    print("  Ontology-Guided Intelligent Document Recognition")
    print("=" * 70)
    
    # 1. Company Registry
    demo_company_registry()
    
    # 2. Ontology Schema
    demo_ontology_schema()
    
    # 3. IDR Processing
    graph_builder = demo_idr_processing()
    
    # 4. GraphRAG Queries
    demo_graphrag_queries(graph_builder)
    
    # 5. Cypher Export
    demo_cypher_export(graph_builder)
    
    print_section("DEMONSTRATION COMPLETE")
    print("\n✅ All components demonstrated successfully!")
    print("\nNext Steps:")
    print("  1. Run: python main.py --demo")
    print("  2. Configure: config/config.yaml")
    print("  3. Process real 10-K PDFs from SEC EDGAR")
    print("  4. Import Cypher into Neo4j")
    print("  5. Query with GraphRAG")
    print()


if __name__ == "__main__":
    main()

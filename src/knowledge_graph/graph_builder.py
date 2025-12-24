"""
Knowledge Graph Builder Module
===============================

Builds and manages the knowledge graph from extracted entities and relations.
Supports Neo4j and in-memory graph storage.

Author: Rajesh Kumar Gupta
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from ..idr.entity_extractor import ExtractedEntity
from ..idr.relation_extractor import ExtractedRelation

logger = logging.getLogger(__name__)

# Try to import Neo4j driver
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Using in-memory graph only.")


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
        }


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph"""
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.type,
            "properties": self.properties,
        }


class KnowledgeGraphBuilder:
    """
    Builds and manages the knowledge graph.
    
    Features:
    - Node and edge creation from entities and relations
    - Cypher query generation for Neo4j
    - In-memory graph storage for testing
    - Graph statistics and analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.document_sources: Dict[str, Set[str]] = defaultdict(set)
        self._neo4j_driver = None
        
        if self.config.get("neo4j") and NEO4J_AVAILABLE:
            self._init_neo4j()
        
        logger.info("KnowledgeGraphBuilder initialized")
    
    def _init_neo4j(self) -> None:
        """Initialize Neo4j connection"""
        neo4j_config = self.config.get("neo4j", {})
        uri = neo4j_config.get("uri", "bolt://localhost:7687")
        user = neo4j_config.get("user", "neo4j")
        password = neo4j_config.get("password", "")
        
        try:
            self._neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            with self._neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._neo4j_driver = None
    
    def _generate_node_id(self, entity: ExtractedEntity) -> str:
        """Generate a unique ID for an entity"""
        text = entity.normalized_text or entity.text
        text_normalized = text.lower().replace(" ", "_").replace(".", "")
        hash_input = f"{entity.entity_type}_{text_normalized}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{entity.entity_type}_{text_normalized}_{short_hash}"
    
    def add_entity(self, entity: ExtractedEntity, document_id: Optional[str] = None) -> str:
        """Add an entity as a node in the graph."""
        node_id = self._generate_node_id(entity)
        
        if node_id not in self.nodes:
            labels = self._get_node_labels(entity)
            properties = {
                "id": node_id,
                "name": entity.normalized_text or entity.text,
                "original_text": entity.text,
                "entity_type": entity.entity_type,
                "confidence": entity.confidence,
                "created_at": datetime.now().isoformat(),
            }
            if entity.ontology_class:
                properties["ontology_class"] = entity.ontology_class
            properties.update(entity.properties)
            
            node = GraphNode(id=node_id, labels=labels, properties=properties)
            self.nodes[node_id] = node
        
        if document_id:
            self.document_sources[node_id].add(document_id)
            self.nodes[node_id].properties["source_documents"] = list(self.document_sources[node_id])
        
        return node_id
    
    def _get_node_labels(self, entity: ExtractedEntity) -> List[str]:
        """Get Neo4j labels for an entity"""
        labels = ["Entity", entity.entity_type]
        type_hierarchy = {
            "Revenue": ["FinancialMetric"],
            "NetIncome": ["FinancialMetric"],
            "EarningsPerShare": ["FinancialMetric"],
            "TotalAssets": ["FinancialMetric"],
            "CashFlow": ["FinancialMetric"],
            "SupplyChainRisk": ["Risk", "OperationalRisk"],
            "CurrencyRisk": ["Risk", "MarketRisk"],
            "RegulatoryRisk": ["Risk"],
            "GeopoliticalRisk": ["Risk"],
            "CompetitiveRisk": ["Risk"],
            "CybersecurityRisk": ["Risk", "OperationalRisk"],
            "TechnologyRisk": ["Risk"],
        }
        if entity.entity_type in type_hierarchy:
            labels.extend(type_hierarchy[entity.entity_type])
        return list(set(labels))
    
    def add_relation(self, relation: ExtractedRelation, document_id: Optional[str] = None) -> None:
        """Add a relation as an edge in the graph."""
        source_id = self.add_entity(relation.subject, document_id)
        target_id = self.add_entity(relation.object, document_id)
        
        properties = {
            "confidence": relation.confidence,
            "created_at": datetime.now().isoformat(),
        }
        if relation.ontology_property:
            properties["ontology_property"] = relation.ontology_property
        if relation.source_text:
            properties["evidence"] = relation.source_text[:500]
        if document_id:
            properties["source_document"] = document_id
        properties.update(relation.properties)
        
        edge = GraphEdge(source_id=source_id, target_id=target_id, type=relation.predicate, properties=properties)
        
        if not self._edge_exists(source_id, target_id, relation.predicate):
            self.edges.append(edge)
    
    def _edge_exists(self, source_id: str, target_id: str, edge_type: str) -> bool:
        """Check if edge already exists"""
        for edge in self.edges:
            if edge.source_id == source_id and edge.target_id == target_id and edge.type == edge_type:
                return True
        return False
    
    def add_entities(self, entities: List[ExtractedEntity], document_id: Optional[str] = None) -> List[str]:
        """Add multiple entities"""
        return [self.add_entity(e, document_id) for e in entities]
    
    def add_relations(self, relations: List[ExtractedRelation], document_id: Optional[str] = None) -> None:
        """Add multiple relations"""
        for relation in relations:
            self.add_relation(relation, document_id)
    
    def to_cypher(self) -> str:
        """Generate Cypher queries to create the knowledge graph."""
        queries = []
        queries.append("// Indexes and Constraints")
        queries.append("CREATE INDEX entity_id IF NOT EXISTS FOR (n:Entity) ON (n.id);")
        queries.append("CREATE INDEX company_name IF NOT EXISTS FOR (n:Company) ON (n.name);")
        queries.append("")
        queries.append("// Create Nodes")
        
        for node in self.nodes.values():
            labels = ":".join(node.labels)
            props = self._props_to_cypher(node.properties)
            query = f"MERGE (n:{labels} {{id: '{node.id}'}}) SET n += {props};"
            queries.append(query)
        
        queries.append("")
        queries.append("// Create Relationships")
        
        for edge in self.edges:
            props = self._props_to_cypher(edge.properties)
            query = f"""MATCH (a:Entity {{id: '{edge.source_id}'}})
MATCH (b:Entity {{id: '{edge.target_id}'}})
MERGE (a)-[r:{edge.type}]->(b)
SET r += {props};"""
            queries.append(query)
        
        return "\n".join(queries)
    
    def _props_to_cypher(self, properties: Dict) -> str:
        """Convert properties dictionary to Cypher format"""
        safe_props = {}
        for key, value in properties.items():
            if isinstance(value, str):
                safe_value = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
                safe_props[key] = f"'{safe_value}'"
            elif isinstance(value, bool):
                safe_props[key] = "true" if value else "false"
            elif isinstance(value, (int, float)):
                safe_props[key] = str(value)
            elif isinstance(value, list):
                items = [f"'{str(v)}'" for v in value]
                safe_props[key] = f"[{', '.join(items)}]"
        items = [f"{k}: {v}" for k, v in safe_props.items()]
        return "{" + ", ".join(items) + "}"
    
    def to_dict(self) -> Dict:
        """Export graph as dictionary"""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "statistics": self.get_statistics(),
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export graph as JSON"""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        stats = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": defaultdict(int),
            "edges_by_type": defaultdict(int),
        }
        for node in self.nodes.values():
            primary_label = node.labels[1] if len(node.labels) > 1 else node.labels[0]
            stats["nodes_by_type"][primary_label] += 1
        for edge in self.edges:
            stats["edges_by_type"][edge.type] += 1
        stats["nodes_by_type"] = dict(stats["nodes_by_type"])
        stats["edges_by_type"] = dict(stats["edges_by_type"])
        return stats
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, GraphNode]]:
        """Get neighboring nodes"""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.target_id in self.nodes:
                neighbors.append((edge.type, self.nodes[edge.target_id]))
            elif edge.target_id == node_id and edge.source_id in self.nodes:
                neighbors.append((edge.type, self.nodes[edge.source_id]))
        return neighbors
    
    def find_nodes_by_type(self, entity_type: str) -> List[GraphNode]:
        """Find all nodes of a specific type"""
        return [node for node in self.nodes.values() if entity_type in node.labels]
    
    def find_nodes_by_name(self, name: str, fuzzy: bool = False) -> List[GraphNode]:
        """Find nodes by name"""
        name_lower = name.lower()
        results = []
        for node in self.nodes.values():
            node_name = node.properties.get("name", "").lower()
            if fuzzy:
                if name_lower in node_name or node_name in name_lower:
                    results.append(node)
            else:
                if node_name == name_lower:
                    results.append(node)
        return results
    
    def clear(self) -> None:
        """Clear the graph"""
        self.nodes.clear()
        self.edges.clear()
        self.document_sources.clear()
    
    def close(self) -> None:
        """Close connections"""
        if self._neo4j_driver:
            self._neo4j_driver.close()

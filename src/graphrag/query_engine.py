"""
GraphRAG Query Engine Module
=============================

Combines graph-based retrieval with LLM generation for
question answering over the knowledge graph.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from ..knowledge_graph.graph_builder import KnowledgeGraphBuilder, GraphNode

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a GraphRAG query"""
    question: str
    answer: str
    cypher_query: str
    retrieved_nodes: List[Dict]
    retrieved_edges: List[Dict]
    context: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "cypher_query": self.cypher_query,
            "retrieved_nodes": self.retrieved_nodes,
            "retrieved_edges": self.retrieved_edges,
            "context": self.context[:1000] if self.context else "",
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class GraphRAGQueryEngine:
    """GraphRAG Query Engine - combines graph retrieval with LLM generation"""
    
    QUESTION_PATTERNS = {
        "risk": [r"(?:what|which)\s+(?:are\s+)?(?:the\s+)?(?:key\s+)?risks?", r"risk\s+factors?"],
        "financial": [r"(?:what\s+is|how\s+much)\s+(?:the\s+)?(?:revenue|sales|income)", r"financial\s+(?:performance|results)"],
        "competitor": [r"(?:who\s+are|what\s+are)\s+(?:the\s+)?competitors?", r"competes?\s+(?:with|against)"],
        "product": [r"(?:what|which)\s+(?:are\s+)?(?:the\s+)?products?"],
        "general": [r"(?:tell\s+me|what\s+do\s+you\s+know)\s+about"],
    }
    
    def __init__(self, graph: KnowledgeGraphBuilder, config: Optional[Dict[str, Any]] = None):
        self.graph = graph
        self.config = config or {}
        logger.info("GraphRAGQueryEngine initialized")
    
    def query(self, question: str) -> QueryResult:
        """Process a natural language query using GraphRAG."""
        question_type = self._classify_question(question)
        entities = self._extract_query_entities(question)
        cypher_query = self._generate_cypher_query(question, question_type, entities)
        subgraph = self._retrieve_subgraph(question_type, entities)
        context = self._format_context(subgraph, question_type)
        answer, confidence = self._generate_response(question, context, question_type)
        
        return QueryResult(
            question=question, answer=answer, cypher_query=cypher_query,
            retrieved_nodes=subgraph.get("nodes", []), retrieved_edges=subgraph.get("edges", []),
            context=context, confidence=confidence,
            metadata={"question_type": question_type, "entities_found": entities}
        )
    
    def _classify_question(self, question: str) -> str:
        question_lower = question.lower()
        for q_type, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return q_type
        return "general"
    
    def _extract_query_entities(self, question: str) -> List[str]:
        entities = []
        question_lower = question.lower()
        for node_id, node in self.graph.nodes.items():
            node_name = node.properties.get("name", "").lower()
            if node_name and len(node_name) > 2 and node_name in question_lower:
                entities.append(node_id)
        return entities
    
    def _generate_cypher_query(self, question: str, question_type: str, entities: List[str]) -> str:
        entity_filter = ""
        if entities:
            entity_list = ", ".join([f"'{e}'" for e in entities])
            entity_filter = f"WHERE n.id IN [{entity_list}]"
        
        templates = {
            "risk": f"MATCH (c:Company)-[r:FACES_RISK]->(risk:Risk)\n{entity_filter}\nRETURN c.name, risk.name, r.evidence LIMIT 20",
            "financial": f"MATCH (c:Company)-[r:REPORTED]->(m:FinancialMetric)\n{entity_filter}\nRETURN c.name, m.name, m.value LIMIT 20",
            "competitor": f"MATCH (c1:Company)-[r:COMPETES_WITH]-(c2:Company)\n{entity_filter}\nRETURN c1.name, c2.name LIMIT 20",
            "product": f"MATCH (c:Company)-[r:MANUFACTURES|SELLS]->(p:Product)\n{entity_filter}\nRETURN c.name, p.name LIMIT 20",
        }
        return templates.get(question_type, f"MATCH (n)-[r]-(m)\n{entity_filter}\nRETURN n, r, m LIMIT 30")
    
    def _retrieve_subgraph(self, question_type: str, entity_ids: List[str]) -> Dict[str, List]:
        nodes, edges, seen_nodes = [], [], set()
        
        for entity_id in entity_ids:
            node = self.graph.get_node(entity_id)
            if node and entity_id not in seen_nodes:
                nodes.append(node.to_dict())
                seen_nodes.add(entity_id)
        
        for entity_id in entity_ids:
            for rel_type, neighbor in self.graph.get_neighbors(entity_id):
                if neighbor.id not in seen_nodes:
                    nodes.append(neighbor.to_dict())
                    seen_nodes.add(neighbor.id)
        
        for edge in self.graph.edges:
            if edge.source_id in seen_nodes and edge.target_id in seen_nodes:
                edges.append(edge.to_dict())
        
        if not entity_ids:
            type_map = {"risk": "Risk", "financial": "FinancialMetric", "competitor": "Company", "product": "Product"}
            for node in self.graph.find_nodes_by_type(type_map.get(question_type, "Entity"))[:10]:
                if node.id not in seen_nodes:
                    nodes.append(node.to_dict())
        
        return {"nodes": nodes, "edges": edges}
    
    def _format_context(self, subgraph: Dict, question_type: str) -> str:
        lines = ["=== KNOWLEDGE GRAPH CONTEXT ===", "", "ENTITIES:"]
        for node in subgraph.get("nodes", [])[:15]:
            name = node["properties"].get("name", "Unknown")
            node_type = node["properties"].get("entity_type", "Unknown")
            lines.append(f"  - {name} ({node_type})")
            if "value" in node["properties"]:
                lines.append(f"      value: {node['properties']['value']}")
        
        lines.append("\nRELATIONSHIPS:")
        for edge in subgraph.get("edges", [])[:15]:
            source = edge.get("source", "").split("_")[1] if "_" in edge.get("source", "") else edge.get("source")
            target = edge.get("target", "").split("_")[1] if "_" in edge.get("target", "") else edge.get("target")
            lines.append(f"  - {source} --[{edge.get('type')}]--> {target}")
            evidence = edge.get("properties", {}).get("evidence", "")
            if evidence:
                lines.append(f"      Evidence: \"{evidence[:100]}...\"")
        
        return "\n".join(lines)
    
    def _generate_response(self, question: str, context: str, question_type: str) -> Tuple[str, float]:
        """Generate template-based response"""
        lines = context.split("\n")
        entities = [l.strip()[2:] for l in lines if l.strip().startswith("- ") and "ENTITIES" in context[:context.find(l)]]
        relationships = [l.strip()[2:] for l in lines if l.strip().startswith("- ") and "--[" in l]
        
        response = f"Based on the knowledge graph analysis:\n\n"
        if entities:
            response += "Entities identified:\n" + "\n".join([f"• {e}" for e in entities[:5]]) + "\n\n"
        if relationships:
            response += "Relationships found:\n" + "\n".join([f"• {r}" for r in relationships[:5]])
        
        return response if entities or relationships else "No relevant information found.", 0.7 if entities else 0.3

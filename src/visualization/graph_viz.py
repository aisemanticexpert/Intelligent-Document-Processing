"""
Graph Visualization Module
===========================

Generates visualizations of the knowledge graph in various formats:
- NetworkX + Matplotlib
- Plotly interactive graphs
- D3.js compatible JSON
- Graphviz DOT format

Author: Rajesh Kumar Gupta
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import visualization libraries
NETWORKX_AVAILABLE = False
MATPLOTLIB_AVAILABLE = False
PLOTLY_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    pass

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# COLOR SCHEMES
# =============================================================================

NODE_COLORS = {
    "Company": "#4CAF50",      # Green
    "Person": "#2196F3",       # Blue
    "Product": "#FF9800",      # Orange
    "Revenue": "#9C27B0",      # Purple
    "NetIncome": "#9C27B0",
    "EarningsPerShare": "#9C27B0",
    "FinancialMetric": "#9C27B0",
    "MonetaryAmount": "#9C27B0",
    "Risk": "#F44336",         # Red
    "SupplyChainRisk": "#F44336",
    "CurrencyRisk": "#F44336",
    "RegulatoryRisk": "#F44336",
    "GeopoliticalRisk": "#F44336",
    "CompetitiveRisk": "#F44336",
    "CybersecurityRisk": "#F44336",
    "EconomicIndicator": "#607D8B",  # Gray-blue
    "Date": "#795548",         # Brown
    "Percentage": "#00BCD4",   # Cyan
    "default": "#9E9E9E",      # Gray
}

EDGE_COLORS = {
    "FACES_RISK": "#F44336",
    "COMPETES_WITH": "#FF5722",
    "REPORTED": "#4CAF50",
    "GENERATED": "#4CAF50",
    "CEO_OF": "#2196F3",
    "WORKS_AT": "#2196F3",
    "MANUFACTURES": "#FF9800",
    "ACQUIRED": "#9C27B0",
    "PARTNERS_WITH": "#00BCD4",
    "default": "#9E9E9E",
}


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization"""
    width: int = 1200
    height: int = 800
    node_size_min: int = 20
    node_size_max: int = 50
    font_size: int = 10
    show_labels: bool = True
    show_edge_labels: bool = False
    layout: str = "spring"  # spring, circular, kamada_kawai, hierarchical
    title: str = "Financial Knowledge Graph"


class GraphVisualizer:
    """
    Knowledge Graph Visualizer
    
    Features:
    - Multiple output formats (PNG, HTML, JSON, DOT)
    - Customizable layouts
    - Interactive Plotly graphs
    - Color coding by entity type
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        logger.info("GraphVisualizer initialized")
    
    def create_networkx_graph(self, graph_data: Dict) -> Optional[Any]:
        """Create NetworkX graph from graph data"""
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available")
            return None
        
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data.get("nodes", []):
            node_id = node.get("id", "")
            properties = node.get("properties", {})
            labels = node.get("labels", [])
            
            G.add_node(
                node_id,
                label=properties.get("name", node_id),
                entity_type=properties.get("entity_type", "unknown"),
                labels=labels,
                **properties,
            )
        
        # Add edges
        for edge in graph_data.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            edge_type = edge.get("type", "RELATED_TO")
            properties = edge.get("properties", {})
            
            G.add_edge(
                source, target,
                type=edge_type,
                **properties,
            )
        
        return G
    
    def get_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """Get node positions based on layout algorithm"""
        if not NETWORKX_AVAILABLE:
            return {}
        
        if self.config.layout == "spring":
            return nx.spring_layout(G, k=2, iterations=50, seed=42)
        elif self.config.layout == "circular":
            return nx.circular_layout(G)
        elif self.config.layout == "kamada_kawai":
            try:
                return nx.kamada_kawai_layout(G)
            except:
                return nx.spring_layout(G, seed=42)
        elif self.config.layout == "hierarchical":
            try:
                return nx.multipartite_layout(G, subset_key="entity_type")
            except:
                return nx.spring_layout(G, seed=42)
        else:
            return nx.spring_layout(G, seed=42)
    
    def render_matplotlib(
        self, 
        graph_data: Dict, 
        output_path: Optional[str] = None,
        figsize: Tuple[int, int] = (16, 12),
    ) -> Optional[str]:
        """Render graph using matplotlib"""
        if not NETWORKX_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            logger.warning("NetworkX or Matplotlib not available")
            return None
        
        G = self.create_networkx_graph(graph_data)
        if G is None or len(G.nodes()) == 0:
            logger.warning("Empty graph, nothing to visualize")
            return None
        
        pos = self.get_layout(G)
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title(self.config.title, fontsize=16, fontweight='bold')
        
        # Group nodes by type for coloring
        node_groups = defaultdict(list)
        for node, data in G.nodes(data=True):
            entity_type = data.get("entity_type", "default")
            node_groups[entity_type].append(node)
        
        # Draw nodes by group
        for entity_type, nodes in node_groups.items():
            color = NODE_COLORS.get(entity_type, NODE_COLORS["default"])
            nx.draw_networkx_nodes(
                G, pos, nodelist=nodes,
                node_color=color,
                node_size=self.config.node_size_max * 10,
                alpha=0.8,
                ax=ax,
            )
        
        # Draw edges
        edge_colors = []
        for u, v, data in G.edges(data=True):
            edge_type = data.get("type", "default")
            edge_colors.append(EDGE_COLORS.get(edge_type, EDGE_COLORS["default"]))
        
        nx.draw_networkx_edges(
            G, pos,
            edge_color=edge_colors,
            alpha=0.6,
            arrows=True,
            arrowsize=15,
            ax=ax,
        )
        
        # Draw labels
        if self.config.show_labels:
            labels = {n: d.get("label", n)[:20] for n, d in G.nodes(data=True)}
            nx.draw_networkx_labels(
                G, pos, labels,
                font_size=self.config.font_size,
                ax=ax,
            )
        
        # Create legend
        legend_patches = []
        for entity_type, color in NODE_COLORS.items():
            if entity_type in node_groups and entity_type != "default":
                patch = mpatches.Patch(color=color, label=entity_type)
                legend_patches.append(patch)
        
        if legend_patches:
            ax.legend(handles=legend_patches[:10], loc='upper left', fontsize=8)
        
        ax.axis('off')
        plt.tight_layout()
        
        # Save or show
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info(f"Graph saved to {output_path}")
            return output_path
        else:
            plt.show()
            return None
    
    def render_plotly(
        self, 
        graph_data: Dict, 
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Render interactive graph using Plotly"""
        if not NETWORKX_AVAILABLE or not PLOTLY_AVAILABLE:
            logger.warning("NetworkX or Plotly not available")
            return None
        
        G = self.create_networkx_graph(graph_data)
        if G is None or len(G.nodes()) == 0:
            return None
        
        pos = self.get_layout(G)
        
        # Create edge traces
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines',
        )
        
        # Create node traces (grouped by type)
        node_traces = []
        node_groups = defaultdict(list)
        
        for node, data in G.nodes(data=True):
            entity_type = data.get("entity_type", "default")
            node_groups[entity_type].append((node, data))
        
        for entity_type, nodes in node_groups.items():
            node_x = [pos[n[0]][0] for n in nodes]
            node_y = [pos[n[0]][1] for n in nodes]
            node_text = [n[1].get("label", n[0]) for n in nodes]
            
            color = NODE_COLORS.get(entity_type, NODE_COLORS["default"])
            
            trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                textfont=dict(size=10),
                name=entity_type,
                marker=dict(
                    color=color,
                    size=15,
                    line=dict(width=2, color='white'),
                ),
            )
            node_traces.append(trace)
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace] + node_traces,
            layout=go.Layout(
                title=dict(text=self.config.title, font=dict(size=20)),
                showlegend=True,
                hovermode='closest',
                width=self.config.width,
                height=self.config.height,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
            ),
        )
        
        if output_path:
            fig.write_html(output_path)
            logger.info(f"Interactive graph saved to {output_path}")
            return output_path
        else:
            fig.show()
            return None
    
    def to_d3_json(self, graph_data: Dict) -> Dict:
        """Convert to D3.js compatible JSON format"""
        d3_data = {
            "nodes": [],
            "links": [],
        }
        
        node_id_map = {}
        
        for i, node in enumerate(graph_data.get("nodes", [])):
            node_id = node.get("id", "")
            properties = node.get("properties", {})
            entity_type = properties.get("entity_type", "unknown")
            
            d3_node = {
                "id": node_id,
                "name": properties.get("name", node_id),
                "group": entity_type,
                "color": NODE_COLORS.get(entity_type, NODE_COLORS["default"]),
                "size": 10,
            }
            d3_data["nodes"].append(d3_node)
            node_id_map[node_id] = i
        
        for edge in graph_data.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            edge_type = edge.get("type", "RELATED_TO")
            
            if source in node_id_map and target in node_id_map:
                d3_link = {
                    "source": source,
                    "target": target,
                    "type": edge_type,
                    "color": EDGE_COLORS.get(edge_type, EDGE_COLORS["default"]),
                }
                d3_data["links"].append(d3_link)
        
        return d3_data
    
    def to_dot(self, graph_data: Dict) -> str:
        """Convert to Graphviz DOT format"""
        lines = [
            "digraph FinancialKnowledgeGraph {",
            f'    label="{self.config.title}";',
            "    rankdir=LR;",
            "    node [style=filled, fontname=Arial];",
            "    edge [fontname=Arial, fontsize=10];",
            "",
        ]
        
        # Add node definitions
        for node in graph_data.get("nodes", []):
            node_id = node.get("id", "").replace("-", "_")
            properties = node.get("properties", {})
            entity_type = properties.get("entity_type", "unknown")
            label = properties.get("name", node_id)[:30]
            color = NODE_COLORS.get(entity_type, NODE_COLORS["default"])
            
            lines.append(f'    "{node_id}" [label="{label}", fillcolor="{color}"];')
        
        lines.append("")
        
        # Add edge definitions
        for edge in graph_data.get("edges", []):
            source = edge.get("source", "").replace("-", "_")
            target = edge.get("target", "").replace("-", "_")
            edge_type = edge.get("type", "RELATED_TO")
            color = EDGE_COLORS.get(edge_type, EDGE_COLORS["default"])
            
            lines.append(f'    "{source}" -> "{target}" [label="{edge_type}", color="{color}"];')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def save_all_formats(
        self, 
        graph_data: Dict, 
        output_dir: str,
        base_name: str = "knowledge_graph",
    ) -> Dict[str, str]:
        """Save graph in all available formats"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        # JSON (D3 format)
        json_path = output_dir / f"{base_name}_d3.json"
        with open(json_path, 'w') as f:
            json.dump(self.to_d3_json(graph_data), f, indent=2)
        outputs["json"] = str(json_path)
        
        # DOT format
        dot_path = output_dir / f"{base_name}.dot"
        with open(dot_path, 'w') as f:
            f.write(self.to_dot(graph_data))
        outputs["dot"] = str(dot_path)
        
        # Matplotlib PNG
        if NETWORKX_AVAILABLE and MATPLOTLIB_AVAILABLE:
            png_path = output_dir / f"{base_name}.png"
            self.render_matplotlib(graph_data, str(png_path))
            outputs["png"] = str(png_path)
        
        # Plotly HTML
        if NETWORKX_AVAILABLE and PLOTLY_AVAILABLE:
            html_path = output_dir / f"{base_name}_interactive.html"
            self.render_plotly(graph_data, str(html_path))
            outputs["html"] = str(html_path)
        
        logger.info(f"Saved graph to: {outputs}")
        return outputs


# =============================================================================
# GRAPH STATISTICS VISUALIZER
# =============================================================================

class GraphStatsVisualizer:
    """Visualize graph statistics"""
    
    @staticmethod
    def plot_entity_distribution(
        stats: Dict,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Plot distribution of entity types"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        nodes_by_type = stats.get("nodes_by_type", {})
        if not nodes_by_type:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        types = list(nodes_by_type.keys())
        counts = list(nodes_by_type.values())
        colors = [NODE_COLORS.get(t, NODE_COLORS["default"]) for t in types]
        
        bars = ax.barh(types, counts, color=colors)
        ax.set_xlabel("Count")
        ax.set_title("Entity Type Distribution")
        
        # Add count labels
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   str(count), va='center', fontsize=10)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    @staticmethod
    def plot_relation_distribution(
        stats: Dict,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Plot distribution of relation types"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        edges_by_type = stats.get("edges_by_type", {})
        if not edges_by_type:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        types = list(edges_by_type.keys())
        counts = list(edges_by_type.values())
        colors = [EDGE_COLORS.get(t, EDGE_COLORS["default"]) for t in types]
        
        ax.pie(counts, labels=types, colors=colors, autopct='%1.1f%%',
               startangle=90, explode=[0.02]*len(types))
        ax.set_title("Relation Type Distribution")
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None

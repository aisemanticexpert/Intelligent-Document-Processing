"""
Financial IDR Pipeline
=======================

Intelligent Document Recognition for Financial Documents.

Components:
- data_sources: Fetch documents from SEC EDGAR, FRED, etc.
- idr: Document classification, entity extraction, relation extraction
- knowledge_graph: Build and manage knowledge graphs
- graphrag: Query knowledge graph using GraphRAG
- pipeline: Main orchestration module

Author: Rajesh Kumar Gupta
Version: 1.0.0
"""

from .pipeline.idr_pipeline import FinancialIDRPipeline, create_pipeline_from_config

__version__ = "1.0.0"
__author__ = "Rajesh Kumar Gupta"

__all__ = [
    "FinancialIDRPipeline",
    "create_pipeline_from_config",
]

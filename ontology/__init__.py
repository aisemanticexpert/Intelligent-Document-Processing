"""Ontology Module"""
from .namespaces import (
    SEI, SEI_CO, SEI_FIN, SEI_DOC, SEI_RISK, SEI_ECON,
    FinancialOntologySchema, CompanyClass, FinancialClass, RiskClass
)

__all__ = [
    "SEI", "SEI_CO", "SEI_FIN", "SEI_DOC", "SEI_RISK", "SEI_ECON",
    "FinancialOntologySchema", "CompanyClass", "FinancialClass", "RiskClass"
]

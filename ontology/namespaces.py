"""
Semantic Expert AI - Financial IDR Ontology Namespaces
======================================================

This module defines RDF namespaces for the Financial IDR Ontology,
providing programmatic access to ontology classes, properties, and relationships.

Author: Rajesh Kumar Gupta
Version: 1.0.0
"""

from rdflib import Namespace, URIRef, RDF, RDFS, OWL, XSD
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# NAMESPACE DEFINITIONS
# =============================================================================

# Standard Namespaces
RDF_NS = RDF
RDFS_NS = RDFS
OWL_NS = OWL
XSD_NS = XSD
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

# FIBO Namespaces (for alignment)
FIBO_FND = Namespace("https://spec.edmcouncil.org/fibo/ontology/FND/")
FIBO_BE = Namespace("https://spec.edmcouncil.org/fibo/ontology/BE/")
FIBO_SEC = Namespace("https://spec.edmcouncil.org/fibo/ontology/SEC/")

# Semantic Expert AI Namespaces
SEI = Namespace("http://www.semanticexpert.ai/ontology/")
SEI_CO = Namespace("http://www.semanticexpert.ai/ontology/company#")
SEI_FIN = Namespace("http://www.semanticexpert.ai/ontology/financial#")
SEI_DOC = Namespace("http://www.semanticexpert.ai/ontology/document#")
SEI_RISK = Namespace("http://www.semanticexpert.ai/ontology/risk#")
SEI_ECON = Namespace("http://www.semanticexpert.ai/ontology/economic#")

# All namespaces dictionary for binding
NAMESPACE_BINDINGS = {
    "rdf": RDF_NS,
    "rdfs": RDFS_NS,
    "owl": OWL_NS,
    "xsd": XSD_NS,
    "skos": SKOS,
    "dcterms": DCTERMS,
    "fibo-fnd": FIBO_FND,
    "fibo-be": FIBO_BE,
    "fibo-sec": FIBO_SEC,
    "sei": SEI,
    "sei-co": SEI_CO,
    "sei-fin": SEI_FIN,
    "sei-doc": SEI_DOC,
    "sei-risk": SEI_RISK,
    "sei-econ": SEI_ECON,
}


# =============================================================================
# ONTOLOGY CLASS ENUMERATIONS
# =============================================================================

class CompanyClass(Enum):
    """Company-related ontology classes"""
    ORGANIZATION = SEI_CO["Organization"]
    COMPANY = SEI_CO["Company"]
    PUBLIC_COMPANY = SEI_CO["PublicCompany"]
    PRIVATE_COMPANY = SEI_CO["PrivateCompany"]
    SUBSIDIARY = SEI_CO["Subsidiary"]
    SUPPLIER = SEI_CO["Supplier"]
    COMPETITOR = SEI_CO["Competitor"]


class SectorClass(Enum):
    """Industry sector classes"""
    INDUSTRY_SECTOR = SEI_CO["IndustrySector"]
    TECHNOLOGY = SEI_CO["TechnologySector"]
    HEALTHCARE = SEI_CO["HealthcareSector"]
    FINANCIAL = SEI_CO["FinancialSector"]
    CONSUMER = SEI_CO["ConsumerSector"]
    ENERGY = SEI_CO["EnergySector"]
    INDUSTRIALS = SEI_CO["IndustrialsSector"]


class FinancialClass(Enum):
    """Financial instrument and metric classes"""
    FINANCIAL_INSTRUMENT = SEI_FIN["FinancialInstrument"]
    SECURITY = SEI_FIN["Security"]
    EQUITY = SEI_FIN["Equity"]
    COMMON_STOCK = SEI_FIN["CommonStock"]
    PREFERRED_STOCK = SEI_FIN["PreferredStock"]
    BOND = SEI_FIN["Bond"]
    DERIVATIVE = SEI_FIN["Derivative"]
    
    # Metrics
    FINANCIAL_METRIC = SEI_FIN["FinancialMetric"]
    REVENUE = SEI_FIN["Revenue"]
    NET_INCOME = SEI_FIN["NetIncome"]
    GROSS_PROFIT = SEI_FIN["GrossProfit"]
    OPERATING_INCOME = SEI_FIN["OperatingIncome"]
    EBITDA = SEI_FIN["EBITDA"]
    EPS = SEI_FIN["EarningsPerShare"]
    TOTAL_ASSETS = SEI_FIN["TotalAssets"]
    TOTAL_LIABILITIES = SEI_FIN["TotalLiabilities"]
    SHAREHOLDERS_EQUITY = SEI_FIN["ShareholdersEquity"]
    CASH_FLOW = SEI_FIN["CashFlow"]
    OPERATING_CASH_FLOW = SEI_FIN["OperatingCashFlow"]
    FREE_CASH_FLOW = SEI_FIN["FreeCashFlow"]
    
    # Ratios
    FINANCIAL_RATIO = SEI_FIN["FinancialRatio"]
    PE_RATIO = SEI_FIN["PriceToEarnings"]
    DEBT_TO_EQUITY = SEI_FIN["DebtToEquity"]
    ROE = SEI_FIN["ReturnOnEquity"]
    ROA = SEI_FIN["ReturnOnAssets"]


class DocumentClass(Enum):
    """Document-related classes"""
    DOCUMENT = SEI_DOC["Document"]
    REGULATORY_FILING = SEI_DOC["RegulatoryFiling"]
    SEC_FILING = SEI_DOC["SECFiling"]
    FORM_10K = SEI_DOC["Form10K"]
    FORM_10Q = SEI_DOC["Form10Q"]
    FORM_8K = SEI_DOC["Form8K"]
    PROXY_STATEMENT = SEI_DOC["ProxyStatement"]
    EQUITY_RESEARCH = SEI_DOC["EquityResearchReport"]
    EARNINGS_CALL = SEI_DOC["EarningsCallTranscript"]
    PRESS_RELEASE = SEI_DOC["PressRelease"]
    
    # Sections
    DOCUMENT_SECTION = SEI_DOC["DocumentSection"]
    BUSINESS_DESCRIPTION = SEI_DOC["BusinessDescription"]
    RISK_FACTORS = SEI_DOC["RiskFactors"]
    MD_AND_A = SEI_DOC["ManagementDiscussion"]
    FINANCIAL_STATEMENTS = SEI_DOC["FinancialStatements"]


class RiskClass(Enum):
    """Risk-related classes"""
    RISK = SEI_RISK["Risk"]
    OPERATIONAL_RISK = SEI_RISK["OperationalRisk"]
    SUPPLY_CHAIN_RISK = SEI_RISK["SupplyChainRisk"]
    CYBERSECURITY_RISK = SEI_RISK["CybersecurityRisk"]
    FINANCIAL_RISK = SEI_RISK["FinancialRisk"]
    CREDIT_RISK = SEI_RISK["CreditRisk"]
    LIQUIDITY_RISK = SEI_RISK["LiquidityRisk"]
    MARKET_RISK = SEI_RISK["MarketRisk"]
    CURRENCY_RISK = SEI_RISK["CurrencyRisk"]
    INTEREST_RATE_RISK = SEI_RISK["InterestRateRisk"]
    REGULATORY_RISK = SEI_RISK["RegulatoryRisk"]
    GEOPOLITICAL_RISK = SEI_RISK["GeopoliticalRisk"]
    COMPETITIVE_RISK = SEI_RISK["CompetitiveRisk"]
    TECHNOLOGY_RISK = SEI_RISK["TechnologyRisk"]
    REPUTATIONAL_RISK = SEI_RISK["ReputationalRisk"]
    ENVIRONMENTAL_RISK = SEI_RISK["EnvironmentalRisk"]


class EconomicClass(Enum):
    """Economic indicator classes"""
    ECONOMIC_INDICATOR = SEI_ECON["EconomicIndicator"]
    MACRO_INDICATOR = SEI_ECON["MacroeconomicIndicator"]
    GDP = SEI_ECON["GDP"]
    INFLATION_RATE = SEI_ECON["InflationRate"]
    UNEMPLOYMENT_RATE = SEI_ECON["UnemploymentRate"]
    INTEREST_RATE = SEI_ECON["InterestRate"]
    FED_FUNDS_RATE = SEI_ECON["FederalFundsRate"]
    CONSUMER_CONFIDENCE = SEI_ECON["ConsumerConfidence"]
    PMI = SEI_ECON["PMI"]
    TRADE_BALANCE = SEI_ECON["TradeBalance"]


# =============================================================================
# ONTOLOGY PROPERTY ENUMERATIONS
# =============================================================================

class ObjectProperty(Enum):
    """Object properties (relationships)"""
    # Company relationships
    HAS_SUBSIDIARY = SEI_CO["hasSubsidiary"]
    IS_SUBSIDIARY_OF = SEI_CO["isSubsidiaryOf"]
    COMPETES_WITH = SEI_CO["competesWith"]
    PARTNERS_WITH = SEI_CO["partnersWith"]
    ACQUIRED = SEI_CO["acquired"]
    SUPPLIES_TO = SEI_CO["suppliesTo"]
    BELONGS_TO_SECTOR = SEI_CO["belongsToSector"]
    
    # Financial relationships
    HAS_FINANCIAL_METRIC = SEI_FIN["hasFinancialMetric"]
    REPORTED_IN = SEI_FIN["reportedIn"]
    HAS_SECURITY = SEI_FIN["hasSecurity"]
    
    # Document relationships
    FILED_BY = SEI_DOC["filedBy"]
    HAS_SECTION = SEI_DOC["hasSection"]
    MENTIONS_ENTITY = SEI_DOC["mentionsEntity"]
    CONTAINS_METRIC = SEI_DOC["containsMetric"]
    
    # Risk relationships
    FACES_RISK = SEI_RISK["facesRisk"]
    DISCLOSED_IN = SEI_RISK["disclosedIn"]
    AFFECTS_METRIC = SEI_RISK["affectsMetric"]
    
    # Economic relationships
    IMPACTED_BY = SEI_ECON["impactedBy"]
    CORRELATES_WITH = SEI_ECON["correlatesWith"]


class DataProperty(Enum):
    """Data properties"""
    # Company properties
    TICKER = SEI_CO["ticker"]
    CIK = SEI_CO["cik"]
    COMPANY_NAME = SEI_CO["companyName"]
    HEADQUARTERS = SEI_CO["headquarters"]
    FOUNDED_YEAR = SEI_CO["foundedYear"]
    EMPLOYEE_COUNT = SEI_CO["employeeCount"]
    
    # Financial properties
    VALUE = SEI_FIN["value"]
    CURRENCY = SEI_FIN["currency"]
    FISCAL_YEAR = SEI_FIN["fiscalYear"]
    FISCAL_QUARTER = SEI_FIN["fiscalQuarter"]
    REPORTING_DATE = SEI_FIN["reportingDate"]
    
    # Document properties
    FILING_DATE = SEI_DOC["filingDate"]
    ACCESSION_NUMBER = SEI_DOC["accessionNumber"]
    DOCUMENT_URL = SEI_DOC["documentUrl"]
    EXTRACTED_TEXT = SEI_DOC["extractedText"]
    
    # Risk properties
    SEVERITY = SEI_RISK["severity"]
    LIKELIHOOD = SEI_RISK["likelihood"]
    RISK_DESCRIPTION = SEI_RISK["riskDescription"]
    
    # Economic properties
    INDICATOR_VALUE = SEI_ECON["indicatorValue"]
    OBSERVATION_DATE = SEI_ECON["observationDate"]
    DATA_SOURCE = SEI_ECON["dataSource"]


# =============================================================================
# ONTOLOGY SCHEMA DEFINITION
# =============================================================================

@dataclass
class OntologyClassDef:
    """Definition of an ontology class"""
    uri: URIRef
    label: str
    parent: Optional[URIRef] = None
    description: str = ""
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class FinancialOntologySchema:
    """
    Complete schema definition for the Financial IDR Ontology.
    Provides programmatic access to all classes, properties, and relationships.
    """
    
    def __init__(self):
        self._build_class_hierarchy()
        self._build_relationship_constraints()
        self._build_entity_patterns()
    
    def _build_class_hierarchy(self):
        """Build the class hierarchy map"""
        self.class_hierarchy: Dict[URIRef, List[URIRef]] = {
            # Company hierarchy
            CompanyClass.ORGANIZATION.value: [],
            CompanyClass.COMPANY.value: [CompanyClass.ORGANIZATION.value],
            CompanyClass.PUBLIC_COMPANY.value: [CompanyClass.COMPANY.value],
            CompanyClass.PRIVATE_COMPANY.value: [CompanyClass.COMPANY.value],
            CompanyClass.SUBSIDIARY.value: [CompanyClass.COMPANY.value],
            
            # Financial hierarchy
            FinancialClass.FINANCIAL_METRIC.value: [],
            FinancialClass.REVENUE.value: [FinancialClass.FINANCIAL_METRIC.value],
            FinancialClass.NET_INCOME.value: [FinancialClass.FINANCIAL_METRIC.value],
            FinancialClass.EBITDA.value: [FinancialClass.FINANCIAL_METRIC.value],
            
            # Risk hierarchy
            RiskClass.RISK.value: [],
            RiskClass.OPERATIONAL_RISK.value: [RiskClass.RISK.value],
            RiskClass.SUPPLY_CHAIN_RISK.value: [RiskClass.OPERATIONAL_RISK.value],
            RiskClass.FINANCIAL_RISK.value: [RiskClass.RISK.value],
            RiskClass.MARKET_RISK.value: [RiskClass.FINANCIAL_RISK.value],
            
            # Document hierarchy
            DocumentClass.DOCUMENT.value: [],
            DocumentClass.SEC_FILING.value: [DocumentClass.REGULATORY_FILING.value],
            DocumentClass.FORM_10K.value: [DocumentClass.SEC_FILING.value],
            DocumentClass.FORM_10Q.value: [DocumentClass.SEC_FILING.value],
        }
    
    def _build_relationship_constraints(self):
        """Define valid relationships between entity types"""
        self.valid_relationships: Dict[tuple, List[URIRef]] = {
            # Company -> Company relationships
            (CompanyClass.COMPANY.value, CompanyClass.COMPANY.value): [
                ObjectProperty.COMPETES_WITH.value,
                ObjectProperty.PARTNERS_WITH.value,
                ObjectProperty.ACQUIRED.value,
            ],
            # Company -> Subsidiary
            (CompanyClass.COMPANY.value, CompanyClass.SUBSIDIARY.value): [
                ObjectProperty.HAS_SUBSIDIARY.value,
            ],
            # Company -> Sector
            (CompanyClass.COMPANY.value, SectorClass.INDUSTRY_SECTOR.value): [
                ObjectProperty.BELONGS_TO_SECTOR.value,
            ],
            # Company -> Risk
            (CompanyClass.COMPANY.value, RiskClass.RISK.value): [
                ObjectProperty.FACES_RISK.value,
            ],
            # Company -> FinancialMetric
            (CompanyClass.COMPANY.value, FinancialClass.FINANCIAL_METRIC.value): [
                ObjectProperty.HAS_FINANCIAL_METRIC.value,
            ],
            # Document -> Company
            (DocumentClass.SEC_FILING.value, CompanyClass.PUBLIC_COMPANY.value): [
                ObjectProperty.FILED_BY.value,
            ],
            # FinancialMetric -> Document
            (FinancialClass.FINANCIAL_METRIC.value, DocumentClass.DOCUMENT.value): [
                ObjectProperty.REPORTED_IN.value,
            ],
        }
    
    def _build_entity_patterns(self):
        """Build NER patterns for entity extraction"""
        self.entity_patterns = {
            # Company patterns
            "Company": {
                "class": CompanyClass.PUBLIC_COMPANY.value,
                "patterns": [
                    r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s(?:Inc\.|Corp\.|Corporation|Ltd\.|LLC|Company|Co\.)\b",
                    r"\b(Apple|Google|Microsoft|Amazon|Tesla|Meta|NVIDIA|AMD|Intel|IBM)\b",
                ],
                "aliases": ["company", "corporation", "firm", "enterprise"]
            },
            
            # Financial Metric patterns
            "Revenue": {
                "class": FinancialClass.REVENUE.value,
                "patterns": [
                    r"(?:total\s+)?revenue(?:s)?\s+(?:of\s+)?\$?([\d,\.]+)\s*(billion|million|B|M)?",
                    r"(?:net\s+)?sales\s+(?:of\s+)?\$?([\d,\.]+)\s*(billion|million|B|M)?",
                ],
                "aliases": ["sales", "net sales", "total revenue"]
            },
            
            "NetIncome": {
                "class": FinancialClass.NET_INCOME.value,
                "patterns": [
                    r"net\s+income\s+(?:of\s+)?\$?([\d,\.]+)\s*(billion|million|B|M)?",
                    r"(?:net\s+)?(?:profit|earnings)\s+(?:of\s+)?\$?([\d,\.]+)\s*(billion|million|B|M)?",
                ],
                "aliases": ["profit", "earnings", "net profit", "net earnings"]
            },
            
            # Risk patterns
            "SupplyChainRisk": {
                "class": RiskClass.SUPPLY_CHAIN_RISK.value,
                "patterns": [
                    r"supply\s+chain\s+(?:risk|disruption|challenge|issue)",
                    r"(?:manufacturing|production|logistics)\s+(?:risk|disruption)",
                    r"(?:supplier|vendor)\s+(?:concentration|dependency|risk)",
                ],
                "aliases": ["supply chain disruption", "supplier risk", "logistics risk"]
            },
            
            "CurrencyRisk": {
                "class": RiskClass.CURRENCY_RISK.value,
                "patterns": [
                    r"(?:currency|foreign\s+exchange|fx)\s+(?:risk|exposure|fluctuation)",
                    r"exchange\s+rate\s+(?:risk|volatility|exposure)",
                ],
                "aliases": ["fx risk", "foreign exchange risk", "currency exposure"]
            },
            
            "RegulatoryRisk": {
                "class": RiskClass.REGULATORY_RISK.value,
                "patterns": [
                    r"regulatory\s+(?:risk|compliance|change|uncertainty)",
                    r"(?:government|legal|legislative)\s+(?:risk|action|change)",
                ],
                "aliases": ["compliance risk", "legal risk", "government risk"]
            },
            
            "GeopoliticalRisk": {
                "class": RiskClass.GEOPOLITICAL_RISK.value,
                "patterns": [
                    r"geopolitical\s+(?:risk|tension|uncertainty|event)",
                    r"(?:trade\s+war|tariff|sanction|political\s+instability)",
                ],
                "aliases": ["political risk", "trade risk", "international risk"]
            },
            
            "CompetitiveRisk": {
                "class": RiskClass.COMPETITIVE_RISK.value,
                "patterns": [
                    r"competitive?\s+(?:risk|pressure|threat|environment)",
                    r"(?:market|industry)\s+competition",
                ],
                "aliases": ["competition risk", "market competition"]
            },
        }
    
    def get_class_parents(self, class_uri: URIRef) -> List[URIRef]:
        """Get parent classes for a given class"""
        return self.class_hierarchy.get(class_uri, [])
    
    def get_valid_relations(self, source_type: URIRef, target_type: URIRef) -> List[URIRef]:
        """Get valid relationship types between two entity types"""
        key = (source_type, target_type)
        return self.valid_relationships.get(key, [])
    
    def get_entity_pattern(self, entity_type: str) -> dict:
        """Get NER patterns for an entity type"""
        return self.entity_patterns.get(entity_type, {})
    
    def get_all_entity_types(self) -> List[str]:
        """Get all supported entity types"""
        return list(self.entity_patterns.keys())


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_uri(namespace: Namespace, local_name: str) -> URIRef:
    """Create a URI reference from namespace and local name"""
    return namespace[local_name]


def get_namespace_prefix(uri: URIRef) -> Optional[str]:
    """Get the namespace prefix for a URI"""
    uri_str = str(uri)
    for prefix, ns in NAMESPACE_BINDINGS.items():
        if uri_str.startswith(str(ns)):
            return prefix
    return None


def resolve_alias(alias: str, schema: FinancialOntologySchema) -> Optional[URIRef]:
    """Resolve an alias to its ontology class URI"""
    alias_lower = alias.lower()
    for entity_type, info in schema.entity_patterns.items():
        if alias_lower in [a.lower() for a in info.get("aliases", [])]:
            return info["class"]
        if alias_lower == entity_type.lower():
            return info["class"]
    return None


# =============================================================================
# SECTOR MAPPING
# =============================================================================

SECTOR_MAPPING = {
    "Technology": SectorClass.TECHNOLOGY.value,
    "Information Technology": SectorClass.TECHNOLOGY.value,
    "Software": SectorClass.TECHNOLOGY.value,
    "Semiconductors": SectorClass.TECHNOLOGY.value,
    "Healthcare": SectorClass.HEALTHCARE.value,
    "Pharmaceuticals": SectorClass.HEALTHCARE.value,
    "Biotechnology": SectorClass.HEALTHCARE.value,
    "Medical Devices": SectorClass.HEALTHCARE.value,
    "Financial Services": SectorClass.FINANCIAL.value,
    "Banks": SectorClass.FINANCIAL.value,
    "Insurance": SectorClass.FINANCIAL.value,
    "Investment Banking": SectorClass.FINANCIAL.value,
    "Consumer Goods": SectorClass.CONSUMER.value,
    "Consumer Discretionary": SectorClass.CONSUMER.value,
    "Consumer Staples": SectorClass.CONSUMER.value,
    "Retail": SectorClass.CONSUMER.value,
    "Energy": SectorClass.ENERGY.value,
    "Oil & Gas": SectorClass.ENERGY.value,
    "Utilities": SectorClass.ENERGY.value,
    "Industrials": SectorClass.INDUSTRIALS.value,
    "Manufacturing": SectorClass.INDUSTRIALS.value,
    "Aerospace": SectorClass.INDUSTRIALS.value,
}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Namespaces
    "SEI", "SEI_CO", "SEI_FIN", "SEI_DOC", "SEI_RISK", "SEI_ECON",
    "NAMESPACE_BINDINGS", "FIBO_FND", "FIBO_BE", "FIBO_SEC",
    
    # Class Enums
    "CompanyClass", "SectorClass", "FinancialClass", 
    "DocumentClass", "RiskClass", "EconomicClass",
    
    # Property Enums
    "ObjectProperty", "DataProperty",
    
    # Schema
    "FinancialOntologySchema", "OntologyClassDef",
    
    # Utilities
    "create_uri", "get_namespace_prefix", "resolve_alias",
    "SECTOR_MAPPING",
]

"""
Ontology Mapper Module
=======================

Maps extracted entities and relations to ontology classes.
Provides clear interface between IDR output and Knowledge Graph.

Author: Rajesh Kumar Gupta
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# =============================================================================
# ONTOLOGY CLASS DEFINITIONS
# =============================================================================

class OntologyNamespace(Enum):
    """Ontology namespace prefixes"""
    SEI = "http://www.semanticdataservices.com/ontology/"
    SEI_CO = "http://www.semanticdataservices.com/ontology/company#"
    SEI_FIN = "http://www.semanticdataservices.com/ontology/financial#"
    SEI_DOC = "http://www.semanticdataservices.com/ontology/document#"
    SEI_RISK = "http://www.semanticdataservices.com/ontology/risk#"
    SEI_ECON = "http://www.semanticdataservices.com/ontology/economic#"
    FIBO_FND = "https://spec.edmcouncil.org/fibo/ontology/FND/"
    FIBO_BE = "https://spec.edmcouncil.org/fibo/ontology/BE/"


@dataclass
class OntologyClass:
    """Definition of an ontology class"""
    uri: str
    label: str
    namespace: OntologyNamespace
    parent_uri: Optional[str] = None
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    
    @property
    def local_name(self) -> str:
        """Get local name from URI"""
        return self.uri.split("#")[-1] if "#" in self.uri else self.uri.split("/")[-1]
    
    def to_dict(self) -> Dict:
        return {
            "uri": self.uri,
            "label": self.label,
            "local_name": self.local_name,
            "namespace": self.namespace.value,
            "parent": self.parent_uri,
            "description": self.description,
            "aliases": self.aliases,
        }


@dataclass
class OntologyProperty:
    """Definition of an ontology property"""
    uri: str
    label: str
    domain_uri: str
    range_uri: str
    property_type: str = "object"  # object or data
    description: str = ""
    inverse_uri: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "uri": self.uri,
            "label": self.label,
            "domain": self.domain_uri,
            "range": self.range_uri,
            "type": self.property_type,
        }


# =============================================================================
# ONTOLOGY SCHEMA REGISTRY
# =============================================================================

class OntologySchema:
    """
    Complete Financial Ontology Schema
    
    Defines all classes, properties, and their mappings for the
    Semantic Expert AI Financial IDR system.
    """
    
    def __init__(self):
        self._classes: Dict[str, OntologyClass] = {}
        self._properties: Dict[str, OntologyProperty] = {}
        self._entity_type_mapping: Dict[str, str] = {}
        self._relation_type_mapping: Dict[str, str] = {}
        self._aliases: Dict[str, str] = {}
        
        self._register_classes()
        self._register_properties()
        self._build_mappings()
    
    def _register_classes(self) -> None:
        """Register all ontology classes"""
        
        # =====================================================================
        # COMPANY CLASSES (sei-co namespace)
        # =====================================================================
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_CO.value}Organization",
            label="Organization",
            namespace=OntologyNamespace.SEI_CO,
            description="A legal entity or group organized for a purpose",
        ))
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_CO.value}Company",
            label="Company",
            namespace=OntologyNamespace.SEI_CO,
            parent_uri=f"{OntologyNamespace.SEI_CO.value}Organization",
            description="A business entity engaged in commercial activities",
            aliases=["corporation", "firm", "enterprise", "business"],
            properties=["ticker", "cik", "companyName", "headquarters", "employeeCount"],
        ))
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_CO.value}PublicCompany",
            label="Public Company",
            namespace=OntologyNamespace.SEI_CO,
            parent_uri=f"{OntologyNamespace.SEI_CO.value}Company",
            description="A company whose shares trade on public exchanges",
            aliases=["listed company", "publicly traded"],
        ))
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_CO.value}Person",
            label="Person",
            namespace=OntologyNamespace.SEI_CO,
            description="An individual person",
            aliases=["executive", "officer", "director"],
            properties=["name", "title", "role"],
        ))
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_CO.value}Product",
            label="Product",
            namespace=OntologyNamespace.SEI_CO,
            description="A product or service offered by a company",
            aliases=["service", "offering"],
        ))
        
        # Industry Sectors
        for sector in ["Technology", "Healthcare", "Financial", "Consumer", "Energy", "Industrials"]:
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_CO.value}{sector}Sector",
                label=f"{sector} Sector",
                namespace=OntologyNamespace.SEI_CO,
                parent_uri=f"{OntologyNamespace.SEI_CO.value}IndustrySector",
                description=f"The {sector} industry sector",
            ))
        
        # =====================================================================
        # FINANCIAL CLASSES (sei-fin namespace)
        # =====================================================================
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_FIN.value}FinancialMetric",
            label="Financial Metric",
            namespace=OntologyNamespace.SEI_FIN,
            description="A quantitative measure of financial performance",
            properties=["value", "currency", "fiscalYear", "fiscalQuarter"],
        ))
        
        financial_metrics = [
            ("Revenue", "Total revenue or sales", ["sales", "net sales", "total revenue"]),
            ("NetIncome", "Net income or profit", ["profit", "earnings", "net profit", "net earnings"]),
            ("GrossProfit", "Gross profit", ["gross margin"]),
            ("OperatingIncome", "Operating income", ["EBIT", "operating profit"]),
            ("EBITDA", "Earnings Before Interest, Taxes, Depreciation and Amortization", []),
            ("EarningsPerShare", "Earnings per share", ["EPS", "diluted EPS"]),
            ("TotalAssets", "Total assets", ["assets"]),
            ("TotalLiabilities", "Total liabilities", ["liabilities", "debt"]),
            ("ShareholdersEquity", "Shareholders equity", ["book value", "stockholders equity"]),
            ("CashFlow", "Cash flow", []),
            ("OperatingCashFlow", "Operating cash flow", ["cash from operations"]),
            ("FreeCashFlow", "Free cash flow", ["FCF"]),
        ]
        
        for name, desc, aliases in financial_metrics:
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_FIN.value}{name}",
                label=name,
                namespace=OntologyNamespace.SEI_FIN,
                parent_uri=f"{OntologyNamespace.SEI_FIN.value}FinancialMetric",
                description=desc,
                aliases=aliases,
            ))
        
        # Financial Ratios
        ratios = [
            ("PriceToEarnings", "P/E Ratio", ["PE ratio", "price earnings"]),
            ("DebtToEquity", "Debt to Equity Ratio", ["D/E ratio", "leverage ratio"]),
            ("ReturnOnEquity", "Return on Equity", ["ROE"]),
            ("ReturnOnAssets", "Return on Assets", ["ROA"]),
        ]
        
        for name, desc, aliases in ratios:
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_FIN.value}{name}",
                label=desc,
                namespace=OntologyNamespace.SEI_FIN,
                parent_uri=f"{OntologyNamespace.SEI_FIN.value}FinancialRatio",
                aliases=aliases,
            ))
        
        # =====================================================================
        # DOCUMENT CLASSES (sei-doc namespace)
        # =====================================================================
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_DOC.value}Document",
            label="Document",
            namespace=OntologyNamespace.SEI_DOC,
            description="A written or electronic record",
            properties=["documentUrl", "filingDate"],
        ))
        
        document_types = [
            ("SECFiling", "SEC Filing", "Document filed with the SEC"),
            ("Form10K", "Form 10-K", "Annual report filed by public companies"),
            ("Form10Q", "Form 10-Q", "Quarterly report filed by public companies"),
            ("Form8K", "Form 8-K", "Current report for material events"),
            ("ProxyStatement", "Proxy Statement", "DEF 14A proxy statement"),
            ("EquityResearchReport", "Equity Research Report", "Analyst research report"),
            ("EarningsCallTranscript", "Earnings Call Transcript", "Transcript of earnings call"),
            ("PressRelease", "Press Release", "Company press release"),
        ]
        
        for name, label, desc in document_types:
            parent = f"{OntologyNamespace.SEI_DOC.value}SECFiling" if "Form" in name else f"{OntologyNamespace.SEI_DOC.value}Document"
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_DOC.value}{name}",
                label=label,
                namespace=OntologyNamespace.SEI_DOC,
                parent_uri=parent,
                description=desc,
            ))
        
        # =====================================================================
        # RISK CLASSES (sei-risk namespace)
        # =====================================================================
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_RISK.value}Risk",
            label="Risk",
            namespace=OntologyNamespace.SEI_RISK,
            description="A potential event that may negatively impact an entity",
            properties=["severity", "likelihood", "riskDescription"],
        ))
        
        risk_types = [
            ("OperationalRisk", "Operational Risk", "Risk", ["operations risk"]),
            ("SupplyChainRisk", "Supply Chain Risk", "OperationalRisk", ["supplier risk", "logistics risk", "manufacturing risk"]),
            ("CybersecurityRisk", "Cybersecurity Risk", "OperationalRisk", ["cyber risk", "data breach risk", "security risk"]),
            ("FinancialRisk", "Financial Risk", "Risk", []),
            ("CreditRisk", "Credit Risk", "FinancialRisk", ["default risk", "counterparty risk"]),
            ("LiquidityRisk", "Liquidity Risk", "FinancialRisk", ["funding risk"]),
            ("MarketRisk", "Market Risk", "FinancialRisk", []),
            ("CurrencyRisk", "Currency Risk", "MarketRisk", ["FX risk", "foreign exchange risk", "exchange rate risk"]),
            ("InterestRateRisk", "Interest Rate Risk", "MarketRisk", ["rate risk"]),
            ("RegulatoryRisk", "Regulatory Risk", "Risk", ["compliance risk", "legal risk", "government risk"]),
            ("GeopoliticalRisk", "Geopolitical Risk", "Risk", ["political risk", "trade risk", "sanction risk"]),
            ("CompetitiveRisk", "Competitive Risk", "Risk", ["competition risk", "market share risk"]),
            ("TechnologyRisk", "Technology Risk", "Risk", ["tech risk", "disruption risk", "obsolescence risk"]),
            ("ReputationalRisk", "Reputational Risk", "Risk", ["brand risk"]),
            ("EnvironmentalRisk", "Environmental Risk", "Risk", ["climate risk", "ESG risk"]),
        ]
        
        for name, label, parent, aliases in risk_types:
            parent_uri = f"{OntologyNamespace.SEI_RISK.value}{parent}"
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_RISK.value}{name}",
                label=label,
                namespace=OntologyNamespace.SEI_RISK,
                parent_uri=parent_uri,
                aliases=aliases,
            ))
        
        # =====================================================================
        # ECONOMIC CLASSES (sei-econ namespace)
        # =====================================================================
        
        self._add_class(OntologyClass(
            uri=f"{OntologyNamespace.SEI_ECON.value}EconomicIndicator",
            label="Economic Indicator",
            namespace=OntologyNamespace.SEI_ECON,
            description="A statistic about economic activity",
            properties=["indicatorValue", "observationDate", "dataSource"],
        ))
        
        economic_indicators = [
            ("GDP", "Gross Domestic Product", ["gross domestic product"]),
            ("InflationRate", "Inflation Rate", ["CPI", "consumer price index"]),
            ("UnemploymentRate", "Unemployment Rate", ["jobless rate"]),
            ("InterestRate", "Interest Rate", ["rates"]),
            ("FederalFundsRate", "Federal Funds Rate", ["fed funds rate", "fed rate"]),
            ("ConsumerConfidence", "Consumer Confidence Index", ["consumer sentiment"]),
            ("PMI", "Purchasing Managers Index", ["manufacturing index"]),
            ("TradeBalance", "Trade Balance", ["trade deficit", "trade surplus"]),
        ]
        
        for name, label, aliases in economic_indicators:
            self._add_class(OntologyClass(
                uri=f"{OntologyNamespace.SEI_ECON.value}{name}",
                label=label,
                namespace=OntologyNamespace.SEI_ECON,
                parent_uri=f"{OntologyNamespace.SEI_ECON.value}MacroeconomicIndicator",
                aliases=aliases,
            ))
    
    def _register_properties(self) -> None:
        """Register all ontology properties"""
        
        # Object Properties (Relationships)
        object_properties = [
            # Company relationships
            ("competesWith", "Company", "Company", "competes with"),
            ("partnersWith", "Company", "Company", "partners with"),
            ("acquired", "Company", "Company", "acquired"),
            ("hasSubsidiary", "Company", "Company", "has subsidiary"),
            ("isSubsidiaryOf", "Company", "Company", "is subsidiary of"),
            ("suppliesTo", "Organization", "Company", "supplies to"),
            ("belongsToSector", "Company", "IndustrySector", "belongs to sector"),
            
            # Financial relationships
            ("hasFinancialMetric", "Company", "FinancialMetric", "has financial metric"),
            ("reportedIn", "FinancialMetric", "Document", "reported in"),
            
            # Document relationships
            ("filedBy", "SECFiling", "PublicCompany", "filed by"),
            ("mentionsEntity", "Document", "Entity", "mentions entity"),
            
            # Risk relationships
            ("facesRisk", "Company", "Risk", "faces risk"),
            ("disclosedIn", "Risk", "Document", "disclosed in"),
            
            # Person relationships
            ("worksAt", "Person", "Company", "works at"),
            ("isCEOOf", "Person", "Company", "is CEO of"),
            
            # Economic relationships
            ("impactedBy", "Company", "EconomicIndicator", "impacted by"),
        ]
        
        for name, domain, range_class, label in object_properties:
            self._properties[name] = OntologyProperty(
                uri=f"{OntologyNamespace.SEI_CO.value}{name}",
                label=label,
                domain_uri=f"{OntologyNamespace.SEI_CO.value}{domain}",
                range_uri=f"{OntologyNamespace.SEI_CO.value}{range_class}",
                property_type="object",
            )
    
    def _build_mappings(self) -> None:
        """Build entity type to URI mappings"""
        
        # Entity type to ontology class mapping
        self._entity_type_mapping = {
            # Company types
            "Company": f"{OntologyNamespace.SEI_CO.value}PublicCompany",
            "PublicCompany": f"{OntologyNamespace.SEI_CO.value}PublicCompany",
            "Organization": f"{OntologyNamespace.SEI_CO.value}Organization",
            "Person": f"{OntologyNamespace.SEI_CO.value}Person",
            "Product": f"{OntologyNamespace.SEI_CO.value}Product",
            
            # Financial metrics
            "Revenue": f"{OntologyNamespace.SEI_FIN.value}Revenue",
            "NetIncome": f"{OntologyNamespace.SEI_FIN.value}NetIncome",
            "EarningsPerShare": f"{OntologyNamespace.SEI_FIN.value}EarningsPerShare",
            "TotalAssets": f"{OntologyNamespace.SEI_FIN.value}TotalAssets",
            "CashFlow": f"{OntologyNamespace.SEI_FIN.value}CashFlow",
            "MonetaryAmount": f"{OntologyNamespace.SEI_FIN.value}FinancialMetric",
            "FinancialMetric": f"{OntologyNamespace.SEI_FIN.value}FinancialMetric",
            
            # Risk types
            "Risk": f"{OntologyNamespace.SEI_RISK.value}Risk",
            "SupplyChainRisk": f"{OntologyNamespace.SEI_RISK.value}SupplyChainRisk",
            "CurrencyRisk": f"{OntologyNamespace.SEI_RISK.value}CurrencyRisk",
            "RegulatoryRisk": f"{OntologyNamespace.SEI_RISK.value}RegulatoryRisk",
            "GeopoliticalRisk": f"{OntologyNamespace.SEI_RISK.value}GeopoliticalRisk",
            "CompetitiveRisk": f"{OntologyNamespace.SEI_RISK.value}CompetitiveRisk",
            "CybersecurityRisk": f"{OntologyNamespace.SEI_RISK.value}CybersecurityRisk",
            "TechnologyRisk": f"{OntologyNamespace.SEI_RISK.value}TechnologyRisk",
            
            # Document types
            "Document": f"{OntologyNamespace.SEI_DOC.value}Document",
            "Form10K": f"{OntologyNamespace.SEI_DOC.value}Form10K",
            "Form10Q": f"{OntologyNamespace.SEI_DOC.value}Form10Q",
            
            # Economic
            "EconomicIndicator": f"{OntologyNamespace.SEI_ECON.value}EconomicIndicator",
            
            # Generic
            "Date": "http://www.w3.org/2001/XMLSchema#date",
            "Percentage": "http://www.w3.org/2001/XMLSchema#decimal",
        }
        
        # Relation type to property mapping
        self._relation_type_mapping = {
            "COMPETES_WITH": f"{OntologyNamespace.SEI_CO.value}competesWith",
            "PARTNERS_WITH": f"{OntologyNamespace.SEI_CO.value}partnersWith",
            "ACQUIRED": f"{OntologyNamespace.SEI_CO.value}acquired",
            "SUBSIDIARY_OF": f"{OntologyNamespace.SEI_CO.value}isSubsidiaryOf",
            "HAS_SUBSIDIARY": f"{OntologyNamespace.SEI_CO.value}hasSubsidiary",
            "SUPPLIES_TO": f"{OntologyNamespace.SEI_CO.value}suppliesTo",
            "BELONGS_TO_SECTOR": f"{OntologyNamespace.SEI_CO.value}belongsToSector",
            "REPORTED": f"{OntologyNamespace.SEI_FIN.value}hasFinancialMetric",
            "GENERATED": f"{OntologyNamespace.SEI_FIN.value}hasFinancialMetric",
            "FACES_RISK": f"{OntologyNamespace.SEI_RISK.value}facesRisk",
            "DISCLOSED_IN": f"{OntologyNamespace.SEI_RISK.value}disclosedIn",
            "WORKS_AT": f"{OntologyNamespace.SEI_CO.value}worksAt",
            "CEO_OF": f"{OntologyNamespace.SEI_CO.value}isCEOOf",
            "IMPACTED_BY": f"{OntologyNamespace.SEI_ECON.value}impactedBy",
            "MANUFACTURES": f"{OntologyNamespace.SEI_CO.value}manufactures",
            "SELLS": f"{OntologyNamespace.SEI_CO.value}sells",
        }
        
        # Build alias lookup
        for class_obj in self._classes.values():
            for alias in class_obj.aliases:
                self._aliases[alias.lower()] = class_obj.uri
            self._aliases[class_obj.label.lower()] = class_obj.uri
    
    def _add_class(self, ontology_class: OntologyClass) -> None:
        """Add a class to the registry"""
        self._classes[ontology_class.uri] = ontology_class
        self._classes[ontology_class.local_name] = ontology_class
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get_class(self, identifier: str) -> Optional[OntologyClass]:
        """Get ontology class by URI or local name"""
        return self._classes.get(identifier)
    
    def get_property(self, name: str) -> Optional[OntologyProperty]:
        """Get ontology property by name"""
        return self._properties.get(name)
    
    def map_entity_type(self, entity_type: str) -> Optional[str]:
        """Map entity type to ontology class URI"""
        return self._entity_type_mapping.get(entity_type)
    
    def map_relation_type(self, relation_type: str) -> Optional[str]:
        """Map relation type to ontology property URI"""
        return self._relation_type_mapping.get(relation_type)
    
    def resolve_alias(self, text: str) -> Optional[str]:
        """Resolve an alias to ontology class URI"""
        return self._aliases.get(text.lower())
    
    def get_all_entity_types(self) -> List[str]:
        """Get all supported entity types"""
        return list(self._entity_type_mapping.keys())
    
    def get_all_relation_types(self) -> List[str]:
        """Get all supported relation types"""
        return list(self._relation_type_mapping.keys())
    
    def get_class_hierarchy(self, class_uri: str) -> List[str]:
        """Get the class hierarchy (ancestors) for a class"""
        hierarchy = [class_uri]
        current = self._classes.get(class_uri)
        
        while current and current.parent_uri:
            hierarchy.append(current.parent_uri)
            current = self._classes.get(current.parent_uri)
        
        return hierarchy
    
    def is_subclass_of(self, class_uri: str, parent_uri: str) -> bool:
        """Check if a class is a subclass of another"""
        hierarchy = self.get_class_hierarchy(class_uri)
        return parent_uri in hierarchy
    
    def validate_relation(self, subject_type: str, relation: str, object_type: str) -> bool:
        """Validate if a relation is valid for given entity types"""
        prop = self._properties.get(relation.lower().replace("_", ""))
        if not prop:
            return True  # Allow unknown relations
        
        # Check domain and range
        subject_uri = self.map_entity_type(subject_type)
        object_uri = self.map_entity_type(object_type)
        
        if not subject_uri or not object_uri:
            return True
        
        # Check if subject is compatible with domain
        domain_compatible = self.is_subclass_of(subject_uri, prop.domain_uri)
        range_compatible = self.is_subclass_of(object_uri, prop.range_uri)
        
        return domain_compatible and range_compatible
    
    def to_dict(self) -> Dict:
        """Export schema as dictionary"""
        return {
            "classes": {k: v.to_dict() for k, v in self._classes.items() if "#" in k},
            "properties": {k: v.to_dict() for k, v in self._properties.items()},
            "entity_mappings": self._entity_type_mapping,
            "relation_mappings": self._relation_type_mapping,
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_schema_instance: Optional[OntologySchema] = None


def get_ontology_schema() -> OntologySchema:
    """Get the singleton ontology schema instance"""
    global _schema_instance
    if _schema_instance is None:
        _schema_instance = OntologySchema()
    return _schema_instance

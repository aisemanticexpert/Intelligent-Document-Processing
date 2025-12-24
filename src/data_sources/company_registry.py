"""
Company Registry Module
========================

Registry of companies from various sectors for IDR processing.
Includes metadata for SEC EDGAR access and sector classification.

Author: Rajesh Kumar Gupta
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Sector(Enum):
    """Industry sectors"""
    TECHNOLOGY = "Technology"
    HEALTHCARE = "Healthcare"
    FINANCIAL = "Financial Services"
    CONSUMER = "Consumer"
    ENERGY = "Energy"
    INDUSTRIALS = "Industrials"
    TELECOMMUNICATIONS = "Telecommunications"
    UTILITIES = "Utilities"
    REAL_ESTATE = "Real Estate"
    MATERIALS = "Materials"


@dataclass
class Company:
    """Company definition with SEC EDGAR metadata"""
    ticker: str
    name: str
    cik: str
    sector: Sector
    industry: str = ""
    headquarters: str = ""
    description: str = ""
    market_cap_category: str = "Large Cap"  # Large Cap, Mid Cap, Small Cap
    sp500: bool = False
    fiscal_year_end: str = "December"
    competitors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "cik": self.cik,
            "sector": self.sector.value,
            "industry": self.industry,
            "headquarters": self.headquarters,
            "market_cap_category": self.market_cap_category,
            "sp500": self.sp500,
        }
    
    @property
    def cik_padded(self) -> str:
        """Get 10-digit padded CIK"""
        return self.cik.lstrip("0").zfill(10)


class CompanyRegistry:
    """
    Registry of companies for Financial IDR processing.
    
    Contains companies from multiple sectors:
    - Technology (Apple, Microsoft, Google, etc.)
    - Healthcare (J&J, Pfizer, UnitedHealth, etc.)
    - Financial (JPMorgan, Goldman Sachs, etc.)
    - Consumer (Walmart, Coca-Cola, etc.)
    - Energy (ExxonMobil, Chevron, etc.)
    """
    
    def __init__(self):
        self._companies: Dict[str, Company] = {}
        self._register_companies()
    
    def _register_companies(self) -> None:
        """Register all companies"""
        
        # =====================================================================
        # TECHNOLOGY SECTOR
        # =====================================================================
        
        tech_companies = [
            Company(
                ticker="AAPL",
                name="Apple Inc.",
                cik="0000320193",
                sector=Sector.TECHNOLOGY,
                industry="Consumer Electronics",
                headquarters="Cupertino, California",
                description="Designs, manufactures, and markets smartphones, computers, tablets, wearables",
                sp500=True,
                fiscal_year_end="September",
                competitors=["MSFT", "GOOGL", "SAMSUNG"],
            ),
            Company(
                ticker="MSFT",
                name="Microsoft Corporation",
                cik="0000789019",
                sector=Sector.TECHNOLOGY,
                industry="Software & Cloud Services",
                headquarters="Redmond, Washington",
                description="Develops software, cloud computing, and hardware products",
                sp500=True,
                competitors=["AAPL", "GOOGL", "AMZN", "ORCL"],
            ),
            Company(
                ticker="GOOGL",
                name="Alphabet Inc.",
                cik="0001652044",
                sector=Sector.TECHNOLOGY,
                industry="Internet Services & AI",
                headquarters="Mountain View, California",
                description="Parent company of Google, focused on search, advertising, and cloud",
                sp500=True,
                competitors=["MSFT", "META", "AMZN"],
            ),
            Company(
                ticker="AMZN",
                name="Amazon.com, Inc.",
                cik="0001018724",
                sector=Sector.TECHNOLOGY,
                industry="E-commerce & Cloud Computing",
                headquarters="Seattle, Washington",
                description="E-commerce, cloud computing (AWS), digital streaming",
                sp500=True,
                competitors=["MSFT", "GOOGL", "WMT"],
            ),
            Company(
                ticker="NVDA",
                name="NVIDIA Corporation",
                cik="0001045810",
                sector=Sector.TECHNOLOGY,
                industry="Semiconductors",
                headquarters="Santa Clara, California",
                description="Graphics processing units (GPUs) and AI computing",
                sp500=True,
                fiscal_year_end="January",
                competitors=["AMD", "INTC", "QCOM"],
            ),
            Company(
                ticker="META",
                name="Meta Platforms, Inc.",
                cik="0001326801",
                sector=Sector.TECHNOLOGY,
                industry="Social Media & Metaverse",
                headquarters="Menlo Park, California",
                description="Social networking, virtual reality, digital advertising",
                sp500=True,
                competitors=["GOOGL", "SNAP", "PINS"],
            ),
            Company(
                ticker="INTC",
                name="Intel Corporation",
                cik="0000050863",
                sector=Sector.TECHNOLOGY,
                industry="Semiconductors",
                headquarters="Santa Clara, California",
                description="Semiconductor chip manufacturing",
                sp500=True,
                competitors=["AMD", "NVDA", "QCOM"],
            ),
            Company(
                ticker="AMD",
                name="Advanced Micro Devices, Inc.",
                cik="0000002488",
                sector=Sector.TECHNOLOGY,
                industry="Semiconductors",
                headquarters="Santa Clara, California",
                description="Semiconductor products for computing and graphics",
                sp500=True,
                competitors=["INTC", "NVDA"],
            ),
            Company(
                ticker="CRM",
                name="Salesforce, Inc.",
                cik="0001108524",
                sector=Sector.TECHNOLOGY,
                industry="Cloud Software",
                headquarters="San Francisco, California",
                description="Cloud-based CRM and enterprise software",
                sp500=True,
                fiscal_year_end="January",
                competitors=["MSFT", "ORCL", "SAP"],
            ),
            Company(
                ticker="ORCL",
                name="Oracle Corporation",
                cik="0001341439",
                sector=Sector.TECHNOLOGY,
                industry="Enterprise Software & Cloud",
                headquarters="Austin, Texas",
                description="Database software, cloud infrastructure, enterprise applications",
                sp500=True,
                fiscal_year_end="May",
                competitors=["MSFT", "SAP", "IBM"],
            ),
        ]
        
        for company in tech_companies:
            self._add_company(company)
        
        # =====================================================================
        # HEALTHCARE SECTOR
        # =====================================================================
        
        healthcare_companies = [
            Company(
                ticker="JNJ",
                name="Johnson & Johnson",
                cik="0000200406",
                sector=Sector.HEALTHCARE,
                industry="Pharmaceuticals & Medical Devices",
                headquarters="New Brunswick, New Jersey",
                description="Pharmaceuticals, medical devices, and consumer health products",
                sp500=True,
                competitors=["PFE", "MRK", "ABBV"],
            ),
            Company(
                ticker="UNH",
                name="UnitedHealth Group Incorporated",
                cik="0000731766",
                sector=Sector.HEALTHCARE,
                industry="Health Insurance",
                headquarters="Minnetonka, Minnesota",
                description="Health insurance and healthcare services",
                sp500=True,
                competitors=["CVS", "ANTM", "CI"],
            ),
            Company(
                ticker="PFE",
                name="Pfizer Inc.",
                cik="0000078003",
                sector=Sector.HEALTHCARE,
                industry="Pharmaceuticals",
                headquarters="New York, New York",
                description="Pharmaceutical and biotechnology corporation",
                sp500=True,
                competitors=["JNJ", "MRK", "ABBV"],
            ),
            Company(
                ticker="ABBV",
                name="AbbVie Inc.",
                cik="0001551152",
                sector=Sector.HEALTHCARE,
                industry="Pharmaceuticals",
                headquarters="North Chicago, Illinois",
                description="Biopharmaceutical company focused on immunology",
                sp500=True,
                competitors=["JNJ", "PFE", "MRK"],
            ),
            Company(
                ticker="MRK",
                name="Merck & Co., Inc.",
                cik="0000310158",
                sector=Sector.HEALTHCARE,
                industry="Pharmaceuticals",
                headquarters="Rahway, New Jersey",
                description="Global pharmaceutical company",
                sp500=True,
                competitors=["JNJ", "PFE", "ABBV"],
            ),
            Company(
                ticker="LLY",
                name="Eli Lilly and Company",
                cik="0000059478",
                sector=Sector.HEALTHCARE,
                industry="Pharmaceuticals",
                headquarters="Indianapolis, Indiana",
                description="Pharmaceutical company focused on diabetes and oncology",
                sp500=True,
                competitors=["NVO", "PFE", "MRK"],
            ),
        ]
        
        for company in healthcare_companies:
            self._add_company(company)
        
        # =====================================================================
        # FINANCIAL SECTOR
        # =====================================================================
        
        financial_companies = [
            Company(
                ticker="JPM",
                name="JPMorgan Chase & Co.",
                cik="0000019617",
                sector=Sector.FINANCIAL,
                industry="Banking",
                headquarters="New York, New York",
                description="Multinational investment bank and financial services",
                sp500=True,
                competitors=["BAC", "GS", "MS", "C"],
            ),
            Company(
                ticker="BAC",
                name="Bank of America Corporation",
                cik="0000070858",
                sector=Sector.FINANCIAL,
                industry="Banking",
                headquarters="Charlotte, North Carolina",
                description="Multinational investment bank and financial services",
                sp500=True,
                competitors=["JPM", "WFC", "C"],
            ),
            Company(
                ticker="GS",
                name="The Goldman Sachs Group, Inc.",
                cik="0000886982",
                sector=Sector.FINANCIAL,
                industry="Investment Banking",
                headquarters="New York, New York",
                description="Global investment banking and securities firm",
                sp500=True,
                competitors=["MS", "JPM"],
            ),
            Company(
                ticker="MS",
                name="Morgan Stanley",
                cik="0000895421",
                sector=Sector.FINANCIAL,
                industry="Investment Banking",
                headquarters="New York, New York",
                description="Global financial services firm",
                sp500=True,
                competitors=["GS", "JPM"],
            ),
            Company(
                ticker="WFC",
                name="Wells Fargo & Company",
                cik="0000072971",
                sector=Sector.FINANCIAL,
                industry="Banking",
                headquarters="San Francisco, California",
                description="Multinational financial services company",
                sp500=True,
                competitors=["JPM", "BAC", "C"],
            ),
            Company(
                ticker="V",
                name="Visa Inc.",
                cik="0001403161",
                sector=Sector.FINANCIAL,
                industry="Payment Processing",
                headquarters="San Francisco, California",
                description="Global payments technology company",
                sp500=True,
                fiscal_year_end="September",
                competitors=["MA", "AXP"],
            ),
            Company(
                ticker="MA",
                name="Mastercard Incorporated",
                cik="0001141391",
                sector=Sector.FINANCIAL,
                industry="Payment Processing",
                headquarters="Purchase, New York",
                description="Global payments and technology company",
                sp500=True,
                competitors=["V", "AXP"],
            ),
        ]
        
        for company in financial_companies:
            self._add_company(company)
        
        # =====================================================================
        # CONSUMER SECTOR
        # =====================================================================
        
        consumer_companies = [
            Company(
                ticker="WMT",
                name="Walmart Inc.",
                cik="0000104169",
                sector=Sector.CONSUMER,
                industry="Retail",
                headquarters="Bentonville, Arkansas",
                description="Multinational retail corporation",
                sp500=True,
                fiscal_year_end="January",
                competitors=["AMZN", "TGT", "COST"],
            ),
            Company(
                ticker="KO",
                name="The Coca-Cola Company",
                cik="0000021344",
                sector=Sector.CONSUMER,
                industry="Beverages",
                headquarters="Atlanta, Georgia",
                description="Multinational beverage corporation",
                sp500=True,
                competitors=["PEP", "KDP"],
            ),
            Company(
                ticker="PEP",
                name="PepsiCo, Inc.",
                cik="0000077476",
                sector=Sector.CONSUMER,
                industry="Beverages & Snacks",
                headquarters="Purchase, New York",
                description="Multinational food, snack, and beverage corporation",
                sp500=True,
                competitors=["KO", "KDP"],
            ),
            Company(
                ticker="PG",
                name="The Procter & Gamble Company",
                cik="0000080424",
                sector=Sector.CONSUMER,
                industry="Consumer Goods",
                headquarters="Cincinnati, Ohio",
                description="Consumer goods corporation",
                sp500=True,
                fiscal_year_end="June",
                competitors=["UL", "CL", "KMB"],
            ),
            Company(
                ticker="COST",
                name="Costco Wholesale Corporation",
                cik="0000909832",
                sector=Sector.CONSUMER,
                industry="Retail",
                headquarters="Issaquah, Washington",
                description="Membership-only warehouse club",
                sp500=True,
                fiscal_year_end="August",
                competitors=["WMT", "TGT", "BJ"],
            ),
            Company(
                ticker="HD",
                name="The Home Depot, Inc.",
                cik="0000354950",
                sector=Sector.CONSUMER,
                industry="Home Improvement Retail",
                headquarters="Atlanta, Georgia",
                description="Home improvement retail company",
                sp500=True,
                fiscal_year_end="January",
                competitors=["LOW"],
            ),
        ]
        
        for company in consumer_companies:
            self._add_company(company)
        
        # =====================================================================
        # ENERGY SECTOR
        # =====================================================================
        
        energy_companies = [
            Company(
                ticker="XOM",
                name="Exxon Mobil Corporation",
                cik="0000034088",
                sector=Sector.ENERGY,
                industry="Oil & Gas",
                headquarters="Irving, Texas",
                description="Multinational oil and gas corporation",
                sp500=True,
                competitors=["CVX", "COP", "BP"],
            ),
            Company(
                ticker="CVX",
                name="Chevron Corporation",
                cik="0000093410",
                sector=Sector.ENERGY,
                industry="Oil & Gas",
                headquarters="San Ramon, California",
                description="Multinational energy corporation",
                sp500=True,
                competitors=["XOM", "COP", "BP"],
            ),
            Company(
                ticker="COP",
                name="ConocoPhillips",
                cik="0001163165",
                sector=Sector.ENERGY,
                industry="Oil & Gas Exploration",
                headquarters="Houston, Texas",
                description="Oil and gas exploration and production",
                sp500=True,
                competitors=["XOM", "CVX"],
            ),
            Company(
                ticker="NEE",
                name="NextEra Energy, Inc.",
                cik="0000753308",
                sector=Sector.ENERGY,
                industry="Utilities & Renewable Energy",
                headquarters="Juno Beach, Florida",
                description="Clean energy and utility company",
                sp500=True,
                competitors=["DUK", "SO"],
            ),
        ]
        
        for company in energy_companies:
            self._add_company(company)
        
        # =====================================================================
        # INDUSTRIALS SECTOR
        # =====================================================================
        
        industrial_companies = [
            Company(
                ticker="CAT",
                name="Caterpillar Inc.",
                cik="0000018230",
                sector=Sector.INDUSTRIALS,
                industry="Heavy Equipment",
                headquarters="Irving, Texas",
                description="Heavy equipment and machinery manufacturer",
                sp500=True,
                competitors=["DE", "CNHI"],
            ),
            Company(
                ticker="BA",
                name="The Boeing Company",
                cik="0000012927",
                sector=Sector.INDUSTRIALS,
                industry="Aerospace & Defense",
                headquarters="Arlington, Virginia",
                description="Aerospace company and defense contractor",
                sp500=True,
                competitors=["LMT", "RTX", "GD"],
            ),
            Company(
                ticker="UPS",
                name="United Parcel Service, Inc.",
                cik="0001090727",
                sector=Sector.INDUSTRIALS,
                industry="Logistics & Delivery",
                headquarters="Atlanta, Georgia",
                description="Package delivery and supply chain services",
                sp500=True,
                competitors=["FDX"],
            ),
            Company(
                ticker="GE",
                name="General Electric Company",
                cik="0000040545",
                sector=Sector.INDUSTRIALS,
                industry="Conglomerate",
                headquarters="Boston, Massachusetts",
                description="Diversified technology and financial services",
                sp500=True,
                competitors=["HON", "MMM"],
            ),
        ]
        
        for company in industrial_companies:
            self._add_company(company)
    
    def _add_company(self, company: Company) -> None:
        """Add company to registry"""
        self._companies[company.ticker] = company
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get(self, ticker: str) -> Optional[Company]:
        """Get company by ticker symbol"""
        return self._companies.get(ticker.upper())
    
    def get_by_cik(self, cik: str) -> Optional[Company]:
        """Get company by CIK number"""
        cik_normalized = cik.lstrip("0")
        for company in self._companies.values():
            if company.cik.lstrip("0") == cik_normalized:
                return company
        return None
    
    def get_by_sector(self, sector: Sector) -> List[Company]:
        """Get all companies in a sector"""
        return [c for c in self._companies.values() if c.sector == sector]
    
    def get_all(self) -> List[Company]:
        """Get all registered companies"""
        return list(self._companies.values())
    
    def get_sp500(self) -> List[Company]:
        """Get all S&P 500 companies"""
        return [c for c in self._companies.values() if c.sp500]
    
    def get_tickers(self) -> List[str]:
        """Get all ticker symbols"""
        return list(self._companies.keys())
    
    def search(self, query: str) -> List[Company]:
        """Search companies by name or ticker"""
        query_lower = query.lower()
        results = []
        for company in self._companies.values():
            if (query_lower in company.ticker.lower() or 
                query_lower in company.name.lower()):
                results.append(company)
        return results
    
    def to_config_list(self, sector: Optional[Sector] = None) -> List[Dict]:
        """Export as list of dicts for pipeline config"""
        companies = self.get_by_sector(sector) if sector else self.get_all()
        return [c.to_dict() for c in companies]
    
    def __len__(self) -> int:
        return len(self._companies)
    
    def __iter__(self):
        return iter(self._companies.values())


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_registry_instance: Optional[CompanyRegistry] = None


def get_company_registry() -> CompanyRegistry:
    """Get the singleton company registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = CompanyRegistry()
    return _registry_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_sample_companies(per_sector: int = 2) -> List[Dict]:
    """Get a sample of companies from each sector"""
    registry = get_company_registry()
    companies = []
    
    for sector in Sector:
        sector_companies = registry.get_by_sector(sector)
        companies.extend([c.to_dict() for c in sector_companies[:per_sector]])
    
    return companies


def get_companies_for_demo() -> List[Dict]:
    """Get default companies for demo/testing"""
    tickers = ["AAPL", "MSFT", "JPM", "JNJ", "XOM", "WMT"]
    registry = get_company_registry()
    return [registry.get(t).to_dict() for t in tickers if registry.get(t)]

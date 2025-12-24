"""
Financial Entity Patterns Module
=================================

Comprehensive regex patterns for extracting financial entities
from SEC filings, earnings calls, and research reports.

Author: Rajesh Kumar Gupta
"""

import re
from typing import Dict, List, Tuple, Pattern
from dataclasses import dataclass


@dataclass
class EntityPattern:
    """Entity extraction pattern definition"""
    name: str
    entity_type: str
    patterns: List[str]
    confidence: float = 0.85
    properties_extractor: str = None  # Function name for extracting properties


# =============================================================================
# COMPANY PATTERNS
# =============================================================================

COMPANY_PATTERNS = [
    # Major Tech Companies
    r'\b(Apple\s+Inc\.?|Apple)\b',
    r'\b(Microsoft\s+Corporation|Microsoft\s+Corp\.?|Microsoft)\b',
    r'\b(Alphabet\s+Inc\.?|Google\s+LLC|Google)\b',
    r'\b(Amazon\.?com,?\s+Inc\.?|Amazon)\b',
    r'\b(Meta\s+Platforms,?\s+Inc\.?|Meta|Facebook)\b',
    r'\b(NVIDIA\s+Corporation|NVIDIA\s+Corp\.?|NVIDIA)\b',
    r'\b(Tesla,?\s+Inc\.?|Tesla)\b',
    r'\b(Intel\s+Corporation|Intel\s+Corp\.?|Intel)\b',
    r'\b(Advanced\s+Micro\s+Devices,?\s+Inc\.?|AMD)\b',
    r'\b(Salesforce,?\s+Inc\.?|Salesforce)\b',
    r'\b(Oracle\s+Corporation|Oracle\s+Corp\.?|Oracle)\b',
    r'\b(IBM|International\s+Business\s+Machines)\b',
    r'\b(Cisco\s+Systems,?\s+Inc\.?|Cisco)\b',
    r'\b(Adobe\s+Inc\.?|Adobe\s+Systems|Adobe)\b',
    
    # Financial Services
    r'\b(JPMorgan\s+Chase\s+&?\s*Co\.?|JPMorgan|JP\s*Morgan)\b',
    r'\b(Bank\s+of\s+America\s+Corporation|Bank\s+of\s+America|BofA)\b',
    r'\b(Goldman\s+Sachs\s+Group,?\s+Inc\.?|Goldman\s+Sachs|Goldman)\b',
    r'\b(Morgan\s+Stanley)\b',
    r'\b(Wells\s+Fargo\s+&?\s*Company|Wells\s+Fargo)\b',
    r'\b(Citigroup\s+Inc\.?|Citibank|Citi)\b',
    r'\b(Visa\s+Inc\.?)\b',
    r'\b(Mastercard\s+Incorporated|Mastercard)\b',
    r'\b(American\s+Express\s+Company|American\s+Express|AmEx)\b',
    r'\b(BlackRock,?\s+Inc\.?|BlackRock)\b',
    
    # Healthcare
    r'\b(Johnson\s+&\s+Johnson|J&J)\b',
    r'\b(UnitedHealth\s+Group\s+Incorporated|UnitedHealth|UHG)\b',
    r'\b(Pfizer\s+Inc\.?|Pfizer)\b',
    r'\b(AbbVie\s+Inc\.?|AbbVie)\b',
    r'\b(Merck\s+&?\s*Co\.?,?\s+Inc\.?|Merck)\b',
    r'\b(Eli\s+Lilly\s+and\s+Company|Eli\s+Lilly|Lilly)\b',
    r'\b(Bristol-Myers\s+Squibb\s+Company|Bristol-Myers\s+Squibb|BMS)\b',
    r'\b(Amgen\s+Inc\.?|Amgen)\b',
    
    # Consumer
    r'\b(Walmart\s+Inc\.?|Walmart|Wal-Mart)\b',
    r'\b(The\s+Coca-Cola\s+Company|Coca-Cola|Coke)\b',
    r'\b(PepsiCo,?\s+Inc\.?|PepsiCo|Pepsi)\b',
    r'\b(The\s+Procter\s+&\s+Gamble\s+Company|Procter\s+&\s+Gamble|P&G)\b',
    r'\b(Costco\s+Wholesale\s+Corporation|Costco)\b',
    r'\b(The\s+Home\s+Depot,?\s+Inc\.?|Home\s+Depot)\b',
    r'\b(Target\s+Corporation|Target)\b',
    
    # Energy
    r'\b(Exxon\s+Mobil\s+Corporation|ExxonMobil|Exxon)\b',
    r'\b(Chevron\s+Corporation|Chevron)\b',
    r'\b(ConocoPhillips)\b',
    r'\b(NextEra\s+Energy,?\s+Inc\.?|NextEra)\b',
    r'\b(Shell\s+plc|Royal\s+Dutch\s+Shell|Shell)\b',
    r'\b(BP\s+p\.?l\.?c\.?|BP)\b',
    
    # Industrials
    r'\b(Caterpillar\s+Inc\.?|Caterpillar|CAT)\b',
    r'\b(The\s+Boeing\s+Company|Boeing)\b',
    r'\b(United\s+Parcel\s+Service,?\s+Inc\.?|UPS)\b',
    r'\b(General\s+Electric\s+Company|General\s+Electric|GE)\b',
    r'\b(Lockheed\s+Martin\s+Corporation|Lockheed\s+Martin)\b',
    r'\b(Raytheon\s+Technologies|Raytheon|RTX)\b',
    r'\b(3M\s+Company|3M)\b',
    r'\b(Honeywell\s+International\s+Inc\.?|Honeywell)\b',
    
    # Generic company patterns (lower confidence)
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:Inc\.?|Corp(?:oration)?\.?|Co\.?|Ltd\.?|LLC|L\.?P\.?))\b',
]

# =============================================================================
# FINANCIAL METRIC PATTERNS
# =============================================================================

REVENUE_PATTERNS = [
    r'(?:total\s+)?(?:net\s+)?(?:revenue|sales|net\s+sales)\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
    r'\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?(?:total\s+)?(?:net\s+)?(?:revenue|sales)',
    r'(?:generated|reported|achieved)\s+(?:total\s+)?(?:net\s+)?(?:revenue|sales)\s+of\s+\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
]

NET_INCOME_PATTERNS = [
    r'(?:net\s+)?(?:income|earnings|profit)\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
    r'\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?(?:net\s+)?(?:income|earnings|profit)',
    r'(?:reported|achieved)\s+(?:net\s+)?(?:income|earnings)\s+of\s+\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
]

EPS_PATTERNS = [
    r'(?:earnings|EPS)\s+(?:per\s+share\s+)?(?:of\s+|was\s+)?\$?([\d]+(?:\.\d+)?)',
    r'\$?([\d]+\.\d+)\s+(?:per\s+share|EPS)',
    r'(?:diluted\s+)?EPS\s+(?:of\s+)?\$?([\d]+(?:\.\d+)?)',
]

CASH_FLOW_PATTERNS = [
    r'(?:operating\s+)?cash\s+flow\s+(?:of\s+|was\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
    r'(?:generated|produced)\s+\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?\s+(?:in\s+)?(?:operating\s+)?cash\s+flow',
    r'(?:free\s+)?cash\s+flow\s+(?:of\s+|was\s+|reached\s+)?\$?([\d,]+(?:\.\d+)?)\s*(billion|million|B|M)?',
]

ASSETS_PATTERNS = [
    r'(?:total\s+)?assets\s+(?:of\s+|exceeded\s+|reached\s+)?\$?([\d,]+(?:\.\d+)?)\s*(trillion|billion|million|T|B|M)?',
    r'\$?([\d,]+(?:\.\d+)?)\s*(trillion|billion|million|T|B|M)?\s+(?:in\s+)?(?:total\s+)?assets',
]

# =============================================================================
# RISK PATTERNS
# =============================================================================

RISK_PATTERNS = {
    "SupplyChainRisk": [
        r'supply\s+chain\s+(?:risk|disruption|challenges?|issues?)',
        r'(?:manufacturing|production)\s+(?:risk|disruption)',
        r'(?:supplier|vendor)\s+(?:risk|dependence|concentration)',
        r'logistics?\s+(?:risk|challenges?|disruption)',
        r'(?:inventory|shortage)\s+risk',
    ],
    "CurrencyRisk": [
        r'(?:currency|foreign\s+exchange|FX|forex)\s+(?:risk|exposure|volatility)',
        r'(?:exchange\s+rate)\s+(?:risk|fluctuation|volatility)',
        r'(?:hedging|currency\s+hedging)\s+(?:risk|exposure)',
    ],
    "RegulatoryRisk": [
        r'(?:regulatory|regulation|compliance)\s+(?:risk|challenges?|requirements?)',
        r'(?:antitrust|anti-trust)\s+(?:risk|investigation|scrutiny)',
        r'(?:government|governmental)\s+(?:risk|regulation)',
        r'(?:legal|litigation)\s+(?:risk|exposure|proceedings?)',
        r'(?:data\s+privacy|privacy)\s+(?:risk|regulation|compliance)',
    ],
    "GeopoliticalRisk": [
        r'(?:geopolitical|political)\s+(?:risk|tensions?|instability)',
        r'(?:trade\s+war|tariff)\s+(?:risk|impact|exposure)',
        r'(?:sanctions?)\s+(?:risk|exposure|impact)',
        r'(?:international|global)\s+(?:political\s+)?(?:risk|instability)',
    ],
    "CompetitiveRisk": [
        r'(?:competitive|competition)\s+(?:risk|pressure|threat)',
        r'(?:market\s+share)\s+(?:risk|loss|erosion)',
        r'(?:intense|increasing)\s+competition',
        r'(?:pricing)\s+(?:pressure|competition)',
    ],
    "CybersecurityRisk": [
        r'(?:cyber(?:security)?|cyber\s+security)\s+(?:risk|threat|attack)',
        r'(?:data\s+breach|security\s+breach)\s+(?:risk)?',
        r'(?:information\s+security|IT\s+security)\s+(?:risk|threat)',
        r'(?:hacking|ransomware|malware)\s+(?:risk|attack|threat)',
    ],
    "TechnologyRisk": [
        r'(?:technology|technological)\s+(?:risk|change|disruption|obsolescence)',
        r'(?:digital\s+)?(?:disruption|transformation)\s+(?:risk)?',
        r'(?:innovation|R&D)\s+(?:risk|challenges?)',
    ],
    "CreditRisk": [
        r'(?:credit)\s+(?:risk|exposure|losses?)',
        r'(?:default|counterparty)\s+(?:risk|exposure)',
        r'(?:loan|lending)\s+(?:risk|losses?)',
    ],
    "InterestRateRisk": [
        r'(?:interest\s+rate)\s+(?:risk|sensitivity|exposure)',
        r'(?:rate)\s+(?:risk|volatility|changes?)',
    ],
    "LiquidityRisk": [
        r'(?:liquidity)\s+(?:risk|challenges?|constraints?)',
        r'(?:funding|cash)\s+(?:risk|constraints?)',
    ],
    "EnvironmentalRisk": [
        r'(?:environmental|climate)\s+(?:risk|change|impact)',
        r'(?:ESG|sustainability)\s+(?:risk|challenges?)',
        r'(?:carbon|emissions?)\s+(?:risk|regulations?)',
    ],
    "ReputationalRisk": [
        r'(?:reputational|reputation|brand)\s+(?:risk|damage|impact)',
    ],
}

# =============================================================================
# PRODUCT PATTERNS
# =============================================================================

PRODUCT_PATTERNS = [
    # Apple Products
    r'\b(iPhone\s*(?:\d+)?(?:\s*Pro)?(?:\s*Max)?)\b',
    r'\b(iPad\s*(?:Pro|Air|Mini)?)\b',
    r'\b(Mac(?:Book)?(?:\s*(?:Pro|Air|Studio|Mini))?)\b',
    r'\b(Apple\s+Watch(?:\s*(?:Series\s*\d+|Ultra|SE))?)\b',
    r'\b(AirPods?(?:\s*(?:Pro|Max))?)\b',
    r'\b(Apple\s+TV(?:\+)?)\b',
    r'\b(iCloud)\b',
    r'\b(App\s+Store)\b',
    
    # Microsoft Products
    r'\b(Windows\s*(?:\d+)?)\b',
    r'\b(Azure)\b',
    r'\b(Microsoft\s+365|Office\s+365|M365)\b',
    r'\b(Xbox(?:\s*(?:Series\s*[XS]|One))?)\b',
    r'\b(LinkedIn)\b',
    r'\b(Teams)\b',
    r'\b(GitHub)\b',
    r'\b(Copilot)\b',
    
    # Google Products
    r'\b(Google\s+(?:Search|Cloud|Ads?|Maps|Chrome|Play|Drive|Workspace|Pixel))\b',
    r'\b(YouTube(?:\s*(?:TV|Music|Premium))?)\b',
    r'\b(Android)\b',
    r'\b(Waymo)\b',
    
    # Amazon Products
    r'\b(AWS|Amazon\s+Web\s+Services)\b',
    r'\b(Prime(?:\s*Video)?)\b',
    r'\b(Alexa)\b',
    r'\b(Kindle)\b',
    r'\b(Echo)\b',
    
    # Generic patterns
    r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\s+(?:platform|service|product|solution)s?)\b',
]

# =============================================================================
# PERSON PATTERNS
# =============================================================================

PERSON_PATTERNS = [
    # With title
    r'(?:CEO|Chief\s+Executive\s+Officer)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(?:the\s+)?(?:CEO|Chief\s+Executive\s+Officer)',
    r'(?:CFO|Chief\s+Financial\s+Officer)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s+(?:the\s+)?(?:CFO|Chief\s+Financial\s+Officer)',
    r'(?:Chairman|President|COO|CTO)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    
    # Known executives
    r'\b(Tim\s+Cook)\b',
    r'\b(Satya\s+Nadella)\b',
    r'\b(Sundar\s+Pichai)\b',
    r'\b(Andy\s+Jassy)\b',
    r'\b(Mark\s+Zuckerberg)\b',
    r'\b(Jensen\s+Huang)\b',
    r'\b(Elon\s+Musk)\b',
    r'\b(Jamie\s+Dimon)\b',
    r'\b(Warren\s+Buffett)\b',
    r'\b(Larry\s+Fink)\b',
]

# =============================================================================
# DATE AND PERIOD PATTERNS
# =============================================================================

DATE_PATTERNS = [
    r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
    r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
    r'\b(\d{4}-\d{2}-\d{2})\b',
    r'\b(Q[1-4]\s+\d{4})\b',
    r'\b(fiscal\s+(?:year\s+)?\d{4})\b',
    r'\b(FY\s*\d{4})\b',
    r'\b((?:first|second|third|fourth)\s+quarter\s+(?:of\s+)?\d{4})\b',
]

# =============================================================================
# MONETARY AMOUNT PATTERNS
# =============================================================================

MONETARY_PATTERNS = [
    r'\$\s*([\d,]+(?:\.\d+)?)\s*(trillion|billion|million|thousand|T|B|M|K)?',
    r'([\d,]+(?:\.\d+)?)\s*(trillion|billion|million|thousand)\s+dollars?',
    r'USD\s*([\d,]+(?:\.\d+)?)\s*(trillion|billion|million|T|B|M)?',
]

# =============================================================================
# PERCENTAGE PATTERNS
# =============================================================================

PERCENTAGE_PATTERNS = [
    r'([\d]+(?:\.\d+)?)\s*%',
    r'([\d]+(?:\.\d+)?)\s+percent',
    r'([\d]+(?:\.\d+)?)\s+percentage\s+points?',
]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compile_patterns(patterns: List[str]) -> List[Pattern]:
    """Compile regex patterns"""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def get_all_company_patterns() -> List[Pattern]:
    """Get all compiled company patterns"""
    return compile_patterns(COMPANY_PATTERNS)


def get_all_risk_patterns() -> Dict[str, List[Pattern]]:
    """Get all compiled risk patterns by type"""
    return {
        risk_type: compile_patterns(patterns)
        for risk_type, patterns in RISK_PATTERNS.items()
    }


def get_multiplier(unit: str) -> float:
    """Get numeric multiplier from unit string"""
    if not unit:
        return 1.0
    
    unit_lower = unit.lower()
    multipliers = {
        'trillion': 1_000_000_000_000,
        't': 1_000_000_000_000,
        'billion': 1_000_000_000,
        'b': 1_000_000_000,
        'million': 1_000_000,
        'm': 1_000_000,
        'thousand': 1_000,
        'k': 1_000,
    }
    return multipliers.get(unit_lower, 1.0)


def parse_monetary_value(text: str) -> Tuple[float, str]:
    """Parse monetary value from text, returning (value, currency)"""
    for pattern in MONETARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', ''))
            multiplier = get_multiplier(match.group(2) if len(match.groups()) > 1 else '')
            return value * multiplier, 'USD'
    return 0.0, 'USD'

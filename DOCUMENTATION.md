# Financial IDR Pipeline - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Loading & Sources](#data-loading--sources)
4. [Intelligent Document Recognition (IDR)](#intelligent-document-recognition-idr)
5. [Ontology Mapping](#ontology-mapping)
6. [Knowledge Graph Construction](#knowledge-graph-construction)
7. [Neo4j Integration](#neo4j-integration)
8. [GraphRAG Query Engine](#graphrag-query-engine)
9. [API Reference](#api-reference)
10. [Usage Examples](#usage-examples)

---

## System Overview

The **Financial IDR (Intelligent Document Recognition) Pipeline** is an end-to-end system that processes financial documents, extracts structured information, maps it to a formal ontology, and builds a queryable knowledge graph.

### Key Features
- 📄 **Multi-Source Data Ingestion**: SEC EDGAR filings (10-K, 10-Q, 8-K), FRED economic data
- 🔍 **Intelligent Document Classification**: Automatic document type detection
- 🧠 **Ontology-Guided Entity Extraction**: Extracts 50+ entity types (companies, financials, risks)
- 🔗 **Relation Extraction**: Identifies relationships between entities
- 📊 **Knowledge Graph**: Builds semantic network in Neo4j or in-memory
- 💬 **GraphRAG**: Natural language querying with LLM integration

### Technology Stack
- **Backend**: Python 3.11, Flask, Gunicorn
- **NLP**: spaCy (optional), Pattern-based extraction
- **Graph Database**: Neo4j 5.x (optional), NetworkX (in-memory)
- **Ontology**: RDF/OWL (Turtle format), FIBO-aligned
- **LLM**: OpenAI GPT-4, Anthropic Claude
- **Deployment**: Docker, Docker Compose

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FINANCIAL IDR PIPELINE                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  DATA SOURCES   │
├─────────────────┤
│ • SEC EDGAR     │────┐
│   (10-K/10-Q/8-K)    │
│ • FRED API      │────┤
│ • PDF Docs      │────┤
└─────────────────┘    │
                       ▼
           ┌───────────────────────┐
           │  DOCUMENT CLASSIFIER  │
           │  (Pattern Matching)   │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  ENTITY EXTRACTOR     │
           │  • Regex Patterns     │
           │  • spaCy NER          │
           │  • 50+ Entity Types   │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  RELATION EXTRACTOR   │
           │  • Pattern-based      │
           │  • Dependency parsing │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  ONTOLOGY MAPPER      │
           │  • Entity → Classes   │
           │  • Relation → Props   │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  KNOWLEDGE GRAPH      │
           │  • Neo4j (optional)   │
           │  • In-memory graph    │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  GRAPHRAG ENGINE      │
           │  • NL Query → Cypher  │
           │  • Context Retrieval  │
           │  • LLM Generation     │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │     REST API          │
           │  (Flask + Gunicorn)   │
           └───────────────────────┘
```

---

## Data Loading & Sources

### 1. SEC EDGAR Data Source

**Purpose**: Fetches SEC filings (10-K, 10-Q, 8-K) from the EDGAR database.

**Implementation**: [`src/data_sources/sec_edgar.py`](src/data_sources/sec_edgar.py)

**How it works**:
1. Connects to SEC EDGAR API
2. Searches for company filings by CIK (Central Index Key) or ticker
3. Downloads filing documents (HTML or text format)
4. Extracts sections (Item 1, Item 1A, Item 7, etc.)
5. Returns structured `FetchedDocument` objects

**Example**:
```python
from src.data_sources.sec_edgar import SECEdgarDataSource

source = SECEdgarDataSource({
    "user_agent": "Financial-IDR research@example.com"
})

companies = [
    {"ticker": "AAPL", "cik": "0000320193"},
    {"ticker": "MSFT", "cik": "0000789019"}
]

for document in source.fetch(companies=companies, filing_types=["10-K"], limit=1):
    print(f"Fetched: {document.metadata.document_type} - {document.metadata.source_id}")
    print(f"Sections: {list(document.sections.keys())}")
```

**Document Structure**:
```python
@dataclass
class FetchedDocument:
    content: str                    # Full document text
    metadata: DocumentMetadata      # Source, type, URL, date
    sections: Dict[str, str]       # Section name → Section content
    raw_data: Optional[bytes]      # Original raw data
```

### 2. FRED Economic Data Source

**Purpose**: Fetches macroeconomic data from Federal Reserve Economic Data (FRED).

**Implementation**: [`src/data_sources/fred_api.py`](src/data_sources/fred_api.py)

**Supported Indicators**:
- GDP, Unemployment Rate, Inflation (CPI)
- Federal Funds Rate, 10-Year Treasury Yield
- Consumer Confidence, PMI

**Example**:
```python
from src.data_sources.fred_api import FREDDataSource

source = FREDDataSource({"api_key": "your_fred_api_key"})

for document in source.fetch(series_ids=["GDP", "UNRATE"], limit=10):
    print(f"Indicator: {document.metadata.source_id}")
```

### 3. PDF Parser (Optional)

**Purpose**: Extracts text from PDF documents.

**Implementation**: [`src/data_sources/pdf_parser.py`](src/data_sources/pdf_parser.py)

**Libraries Used**: pdfplumber, PyPDF2

---

## Intelligent Document Recognition (IDR)

The IDR system consists of three main components:

### 1. Document Classifier

**File**: [`src/idr/document_classifier.py`](src/idr/document_classifier.py)

**Purpose**: Classifies financial documents into predefined categories.

**Supported Document Types**:
- Form 10-K (Annual Report)
- Form 10-Q (Quarterly Report)
- Form 8-K (Current Report)
- Proxy Statement (DEF 14A)
- Equity Research Reports
- Earnings Call Transcripts
- Press Releases
- Economic Data

**Classification Method**:

1. **Pattern Matching**: Uses regex patterns to identify document indicators
   ```python
   CLASSIFICATION_PATTERNS = {
       DocumentType.FORM_10K: {
           "patterns": [
               r"FORM\s+10-K",
               r"ANNUAL\s+REPORT\s+PURSUANT\s+TO\s+SECTION\s+13",
               r"For\s+the\s+fiscal\s+year\s+ended",
           ],
           "weight": 1.0,
           "ontology_class": "http://...#Form10K"
       }
   }
   ```

2. **Section Detection**: Identifies document sections (Item 1, Item 1A, etc.)
   - Boosts confidence for SEC filings
   - Validates document structure

3. **Confidence Scoring**: Combines pattern matches and section detection
   ```python
   score = (matched_patterns / total_patterns) * weight + section_overlap * 0.3
   ```

**Usage**:
```python
from src.idr.document_classifier import DocumentClassifier

classifier = DocumentClassifier()
result = classifier.classify(document_text)

print(f"Type: {result.document_type}")
print(f"Confidence: {result.confidence}")
print(f"Ontology Class: {result.ontology_class}")
print(f"Sections: {result.sections_detected}")
```

**Output**:
```python
@dataclass
class ClassificationResult:
    document_type: DocumentType
    ontology_class: str
    confidence: float
    matched_patterns: List[str]
    sections_detected: List[str]
    metadata: Dict[str, Any]
```

### 2. Entity Extractor

**File**: [`src/idr/entity_extractor.py`](src/idr/entity_extractor.py)

**Purpose**: Extracts named entities from financial documents.

**Entity Types** (50+ types):

**Company Entities**:
- Company, PublicCompany, Organization
- Person (executives, officers)
- Product, Service

**Financial Metrics**:
- Revenue, NetIncome, GrossProfit
- EarningsPerShare (EPS)
- TotalAssets, TotalLiabilities
- CashFlow, OperatingCashFlow, FreeCashFlow
- Financial Ratios (P/E, ROE, ROA)

**Risk Entities**:
- SupplyChainRisk
- CurrencyRisk (FX risk)
- RegulatoryRisk (compliance)
- GeopoliticalRisk (trade wars, sanctions)
- CompetitiveRisk
- CybersecurityRisk
- TechnologyRisk
- ReputationalRisk

**Economic Indicators**:
- GDP, InflationRate, UnemploymentRate
- InterestRate, FederalFundsRate

**General**:
- Date, MonetaryAmount, Percentage

**Extraction Methods**:

1. **Pattern-Based Extraction** (Primary):
   ```python
   ENTITY_PATTERNS = {
       "Company": [
           (r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(?:Inc\.|Corp\.)\b", 0.9),
           (r"\b(Apple|Microsoft|Amazon|Google)\b", 0.95),
       ],
       "Revenue": [
           (r"revenue\s+of\s+\$?([\d,]+\.?\d*)\s*(billion|million)?", 0.9),
       ],
       "SupplyChainRisk": [
           (r"supply\s+chain\s+(?:risk|disruption|challenge)", 0.85),
       ]
   }
   ```

2. **spaCy NER** (Optional, if installed):
   - ORG → Company
   - PERSON → Person
   - DATE → Date
   - MONEY → MonetaryAmount

3. **Entity Normalization**:
   ```python
   COMPANY_ALIASES = {
       "alphabet": "Alphabet Inc.",
       "google": "Alphabet Inc.",
       "apple": "Apple Inc.",
   }
   ```

4. **Property Extraction**:
   For financial metrics, extracts numeric values and multipliers:
   ```python
   # "revenue of $120.5 billion"
   {
       "value": 120500000000,
       "currency": "USD"
   }
   ```

**Section-Aware Extraction**:
Different sections focus on different entity types:
```python
section_entity_types = {
    "item_1": ["Company", "Product", "Person"],
    "item_1a": ["Company", "SupplyChainRisk", "CurrencyRisk", "RegulatoryRisk"],
    "item_7": ["Company", "Revenue", "NetIncome", "Percentage"],
    "item_8": ["Revenue", "NetIncome", "TotalAssets", "CashFlow"]
}
```

**Usage**:
```python
from src.idr.entity_extractor import EntityExtractor

extractor = EntityExtractor()
entities = extractor.extract(text)

for entity in entities:
    print(f"{entity.text} ({entity.entity_type}) - {entity.confidence}")
    print(f"  Ontology: {entity.ontology_class}")
    print(f"  Properties: {entity.properties}")
```

**Output**:
```python
@dataclass
class ExtractedEntity:
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    ontology_class: Optional[str]
    normalized_text: Optional[str]
    properties: Dict[str, Any]
    source: str  # "pattern" or "spacy"
```

### 3. Relation Extractor

**File**: [`src/idr/relation_extractor.py`](src/idr/relation_extractor.py)

**Purpose**: Extracts relationships between entities to build knowledge graph triples.

**Relation Types**:

**Company-Company**:
- COMPETES_WITH: "Apple competes with Samsung"
- PARTNERS_WITH: "Microsoft partners with OpenAI"
- ACQUIRED: "Meta acquired Instagram"
- SUBSIDIARY_OF: "YouTube, a subsidiary of Google"
- SUPPLIES_TO: "TSMC supplies to Apple"

**Company-Financial**:
- REPORTED: "Apple reported revenue of $120B"
- GENERATED: "Microsoft generated $50B in revenue"

**Company-Risk**:
- FACES_RISK: "Tesla faces supply chain risk"

**Company-Product**:
- MANUFACTURES: "Apple manufactures iPhone"
- SELLS: "Amazon sells AWS services"

**Person-Company**:
- CEO_OF: "Tim Cook, CEO of Apple"
- WORKS_AT: "Satya Nadella works at Microsoft"

**Company-Economic**:
- IMPACTED_BY: "Apple impacted by interest rates"

**Extraction Method**:

1. **Pattern-Based**:
   ```python
   RELATION_PATTERNS = {
       "COMPETES_WITH": [
           (r"(\w+)\s+competes?\s+with\s+(\w+)", "Company", "Company", 0.85),
       ],
       "REPORTED": [
           (r"(\w+)\s+reported\s+.*(\$[\d,\.]+\s*(?:billion|million)?)",
            "Company", "FinancialMetric", 0.85),
       ],
   }
   ```

2. **Entity Pair Matching**: Finds entity pairs in sentences

3. **Ontology Validation**: Ensures relation types match entity types
   ```python
   VALID_TYPE_PAIRS = {
       "COMPETES_WITH": [("Company", "Company")],
       "FACES_RISK": [
           ("Company", "SupplyChainRisk"),
           ("Company", "CurrencyRisk"),
       ],
   }
   ```

**Usage**:
```python
from src.idr.relation_extractor import RelationExtractor

extractor = RelationExtractor()
relations = extractor.extract(text, entities)

for rel in relations:
    print(f"{rel.subject.text} --[{rel.predicate}]--> {rel.object.text}")
    print(f"  Confidence: {rel.confidence}")
    print(f"  Ontology Property: {rel.ontology_property}")
```

**Output**:
```python
@dataclass
class ExtractedRelation:
    subject: ExtractedEntity
    predicate: str
    object: ExtractedEntity
    confidence: float
    ontology_property: Optional[str]
    source_text: str
    properties: Dict[str, Any]
```

---

## Ontology Mapping

**File**: [`src/idr/ontology_mapper.py`](src/idr/ontology_mapper.py)

**Purpose**: Maps extracted entities and relations to formal ontology classes and properties.

**Ontology Structure**:

### Namespaces

```turtle
@prefix sei-co:   <http://www.semanticdataservices.com/ontology/company#>
@prefix sei-fin:  <http://www.semanticdataservices.com/ontology/financial#>
@prefix sei-doc:  <http://www.semanticdataservices.com/ontology/document#>
@prefix sei-risk: <http://www.semanticdataservices.com/ontology/risk#>
@prefix sei-econ: <http://www.semanticdataservices.com/ontology/economic#>
@prefix fibo:     <https://spec.edmcouncil.org/fibo/ontology/>
```

### Class Hierarchy

**Company Classes** (sei-co):
```
Organization
  └── Company
       ├── PublicCompany
       ├── PrivateCompany
       └── Subsidiary
  └── Person
  └── Product
IndustrySector
  ├── TechnologySector
  ├── HealthcareSector
  ├── FinancialSector
  └── ...
```

**Financial Classes** (sei-fin):
```
FinancialMetric
  ├── Revenue
  ├── NetIncome
  ├── GrossProfit
  ├── OperatingIncome
  ├── EBITDA
  ├── EarningsPerShare
  ├── TotalAssets
  ├── TotalLiabilities
  ├── ShareholdersEquity
  ├── CashFlow
  ├── OperatingCashFlow
  └── FreeCashFlow
FinancialRatio
  ├── PriceToEarnings
  ├── DebtToEquity
  ├── ReturnOnEquity
  └── ReturnOnAssets
```

**Risk Classes** (sei-risk):
```
Risk
  ├── OperationalRisk
  │    ├── SupplyChainRisk
  │    └── CybersecurityRisk
  ├── FinancialRisk
  │    ├── CreditRisk
  │    ├── LiquidityRisk
  │    └── MarketRisk
  │         ├── CurrencyRisk
  │         └── InterestRateRisk
  ├── RegulatoryRisk
  ├── GeopoliticalRisk
  ├── CompetitiveRisk
  ├── TechnologyRisk
  ├── ReputationalRisk
  └── EnvironmentalRisk
```

**Document Classes** (sei-doc):
```
Document
  └── SECFiling
       ├── Form10K
       ├── Form10Q
       ├── Form8K
       └── ProxyStatement
  ├── EquityResearchReport
  ├── EarningsCallTranscript
  └── PressRelease
```

**Economic Classes** (sei-econ):
```
EconomicIndicator
  └── MacroeconomicIndicator
       ├── GDP
       ├── InflationRate
       ├── UnemploymentRate
       ├── InterestRate
       ├── FederalFundsRate
       ├── ConsumerConfidence
       ├── PMI
       └── TradeBalance
```

### Object Properties (Relationships)

```python
ONTOLOGY_PROPERTIES = {
    # Company relationships
    "competesWith": (Company, Company),
    "partnersWith": (Company, Company),
    "acquired": (Company, Company),
    "hasSubsidiary": (Company, Company),
    "isSubsidiaryOf": (Company, Company),
    "suppliesTo": (Organization, Company),
    "belongsToSector": (Company, IndustrySector),

    # Financial relationships
    "hasFinancialMetric": (Company, FinancialMetric),
    "reportedIn": (FinancialMetric, Document),

    # Risk relationships
    "facesRisk": (Company, Risk),
    "disclosedIn": (Risk, Document),

    # Person relationships
    "worksAt": (Person, Company),
    "isCEOOf": (Person, Company),

    # Economic relationships
    "impactedBy": (Company, EconomicIndicator),
}
```

### Mapping Process

**1. Entity Type to Ontology Class**:
```python
entity_type_mapping = {
    "Company": "http://www.semanticdataservices.com/ontology/company#PublicCompany",
    "Revenue": "http://www.semanticdataservices.com/ontology/financial#Revenue",
    "SupplyChainRisk": "http://www.semanticdataservices.com/ontology/risk#SupplyChainRisk",
}
```

**2. Relation Type to Ontology Property**:
```python
relation_type_mapping = {
    "COMPETES_WITH": "http://www.semanticdataservices.com/ontology/company#competesWith",
    "REPORTED": "http://www.semanticdataservices.com/ontology/financial#hasFinancialMetric",
    "FACES_RISK": "http://www.semanticdataservices.com/ontology/risk#facesRisk",
}
```

**3. Alias Resolution**:
```python
# "alphabet" → "http://...#PublicCompany" (Alphabet Inc.)
# "supply chain risk" → "http://...#SupplyChainRisk"
```

**Usage**:
```python
from src.idr.ontology_mapper import get_ontology_schema

schema = get_ontology_schema()

# Map entity type
ontology_class = schema.map_entity_type("Company")
# → "http://www.semanticdataservices.com/ontology/company#PublicCompany"

# Map relation type
ontology_property = schema.map_relation_type("COMPETES_WITH")
# → "http://www.semanticdataservices.com/ontology/company#competesWith"

# Validate relation
valid = schema.validate_relation("Company", "COMPETES_WITH", "Company")
# → True
```

---

## Knowledge Graph Construction

**File**: [`src/knowledge_graph/graph_builder.py`](src/knowledge_graph/graph_builder.py)

**Purpose**: Constructs a knowledge graph from extracted entities and relations.

### Graph Structure

**Nodes** (Entities):
```python
@dataclass
class GraphNode:
    id: str                        # Unique identifier
    labels: List[str]             # Neo4j labels (e.g., ["Entity", "Company"])
    properties: Dict[str, Any]    # Node properties
```

**Edges** (Relations):
```python
@dataclass
class GraphEdge:
    source_id: str                # Source node ID
    target_id: str                # Target node ID
    type: str                     # Relationship type
    properties: Dict[str, Any]    # Edge properties
```

### Node Creation Process

**1. Generate Unique ID**:
```python
def _generate_node_id(entity: ExtractedEntity) -> str:
    text = entity.normalized_text or entity.text
    text_normalized = text.lower().replace(" ", "_")
    hash_input = f"{entity.entity_type}_{text_normalized}"
    short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"{entity.entity_type}_{text_normalized}_{short_hash}"

# Example: "Company_apple_inc_a1b2c3d4"
```

**2. Assign Labels** (for Neo4j):
```python
labels = ["Entity", entity.entity_type]

# Add hierarchical labels
if entity.entity_type == "Revenue":
    labels.extend(["FinancialMetric"])
if entity.entity_type == "SupplyChainRisk":
    labels.extend(["Risk", "OperationalRisk"])

# Example: ["Entity", "Revenue", "FinancialMetric"]
```

**3. Set Properties**:
```python
properties = {
    "id": node_id,
    "name": entity.normalized_text or entity.text,
    "original_text": entity.text,
    "entity_type": entity.entity_type,
    "confidence": entity.confidence,
    "ontology_class": entity.ontology_class,
    "created_at": datetime.now().isoformat(),
    # Plus entity-specific properties
    "value": 120500000000,  # For financial metrics
    "currency": "USD"
}
```

### Edge Creation Process

**1. Create/Retrieve Nodes**:
```python
source_id = add_entity(relation.subject, document_id)
target_id = add_entity(relation.object, document_id)
```

**2. Create Edge**:
```python
edge = GraphEdge(
    source_id=source_id,
    target_id=target_id,
    type=relation.predicate,  # e.g., "COMPETES_WITH"
    properties={
        "confidence": relation.confidence,
        "ontology_property": relation.ontology_property,
        "evidence": relation.source_text,
        "source_document": document_id,
        "created_at": datetime.now().isoformat()
    }
)
```

### Graph Export Formats

**1. Cypher (Neo4j)**:
```python
graph_builder.to_cypher()
```

Output:
```cypher
// Create nodes
CREATE (:Company:Entity {
    id: "Company_apple_inc_a1b2c3d4",
    name: "Apple Inc.",
    entity_type: "Company",
    confidence: 0.95,
    ticker: "AAPL"
});

CREATE (:Revenue:FinancialMetric:Entity {
    id: "Revenue_120b_x1y2z3",
    name: "$120B Revenue",
    value: 120000000000,
    currency: "USD"
});

// Create relationships
MATCH (a:Company {id: "Company_apple_inc_a1b2c3d4"})
MATCH (b:Revenue {id: "Revenue_120b_x1y2z3"})
CREATE (a)-[:REPORTED {
    confidence: 0.85,
    source_document: "AAPL-10K-2024"
}]->(b);
```

**2. JSON**:
```python
graph_builder.to_json()
```

Output:
```json
{
  "nodes": [
    {
      "id": "Company_apple_inc_a1b2c3d4",
      "labels": ["Entity", "Company"],
      "properties": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "confidence": 0.95
      }
    }
  ],
  "edges": [
    {
      "source": "Company_apple_inc_a1b2c3d4",
      "target": "Revenue_120b_x1y2z3",
      "type": "REPORTED",
      "properties": {
        "confidence": 0.85
      }
    }
  ]
}
```

**3. RDF/Turtle**:
```python
graph_builder.to_rdf()
```

Output:
```turtle
@prefix sei-co: <http://www.semanticdataservices.com/ontology/company#> .
@prefix sei-fin: <http://www.semanticdataservices.com/ontology/financial#> .

sei-co:apple_inc_a1b2c3d4 a sei-co:PublicCompany ;
    rdfs:label "Apple Inc." ;
    sei-co:ticker "AAPL" .

sei-fin:revenue_120b_x1y2z3 a sei-fin:Revenue ;
    sei-fin:value "120000000000"^^xsd:decimal ;
    sei-fin:currency "USD" .

sei-co:apple_inc_a1b2c3d4 sei-fin:hasFinancialMetric sei-fin:revenue_120b_x1y2z3 .
```

### Graph Statistics

```python
stats = graph_builder.get_statistics()
```

Output:
```json
{
  "total_nodes": 1250,
  "total_edges": 3420,
  "nodes_by_type": {
    "Company": 145,
    "Revenue": 320,
    "Risk": 185,
    "Person": 78
  },
  "edges_by_type": {
    "REPORTED": 850,
    "COMPETES_WITH": 120,
    "FACES_RISK": 340
  }
}
```

---

## Neo4j Integration

### Connection Setup

**Configuration** (`.env`):
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

**Python Code**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)
```

### Loading Data into Neo4j

**Method 1: Via Cypher Export**:
```python
# Generate Cypher script
cypher_script = graph_builder.to_cypher()

# Save to file
with open("knowledge_graph.cypher", "w") as f:
    f.write(cypher_script)

# Execute in Neo4j
with driver.session() as session:
    session.run(cypher_script)
```

**Method 2: Direct Write**:
```python
# Create node
with driver.session() as session:
    session.run("""
        CREATE (c:Company:Entity {
            id: $id,
            name: $name,
            ticker: $ticker
        })
        """,
        id="Company_apple_inc_a1b2c3d4",
        name="Apple Inc.",
        ticker="AAPL"
    )
```

### Sample Neo4j Queries

**1. Find all companies**:
```cypher
MATCH (c:Company)
RETURN c.name, c.ticker
LIMIT 10
```

**2. Find company financial metrics**:
```cypher
MATCH (c:Company {name: "Apple Inc."})-[:REPORTED]->(m:FinancialMetric)
RETURN m.entity_type, m.value, m.currency
```

**3. Find risks faced by a company**:
```cypher
MATCH (c:Company {name: "Apple Inc."})-[:FACES_RISK]->(r:Risk)
RETURN r.entity_type, r.name, r.severity
```

**4. Find competitors**:
```cypher
MATCH (c1:Company {name: "Apple Inc."})-[:COMPETES_WITH]-(c2:Company)
RETURN c2.name
```

**5. Find supply chain relationships**:
```cypher
MATCH (supplier:Company)-[:SUPPLIES_TO]->(company:Company)
RETURN supplier.name, company.name
```

**6. Complex: Companies with high revenue facing supply chain risk**:
```cypher
MATCH (c:Company)-[:REPORTED]->(r:Revenue)
WHERE r.value > 50000000000
MATCH (c)-[:FACES_RISK]->(risk:SupplyChainRisk)
RETURN c.name, r.value, COUNT(risk) AS risk_count
ORDER BY r.value DESC
```

### Neo4j Indexes (Recommended)

```cypher
// Create indexes for better performance
CREATE INDEX company_name FOR (c:Company) ON (c.name);
CREATE INDEX company_ticker FOR (c:Company) ON (c.ticker);
CREATE INDEX entity_type FOR (e:Entity) ON (e.entity_type);
```

---

## GraphRAG Query Engine

**File**: [`src/graphrag/query_engine.py`](src/graphrag/query_engine.py)

**Purpose**: Natural language querying over the knowledge graph using LLMs.

### Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Query Parser   │  Convert NL → Structured Query
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Cypher Generator│  Generate Cypher query
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  Graph Query    │  Execute on Neo4j/in-memory
└─────────────────┘
     │
     ▼
┌─────────────────┐
│Context Retrieval│  Get relevant nodes/edges
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  LLM Generator  │  Generate final answer
└─────────────────┘
     │
     ▼
   Answer
```

### Query Examples

**Question**: "What was Apple's revenue in 2024?"

**Generated Cypher**:
```cypher
MATCH (c:Company {name: "Apple Inc."})-[:REPORTED]->(r:Revenue)
WHERE r.fiscalYear = "2024"
RETURN r.value, r.currency
```

**Answer**: "Apple reported revenue of $383 billion in fiscal year 2024."

---

**Question**: "What risks does Tesla face?"

**Generated Cypher**:
```cypher
MATCH (c:Company {name: "Tesla Inc."})-[:FACES_RISK]->(r:Risk)
RETURN r.entity_type, r.name, r.description
```

**Answer**: "Tesla faces several risks including supply chain risks related to battery manufacturing, regulatory risks around autonomous driving, and competitive risks from traditional automakers entering the EV market."

---

## API Reference

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 1. Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "pipeline_ready": false
  }
}
```

#### 2. Classify Document
```http
POST /api/classify
Content-Type: application/json

{
  "text": "FORM 10-K Annual Report..."
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "document_type": "10-K",
    "confidence": 0.95,
    "sections_detected": ["item_1", "item_1a", "item_7"],
    "ontology_class": "http://...#Form10K"
  }
}
```

#### 3. Extract Entities
```http
POST /api/extract/entities
Content-Type: application/json

{
  "text": "Apple reported revenue of $120 billion...",
  "entity_types": ["Company", "Revenue"]  # Optional
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "entity_count": 2,
    "entities": [
      {
        "text": "Apple",
        "type": "Company",
        "confidence": 0.95,
        "ontology_class": "http://...#PublicCompany"
      },
      {
        "text": "$120 billion",
        "type": "Revenue",
        "confidence": 0.9,
        "properties": {
          "value": 120000000000,
          "currency": "USD"
        }
      }
    ]
  }
}
```

#### 4. Extract Relations
```http
POST /api/extract/relations
Content-Type: application/json

{
  "text": "Apple competes with Samsung in smartphones..."
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "relation_count": 1,
    "relations": [
      {
        "subject": "Apple",
        "subject_type": "Company",
        "predicate": "COMPETES_WITH",
        "object": "Samsung",
        "object_type": "Company",
        "confidence": 0.85
      }
    ]
  }
}
```

#### 5. Process Full Document
```http
POST /api/process
Content-Type: application/json

{
  "text": "Full document text...",
  "document_id": "AAPL-10K-2024"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "document_id": "AAPL-10K-2024",
    "classification": {
      "type": "10-K",
      "confidence": 0.95
    },
    "extraction": {
      "entity_count": 450,
      "relation_count": 120
    },
    "graph": {
      "total_nodes": 450,
      "total_edges": 120
    }
  }
}
```

#### 6. Query Knowledge Graph
```http
POST /api/query
Content-Type: application/json

{
  "question": "What was Apple's revenue in 2024?"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "question": "What was Apple's revenue in 2024?",
    "answer": "Apple reported revenue of $383 billion in fiscal year 2024.",
    "cypher_query": "MATCH (c:Company {name: 'Apple Inc.'})-[:REPORTED]->(r:Revenue)...",
    "confidence": 0.92,
    "retrieved_nodes": 5,
    "retrieved_edges": 3
  }
}
```

#### 7. Get Companies
```http
GET /api/companies
GET /api/companies?sector=Technology
GET /api/companies/AAPL
```

#### 8. Export Graph
```http
GET /api/graph/export?format=json
GET /api/graph/export?format=cypher
```

---

## Usage Examples

### Example 1: Process a 10-K Filing

```python
from src.pipeline.idr_pipeline import FinancialIDRPipeline

# Initialize pipeline
pipeline = FinancialIDRPipeline(config_path="config/config.yaml")

# Configure companies
companies = [
    {"ticker": "AAPL", "cik": "0000320193"}
]

# Run pipeline
stats = pipeline.run(
    source_types=["sec_edgar"],
    companies=companies,
    max_documents=1
)

print(f"Processed {stats.documents_processed} documents")
print(f"Extracted {stats.total_entities} entities")
print(f"Extracted {stats.total_relations} relations")
print(f"Graph has {stats.total_nodes} nodes and {stats.total_edges} edges")

# Export graph
pipeline.export_graph("data/output", formats=["cypher", "json"])

# Query graph
result = pipeline.query("What risks does Apple face?")
print(result.answer)
```

### Example 2: Using the API

```python
import requests

# Classify document
response = requests.post(
    "http://localhost:5000/api/classify",
    json={"text": "FORM 10-K Annual Report..."}
)
print(response.json())

# Extract entities
response = requests.post(
    "http://localhost:5000/api/extract/entities",
    json={
        "text": "Apple reported revenue of $120 billion...",
        "entity_types": ["Company", "Revenue"]
    }
)
entities = response.json()["data"]["entities"]

# Query graph
response = requests.post(
    "http://localhost:5000/api/query",
    json={"question": "What was Apple's revenue?"}
)
print(response.json()["data"]["answer"])
```

### Example 3: Direct Component Usage

```python
# Document Classification
from src.idr.document_classifier import DocumentClassifier

classifier = DocumentClassifier()
result = classifier.classify(document_text)
print(f"Document Type: {result.document_type.value}")

# Entity Extraction
from src.idr.entity_extractor import EntityExtractor

extractor = EntityExtractor()
entities = extractor.extract(text)
for entity in entities:
    print(f"{entity.text} ({entity.entity_type})")

# Relation Extraction
from src.idr.relation_extractor import RelationExtractor

rel_extractor = RelationExtractor()
relations = rel_extractor.extract(text, entities)
for rel in relations:
    print(f"{rel.subject.text} --[{rel.predicate}]--> {rel.object.text}")

# Knowledge Graph
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder

graph = KnowledgeGraphBuilder()
graph.add_entities(entities, "doc-001")
graph.add_relations(relations, "doc-001")

# Export to Cypher
cypher = graph.to_cypher()
print(cypher)
```

---

## Configuration

**File**: `config/config.yaml`

```yaml
data_sources:
  sec_edgar:
    enabled: true
    user_agent: "Financial-IDR research@example.com"
    rate_limit: 10  # requests per second

  fred:
    enabled: true
    api_key: ${FRED_API_KEY}

idr:
  document_classifier:
    confidence_threshold: 0.5

  entity_extractor:
    confidence_threshold: 0.7
    use_spacy: true
    spacy_model: "en_core_web_sm"

  relation_extractor:
    confidence_threshold: 0.7
    max_sentence_length: 500

knowledge_graph:
  neo4j:
    uri: ${NEO4J_URI}
    user: ${NEO4J_USER}
    password: ${NEO4J_PASSWORD}

graphrag:
  llm_provider: "anthropic"  # or "openai"
  model: "claude-3-sonnet-20240229"
  temperature: 0.1
```

---

## Docker Deployment

### Quick Start

```bash
# 1. Build image
docker build -t financial-idr:latest .

# 2. Run API only
docker-compose up -d

# 3. Run with Neo4j
docker-compose --profile neo4j up -d

# 4. Run full stack (API + Neo4j + Redis + Nginx)
docker-compose --profile full up -d
```

### Access Points

- **API**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Bolt**: bolt://localhost:7687

---

## Summary

The Financial IDR Pipeline provides:

1. **Data Loading**: Multi-source document ingestion (SEC, FRED, PDF)
2. **IDR Processing**:
   - Document classification (10-K, 10-Q, etc.)
   - Entity extraction (50+ types: companies, financials, risks)
   - Relation extraction (15+ relation types)
3. **Ontology Mapping**: Formal semantic mappings to OWL/RDF ontology
4. **Knowledge Graph**: Neo4j or in-memory graph with Cypher export
5. **GraphRAG**: Natural language querying with LLM integration
6. **REST API**: Production-ready Flask API with Docker deployment

The system transforms unstructured financial documents into a structured, queryable knowledge graph aligned with formal ontologies, enabling semantic search and AI-powered insights.

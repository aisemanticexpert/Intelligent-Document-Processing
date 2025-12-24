# Financial IDR Pipeline

## Intelligent Document Recognition for Financial Documents with Knowledge Graph

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready **Intelligent Document Recognition (IDR)** system that processes financial documents (10-K, 10-Q, 8-K SEC filings), extracts entities and relationships using ontology-guided NER, and builds a queryable knowledge graph.

![Pipeline Architecture](docs/architecture.png)

## 🌟 Features

- **📄 Multi-Source Document Ingestion**
  - SEC EDGAR (10-K, 10-Q, 8-K filings)
  - FRED (Federal Reserve Economic Data)
  - Extensible data source architecture

- **🔍 Intelligent Document Recognition**
  - Automatic document classification
  - Section detection and parsing
  - Ontology-guided entity extraction
  - Relation extraction for knowledge graph

- **🧠 Financial Ontology**
  - Custom FIBO-aligned ontology
  - Company, Financial, Risk, Economic classes
  - 50+ entity types and relationships

- **📊 Knowledge Graph**
  - Neo4j and in-memory graph support
  - Cypher query generation
  - RDF/Turtle export

- **🔎 GraphRAG Query Engine**
  - Natural language question answering
  - Graph-based context retrieval
  - LLM integration (OpenAI, Anthropic)

## 📁 Project Structure

```
financial_idr/
├── config/
│   └── config.yaml              # Pipeline configuration
├── ontology/
│   ├── financial_ontology.ttl   # OWL/TTL ontology definition
│   └── namespaces.py            # Python namespace bindings
├── src/
│   ├── data_sources/            # Data source connectors
│   │   ├── base_source.py       # Abstract base class
│   │   ├── sec_edgar.py         # SEC EDGAR connector
│   │   └── fred_api.py          # FRED API connector
│   ├── idr/                     # IDR components
│   │   ├── document_classifier.py
│   │   ├── entity_extractor.py
│   │   └── relation_extractor.py
│   ├── knowledge_graph/
│   │   └── graph_builder.py     # Knowledge graph construction
│   ├── graphrag/
│   │   └── query_engine.py      # GraphRAG implementation
│   ├── pipeline/
│   │   └── idr_pipeline.py      # Main orchestration
│   └── utils/
│       └── helpers.py           # Utility functions
├── tests/                       # Unit tests
├── examples/                    # Example scripts
├── data/                        # Data directories
│   ├── raw/
│   ├── processed/
│   └── graphs/
├── main.py                      # Entry point
├── requirements.txt
├── setup.py
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/aisemanticexpert/Intelligent-Document-Processing-.git
cd Intelligent-Document-Processing-

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Run Demo

```bash
python main.py --demo
```

### Run Full Pipeline

```bash
# Process SEC filings
python main.py --config config/config.yaml --max-docs 10
```

## 📖 Usage Examples

### Basic Usage

```python
from src.pipeline.idr_pipeline import FinancialIDRPipeline

# Initialize pipeline
pipeline = FinancialIDRPipeline(config_path="config/config.yaml")

# Run pipeline
stats = pipeline.run(max_documents=5)

# Query the knowledge graph
result = pipeline.query("What risks does Apple face?")
print(result.answer)

# Export graph
pipeline.export_graph("data/graphs", formats=["json", "cypher"])
```

### Process Single Document

```python
from src.idr.document_classifier import DocumentClassifier
from src.idr.entity_extractor import EntityExtractor
from src.idr.relation_extractor import RelationExtractor
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder

# Load document
with open("apple_10k.txt", "r") as f:
    content = f.read()

# Classify
classifier = DocumentClassifier()
classification = classifier.classify(content)
print(f"Document Type: {classification.document_type}")

# Extract entities
extractor = EntityExtractor()
entities = extractor.extract(content)
print(f"Found {len(entities)} entities")

# Extract relations
relation_extractor = RelationExtractor()
relations = relation_extractor.extract(content, entities)
print(f"Found {len(relations)} relations")

# Build graph
graph = KnowledgeGraphBuilder()
graph.add_entities(entities)
graph.add_relations(relations)

# Export to Neo4j Cypher
print(graph.to_cypher())
```

### Custom Entity Extraction

```python
from src.idr.entity_extractor import EntityExtractor

extractor = EntityExtractor(config={
    "confidence_threshold": 0.8,
    "use_spacy": True,
})

# Extract specific entity types
entities = extractor.extract(
    text="Apple reported revenue of $394 billion...",
    entity_types=["Company", "Revenue", "MonetaryAmount"]
)

for entity in entities:
    print(f"{entity.text} ({entity.entity_type}) - {entity.confidence:.2%}")
```

## 🏗️ Architecture

### IDR Pipeline Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Data Source │────▶│ IDR Classifier│────▶│ Entity Extractor│
│ (SEC/FRED)  │     │              │     │ (Ontology-Guided)│
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ GraphRAG    │◀────│Knowledge Graph│◀────│Relation Extractor│
│ Query Engine│     │   Builder    │     │                 │
└─────────────┘     └──────────────┘     └─────────────────┘
```

### Ontology Namespaces

| Prefix | Namespace | Description |
|--------|-----------|-------------|
| sei-co | `http://www.semanticexpert.ai/ontology/company#` | Company entities |
| sei-fin | `http://www.semanticexpert.ai/ontology/financial#` | Financial metrics |
| sei-doc | `http://www.semanticexpert.ai/ontology/document#` | Document types |
| sei-risk | `http://www.semanticexpert.ai/ontology/risk#` | Risk factors |
| sei-econ | `http://www.semanticexpert.ai/ontology/economic#` | Economic indicators |

### Supported Entity Types

**Companies**: Company, PublicCompany, Subsidiary, Competitor, Supplier

**Financial Metrics**: Revenue, NetIncome, EarningsPerShare, TotalAssets, CashFlow, EBITDA

**Risks**: SupplyChainRisk, CurrencyRisk, RegulatoryRisk, GeopoliticalRisk, CompetitiveRisk, CybersecurityRisk, TechnologyRisk

**Documents**: Form10K, Form10Q, Form8K, EarningsCall, PressRelease

**Economic**: GDP, InflationRate, UnemploymentRate, InterestRate, ConsumerConfidence

## 🔧 Configuration

Edit `config/config.yaml`:

```yaml
# Data Sources
data_sources:
  sec_edgar:
    enabled: true
    user_agent: "YourApp/1.0 (your@email.com)"
    filing_types: ["10-K", "10-Q"]
  
  fred:
    enabled: true
    api_key: "${FRED_API_KEY}"

# Target Companies
companies:
  technology:
    - ticker: "AAPL"
      name: "Apple Inc."
      cik: "0000320193"

# IDR Settings
idr:
  entity_extractor:
    confidence_threshold: 0.75

# Knowledge Graph
knowledge_graph:
  backend: "neo4j"  # or "memory"
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "${NEO4J_PASSWORD}"
```

## 📊 Output Examples

### Extracted Entities

```json
{
  "text": "Apple",
  "entity_type": "Company",
  "confidence": 0.95,
  "ontology_class": "http://www.semanticexpert.ai/ontology/company#PublicCompany",
  "properties": {"ticker": "AAPL"}
}
```

### Extracted Relations

```json
{
  "subject": {"text": "Apple", "type": "Company"},
  "predicate": "FACES_RISK",
  "object": {"text": "supply chain risk", "type": "SupplyChainRisk"},
  "confidence": 0.85,
  "evidence": "Apple faces significant supply chain risk..."
}
```

### Generated Cypher

```cypher
MERGE (n:Entity:Company {id: 'Company_apple_abc123'})
SET n += {name: 'Apple Inc.', ticker: 'AAPL', confidence: 0.95};

MATCH (a:Entity {id: 'Company_apple_abc123'})
MATCH (b:Entity {id: 'SupplyChainRisk_supply_chain_risk_def456'})
MERGE (a)-[r:FACES_RISK]->(b)
SET r += {confidence: 0.85, evidence: '...'};
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_entity_extractor.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Rajesh Kumar Gupta**
- LinkedIn: [Rajesh Kumar Gupta](https://linkedin.com/in/rajesh-gupta)
- GitHub: [@aisemanticexpert](https://github.com/aisemanticexpert)

## 🙏 Acknowledgments

- [FIBO Ontology](https://spec.edmcouncil.org/fibo/) - Financial Industry Business Ontology
- [SEC EDGAR](https://www.sec.gov/edgar) - Electronic Data Gathering, Analysis, and Retrieval
- [FRED](https://fred.stlouisfed.org/) - Federal Reserve Economic Data
# Intelligent-Document-Processing-

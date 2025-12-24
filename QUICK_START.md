# Financial IDR - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Start the Docker Container

```bash
# Start API server
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f
```

**API is now running at**: `http://localhost:5000`

---

## 📝 Basic Usage Examples

### Test API Health

```bash
curl http://localhost:5000/api/health
```

### Classify a Document

```bash
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FORM 10-K Annual Report pursuant to Section 13 or 15(d) of the Securities Exchange Act of 1934 For the fiscal year ended September 30, 2024"
  }'
```

### Extract Entities

```bash
curl -X POST http://localhost:5000/api/extract/entities \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple Inc. reported revenue of $120 billion, an increase of 15% year-over-year. CEO Tim Cook stated that supply chain risks remain a concern."
  }'
```

**Response** (entities found):
- Apple Inc. (Company)
- $120 billion (Revenue)
- 15% (Percentage)
- Tim Cook (Person)
- supply chain risks (SupplyChainRisk)

### Extract Relations

```bash
curl -X POST http://localhost:5000/api/extract/relations \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple competes with Samsung in the smartphone market. Microsoft partners with OpenAI on AI initiatives."
  }'
```

**Response** (relations found):
- Apple --[COMPETES_WITH]--> Samsung
- Microsoft --[PARTNERS_WITH]--> OpenAI

### Process Full Document

```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your full document text here...",
    "document_id": "AAPL-10K-2024"
  }'
```

### List Companies

```bash
# All companies
curl http://localhost:5000/api/companies

# Filter by sector
curl http://localhost:5000/api/companies?sector=Technology

# Get specific company
curl http://localhost:5000/api/companies/AAPL
```

---

## 🐍 Python Examples

### Install Python Client

```bash
pip install requests
```

### Example Script

```python
import requests
import json

API_BASE = "http://localhost:5000/api"

# 1. Classify document
def classify_document(text):
    response = requests.post(
        f"{API_BASE}/classify",
        json={"text": text}
    )
    return response.json()

# 2. Extract entities
def extract_entities(text, entity_types=None):
    payload = {"text": text}
    if entity_types:
        payload["entity_types"] = entity_types

    response = requests.post(
        f"{API_BASE}/extract/entities",
        json=payload
    )
    return response.json()

# 3. Extract relations
def extract_relations(text):
    response = requests.post(
        f"{API_BASE}/extract/relations",
        json={"text": text}
    )
    return response.json()

# 4. Process full document
def process_document(text, doc_id):
    response = requests.post(
        f"{API_BASE}/process",
        json={
            "text": text,
            "document_id": doc_id
        }
    )
    return response.json()

# Usage
text = """
Apple Inc. reported revenue of $383 billion for fiscal year 2024,
an increase of 2% year-over-year. The company continues to face
supply chain risks and regulatory challenges in international markets.
"""

# Classify
result = classify_document(text)
print(f"Document Type: {result['data']['document_type']}")

# Extract entities
result = extract_entities(text)
for entity in result['data']['entities']:
    print(f"Entity: {entity['text']} ({entity['type']})")

# Extract relations
result = extract_relations(text)
for relation in result['data']['relations']:
    print(f"Relation: {relation['subject']} --[{relation['predicate']}]--> {relation['object']}")
```

---

## 📊 Run Complete Pipeline (Python)

```python
from src.pipeline.idr_pipeline import FinancialIDRPipeline

# Initialize pipeline
pipeline = FinancialIDRPipeline()

# Process a document
from src.data_sources.base_source import FetchedDocument, DocumentMetadata, DataSourceType

document = FetchedDocument(
    content="Your document text here...",
    metadata=DocumentMetadata(
        source_id="test-doc-001",
        source_type=DataSourceType.SEC_EDGAR,
        document_type="10-K",
        source_url="https://...",
        fetch_date="2024-12-18"
    ),
    sections={}
)

# Process through pipeline
result = pipeline.process_document(document)

print(f"Success: {result.success}")
print(f"Entities: {len(result.entities)}")
print(f"Relations: {len(result.relations)}")

# Export knowledge graph
pipeline.export_graph("data/output", formats=["cypher", "json"])
```

---

## 🗄️ Start with Neo4j

```bash
# Start API + Neo4j
docker-compose --profile neo4j up -d

# Access Neo4j Browser
open http://localhost:7474

# Default credentials:
# Username: neo4j
# Password: password123
```

### Load Data into Neo4j

```python
from src.pipeline.idr_pipeline import FinancialIDRPipeline

# Configure Neo4j
config = {
    "knowledge_graph": {
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password123"
        }
    }
}

pipeline = FinancialIDRPipeline(config=config)

# Process documents (will auto-load to Neo4j)
stats = pipeline.run(max_documents=10)

print(f"Loaded {stats.total_nodes} nodes into Neo4j")
```

### Query Neo4j

```cypher
// Find all companies
MATCH (c:Company)
RETURN c.name, c.ticker
LIMIT 10;

// Find Apple's financial metrics
MATCH (c:Company {name: "Apple Inc."})-[:REPORTED]->(m:FinancialMetric)
RETURN m.entity_type, m.value, m.currency;

// Find risks
MATCH (c:Company {name: "Apple Inc."})-[:FACES_RISK]->(r:Risk)
RETURN r.entity_type, r.name;

// Find competitors
MATCH (c1:Company {name: "Apple Inc."})-[:COMPETES_WITH]-(c2:Company)
RETURN c2.name;
```

---

## 📚 Common Use Cases

### Use Case 1: Analyze Company Risks

```bash
curl -X POST http://localhost:5000/api/extract/entities \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "text": "The company faces significant supply chain risks due to reliance on single-source manufacturing. Additionally, regulatory risks in international markets and cybersecurity threats pose ongoing challenges.",
  "entity_types": ["SupplyChainRisk", "RegulatoryRisk", "CybersecurityRisk"]
}
EOF
```

### Use Case 2: Extract Financial Metrics

```bash
curl -X POST http://localhost:5000/api/extract/entities \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "text": "For fiscal year 2024, total revenue was $383 billion, net income reached $97 billion, and earnings per share were $6.42.",
  "entity_types": ["Revenue", "NetIncome", "EarningsPerShare"]
}
EOF
```

### Use Case 3: Identify Company Relationships

```bash
curl -X POST http://localhost:5000/api/extract/relations \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "text": "Apple acquired Beats Electronics in 2014. The company competes directly with Samsung and Google in the smartphone market. Apple also partners with TSMC for chip manufacturing."
}
EOF
```

---

## 🛠️ Troubleshooting

### Container won't start?

```bash
# Check logs
docker-compose logs financial-idr

# Restart
docker-compose restart

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

### API returns 500 error?

```bash
# Check API logs
docker-compose logs -f financial-idr

# Test health endpoint
curl http://localhost:5000/api/health
```

### Neo4j connection issues?

```bash
# Check Neo4j is running
docker-compose --profile neo4j ps

# Test connection
docker exec financial-idr-neo4j cypher-shell -u neo4j -p password123 "RETURN 1"
```

---

## 📖 Next Steps

1. Read full documentation: [DOCUMENTATION.md](DOCUMENTATION.md)
2. Explore example scripts: `examples/`
3. Configure pipeline: `config/config.yaml`
4. Check ontology: `ontology/financial_ontology.ttl`

---

## 🆘 Support

- Issues: https://github.com/aisemanticexpert/Intelligent-Document-Processing-/issues
- Email: aisemanticexpert@gmail.com

---

## 📊 Pipeline Flow Summary

```
1. LOAD DATA
   └─> SEC EDGAR / FRED / PDF

2. CLASSIFY DOCUMENT
   └─> 10-K, 10-Q, 8-K, etc.

3. EXTRACT ENTITIES
   └─> Companies, Financials, Risks, People

4. EXTRACT RELATIONS
   └─> COMPETES_WITH, REPORTED, FACES_RISK

5. MAP TO ONTOLOGY
   └─> Entity Types → OWL Classes
   └─> Relation Types → OWL Properties

6. BUILD KNOWLEDGE GRAPH
   └─> Nodes (Entities) + Edges (Relations)

7. EXPORT / QUERY
   └─> Cypher (Neo4j)
   └─> JSON
   └─> RDF/Turtle
   └─> Natural Language (GraphRAG)
```

Happy Processing! 🚀

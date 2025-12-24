# 🐳 Financial IDR Pipeline - Docker Deployment Guide

## Quick Start

```bash
# Clone and enter directory
cd financial_idr

# Copy environment file and configure
cp .env.example .env

# Build and run
make quick-start

# Or manually:
docker-compose build
docker-compose up -d
```

**API available at:** http://localhost:5000

## Docker Commands

### Using Makefile (Recommended)

```bash
make help          # Show all available commands
make build         # Build Docker image
make up            # Start API server
make up-neo4j      # Start with Neo4j database
make up-full       # Start all services (Neo4j, Redis, Nginx)
make down          # Stop all containers
make logs          # View logs
make shell         # Open shell in container
make demo          # Run demo
make test          # Run tests
make clean         # Clean up
```

### Using Docker Compose Directly

```bash
# Build image
docker-compose build

# Start API only
docker-compose up -d

# Start with Neo4j
docker-compose --profile neo4j up -d

# Start all services
docker-compose --profile full up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Deployment Profiles

| Profile | Services | Command |
|---------|----------|---------|
| (default) | API only | `docker-compose up -d` |
| `neo4j` | API + Neo4j | `docker-compose --profile neo4j up -d` |
| `cache` | API + Redis | `docker-compose --profile cache up -d` |
| `proxy` | API + Nginx | `docker-compose --profile proxy up -d` |
| `full` | All services | `docker-compose --profile full up -d` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/classify` | POST | Classify document type |
| `/api/extract/entities` | POST | Extract entities |
| `/api/extract/relations` | POST | Extract relations |
| `/api/process` | POST | Full pipeline processing |
| `/api/query` | POST | GraphRAG query |
| `/api/companies` | GET | List companies |
| `/api/companies/<ticker>` | GET | Get company by ticker |
| `/api/ontology` | GET | Get ontology info |
| `/api/graph/stats` | GET | Graph statistics |
| `/api/graph/export` | GET | Export graph |

## Example API Calls

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Classify Document
```bash
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "FORM 10-K ANNUAL REPORT..."}'
```

### Extract Entities
```bash
curl -X POST http://localhost:5000/api/extract/entities \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple reported revenue of $394 billion..."}'
```

### Process Full Document
```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "document_id": "apple_10k_2024"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 5000 | API server port |
| `LOG_LEVEL` | INFO | Logging level |
| `NEO4J_URI` | bolt://neo4j:7687 | Neo4j connection URI |
| `NEO4J_USER` | neo4j | Neo4j username |
| `NEO4J_PASSWORD` | password123 | Neo4j password |
| `OPENAI_API_KEY` | - | OpenAI API key (optional) |
| `ANTHROPIC_API_KEY` | - | Anthropic API key (optional) |
| `SEC_USER_AGENT` | - | SEC EDGAR user agent |
| `FRED_API_KEY` | - | FRED API key |

## Production Deployment

```bash
# Use production override
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile full up -d
```

### Production Checklist

- [ ] Update `.env` with production values
- [ ] Set strong `NEO4J_PASSWORD`
- [ ] Configure SSL certificates in `docker/nginx/ssl/`
- [ ] Enable HTTPS in `nginx.conf`
- [ ] Set appropriate resource limits
- [ ] Configure logging and monitoring
- [ ] Set up backups for Neo4j data

## Volumes

| Volume | Path | Description |
|--------|------|-------------|
| `./data` | `/app/data` | Input/output data |
| `./logs` | `/app/logs` | Application logs |
| `./config` | `/app/config` | Configuration files |
| `neo4j-data` | `/data` | Neo4j database |
| `redis-data` | `/data` | Redis persistence |

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs financial-idr

# Check health
docker inspect financial-idr-api | grep -A 10 Health
```

### Neo4j connection issues
```bash
# Ensure Neo4j is healthy first
docker-compose --profile neo4j logs neo4j

# Test connection
docker exec financial-idr-api python -c "from neo4j import GraphDatabase; print('OK')"
```

### Memory issues
```bash
# Check resource usage
docker stats

# Adjust limits in docker-compose.prod.yml
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx                                │
│                    (Reverse Proxy)                           │
│                      Port 80/443                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Financial IDR API                          │
│                    (Flask + Gunicorn)                        │
│                       Port 5000                              │
└─────────┬───────────────────────────────────────┬───────────┘
          │                                       │
┌─────────▼─────────┐                   ┌────────▼────────┐
│      Neo4j        │                   │      Redis      │
│  (Graph Database) │                   │     (Cache)     │
│   Port 7474/7687  │                   │    Port 6379    │
└───────────────────┘                   └─────────────────┘
```

## License

MIT License - See LICENSE file for details.

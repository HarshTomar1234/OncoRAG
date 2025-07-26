# 🧬 OncoPilot MCP Collection-Centric System

**Production-grade oncology chatbot** using **official MCP Python SDK (FastMCP)** with collection-centric multi-agent architecture.

## 🏗️ **Architecture**

```
User Query → Query-Orchestrator → Intent Analysis → Agent Routing → Parallel Execution → Response Synthesis
```

### **Collection-Centric Agents**
- **🔬 CancerKnowledgeAgent** → `cancers` collection (9 tools)
- **🧬 GeneKnowledgeAgent** → `genes` collection (9 tools)  
- **💊 DrugKnowledgeAgent** → `drugs` collection (10 tools)
- **🇮🇳 DrugIndiaKnowledgeAgent** → `drugs_india` collection (10 tools)

### **External MCP Servers**
- **📚 PubMed Server** → Literature search via NCBI E-utilities
- **🔬 ClinicalTrials Server** → Trial data via ClinicalTrials.gov API
- **🌐 WebSearch Server** → Web search via SerpAPI

## 📋 **Prerequisites**

- **Python 3.8+**
- **MongoDB** (local or cloud)
- **Docker & Docker Compose** (for containerized deployment)
- **Git**

## ⚡ **Quick Start**

### **Option 1: Development Setup (Recommended)**

```bash
# 1. Clone and navigate
git clone <repository>
cd "Oncology MCP"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp deployment/env.example .env
# Edit .env with your MongoDB URI and API keys

# 4. Test collection agents
python test_collection_agents.py

# 5. Run individual MCP servers (in separate terminals)
python mcp_servers/cancer_knowledge_server.py    # Port 8001
python mcp_servers/gene_knowledge_server.py      # Port 8002  
python mcp_servers/drug_knowledge_server.py      # Port 8003
python mcp_servers/drug_india_knowledge_server.py # Port 8004

# 6. Start web service
python app.py                                    # Port 8000
```

### **Option 2: Docker Deployment**

```bash
cd deployment

# Development deployment
./deploy.sh dev

# Production deployment  
./deploy.sh prod

# Check health
./deploy.sh health

# View logs
./deploy.sh logs

# Stop services
./deploy.sh stop
```

## 🧪 **Testing**

### **Collection Agent Testing**
```bash
python test_collection_agents.py
```
**Expected Output:**
```
🧬 Cancer Information (cancers collection)
✅ Status: Success (0.05s)
📋 Summary: Found cancer information for: lung cancer
🤖 Agents: CancerKnowledgeAgent
📊 CancerKnowledgeAgent → cancers collection
```

### **Web Service Testing**
```bash
# Health check
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/agents

# Test query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are biomarkers for lung cancer?"}'
```

### **Individual Agent Testing**
```bash
# Test cancer agent directly
curl http://localhost:8001/tools  # List tools

# Test with MCP Inspector
uv run mcp dev mcp_servers/cancer_knowledge_server.py
```

## 🛠️ **Development**

### **FastMCP Server Pattern**
```python
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("AgentName")

@mcp.tool()
async def search_function(query: str) -> str:
    """Tool description."""
    # Implementation
    return json.dumps(result)

# Run server
if __name__ == "__main__":
    mcp.run()
```

### **Adding New Tools**
1. Add `@mcp.tool()` decorator to function
2. Use async functions for database operations
3. Return JSON strings with structured data
4. Include error handling

### **Collection Schema**
Refer to `DB context for Agents + MCP.md` for detailed field descriptions:
- **cancers**: Cancer info, biomarkers, guidelines, survival rates
- **genes**: Gene mutations, drug associations, prognosis, trials
- **drugs**: Global drug data, efficacy, safety, approvals
- **drugs_india**: India-specific drugs, CDSCO approvals, brands

## 📚 **API Documentation**

### **Main Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/chat` | POST | Process oncology queries |
| `/chat/stream` | POST | Streaming chat responses |
| `/agents` | GET | List available agents |
| `/collections` | GET | MongoDB collections info |
| `/examples` | GET | Example queries |

### **Chat Request Format**
```json
{
  "query": "What are EGFR mutation treatments?",
  "session_id": "optional_session_id"
}
```

### **Chat Response Format**
```json
{
  "response": {
    "status": "success",
    "summary": "Retrieved information from 2 collections...",
    "agents_used": ["GeneKnowledgeAgent", "DrugKnowledgeAgent"],
    "detailed_responses": [...]
  },
  "timestamp": "2025-01-15T10:30:00"
}
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
MONGODB_URI=mongodb://localhost:27017/oncology_db
DATABASE_NAME=oncology_db

# API Keys (Optional)
NCBI_API_KEY=your_key
SERPAPI_KEY=your_key  
OPENAI_API_KEY=your_key

# Service
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### **MongoDB Setup**
```bash
# Local MongoDB
mongod --dbpath /data/db

# Or use Docker
docker run -d -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7.0
```

## 🚀 **Deployment**

### **Docker Compose Services**
```yaml
services:
  mongodb:          # MongoDB database
  cancer-agent:     # Cancer Knowledge Server (8001)
  gene-agent:       # Gene Knowledge Server (8002)
  drug-agent:       # Drug Knowledge Server (8003)
  drug-india-agent: # Drug India Server (8004)
  pubmed-server:    # PubMed Server (8005)
  clinicaltrials-server: # Clinical Trials (8006)
  websearch-server: # Web Search Server (8007)
  web-service:      # Main FastAPI App (8000)
```

### **Production Checklist**
- [ ] Set strong MongoDB passwords
- [ ] Configure API keys for external services
- [ ] Set up SSL/TLS certificates
- [ ] Configure load balancers
- [ ] Set up monitoring and logging
- [ ] Configure backups

## 🎯 **Usage Examples**

### **Cancer Information**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are biomarkers for lung cancer?"}'
```

### **Gene Analysis**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "EGFR mutation prognosis and treatment options"}'
```

### **Drug Information**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Pembrolizumab efficacy and side effects"}'
```

### **India-Specific Queries**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Is imatinib approved by CDSCO in India?"}'
```

## 🔍 **Query Processing Flow**

1. **User Query** → FastAPI endpoint
2. **Query Analysis** → Intent extraction & entity recognition
3. **Agent Routing** → Determine which collection agents to call
4. **Parallel Execution** → Call multiple FastMCP servers simultaneously  
5. **Result Collection** → Gather responses from agents
6. **Response Synthesis** → Generate coherent markdown response
7. **Cache Storage** → Store results for future queries

## 📊 **Monitoring**

### **Health Checks**
```bash
# Service health
curl http://localhost:8000/health

# Individual agent health  
curl http://localhost:8001/health  # Cancer agent
curl http://localhost:8002/health  # Gene agent
curl http://localhost:8003/health  # Drug agent
curl http://localhost:8004/health  # Drug India agent
```

### **Logs**
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f cancer-agent
docker-compose logs -f web-service
```

## 🛡️ **Security**

- **No authentication** required (as per requirements)
- **Input sanitization** for MongoDB queries
- **Error handling** prevents information leakage
- **Rate limiting** can be added via reverse proxy
- **CORS** configured for web access

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Import Error: cannot import name 'Server' from 'mcp'**
   ```bash
   pip install --upgrade mcp>=1.11.0
   ```

2. **MongoDB Connection Failed**
   ```bash
   # Check MongoDB is running
   mongosh --eval "db.runCommand('ping')"
   ```

3. **Port Already in Use**
   ```bash
   # Find and kill process using port
   lsof -ti:8000 | xargs kill -9
   ```

4. **FastMCP Server Not Starting**
   ```bash
   # Check logs for specific error
   python mcp_servers/cancer_knowledge_server.py
   ```

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python app.py
```

## 📁 **Project Structure**

```
Oncology MCP/
├── agents/
│   └── query_orchestrator.py     # Main orchestrator
├── mcp_servers/
│   ├── cancer_knowledge_server.py    # Cancer agent
│   ├── gene_knowledge_server.py      # Gene agent  
│   ├── drug_knowledge_server.py      # Drug agent
│   ├── drug_india_knowledge_server.py # Drug India agent
│   ├── pubmed_server.py              # PubMed integration
│   ├── clinicaltrials_server.py      # Clinical trials
│   └── websearch_server.py           # Web search
├── deployment/
│   ├── docker-compose.yml           # Container orchestration
│   ├── Dockerfile.mcp-server        # MCP server container
│   ├── Dockerfile.web-service       # Web service container
│   ├── deploy.sh                    # Deployment script
│   └── env.example                  # Environment template
├── app.py                           # FastAPI web service
├── models.py                        # Pydantic data models  
├── config.py                        # Configuration management
├── test_collection_agents.py        # Testing script
└── requirements.txt                 # Python dependencies
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Follow FastMCP patterns for new agents
4. Add tests for new functionality
5. Submit pull request

## 📄 **License**

MIT License - see LICENSE file for details.

---

## 🔗 **Related Documentation**

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://ai.pydantic.dev/mcp/server/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 
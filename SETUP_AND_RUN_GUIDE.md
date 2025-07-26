# OncoPilot MCP System - Setup and Run Guide

## 🧬 Overview

The OncoPilot MCP system is a **collection-centric multi-agent architecture** that provides intelligent oncology query processing across multiple data sources:

- **Database Collections**: `cancers`, `genes`, `drugs`, `drugs_india`
- **External Sources**: Web search, PubMed literature, Clinical trials
- **Interface**: Streamlit chat interface for interactive queries

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB access (configured in environment)
- Internet connection for external sources

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Install core requirements
pip install -r requirements_streamlit.txt

# Install MCP framework (required)
pip install mcp

# Optional: Install FastMCP for enhanced functionality
# Check MCP Python SDK documentation for latest installation
```

### Step 2: Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp environment_template.env .env
   ```

2. **Edit `.env` file with your configurations:**
   ```env
   # Required: MongoDB connection
   MONGODB_URI=your_mongodb_connection_string
   DATABASE_NAME=your_database_name
   
   # Optional: External API keys for enhanced functionality
   SERPAPI_KEY=your_serpapi_key
   NCBI_API_KEY=your_ncbi_api_key
   ```

### Step 3: Run the Application

```bash
# Using the provided runner script
python run_streamlit.py

# Or run Streamlit directly
streamlit run streamlit_app.py
```

The application will be available at: **http://localhost:8501**

## 📁 Environment File Configuration

### Required Settings

```env
# Database Connection (REQUIRED)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=oncopilot-agent
```

### Optional Settings

```env
# External API Keys (Optional but recommended)
SERPAPI_KEY=your_serpapi_key_here        # For enhanced web search
NCBI_API_KEY=your_ncbi_api_key_here      # For better PubMed access

# Performance Tuning
MAX_CONCURRENT_QUERIES=5
MAX_ENTITIES_PER_QUERY=5
MAX_INTENTS_PER_QUERY=8

# Feature Toggles
ENABLE_WEB_SEARCH=true
ENABLE_PUBMED_SEARCH=true
ENABLE_CLINICAL_TRIALS=true
```

## 🔧 System Architecture & Prompt Usage

### System Prompt Integration

**Important Note**: The `system_prompt.md` file is **documentation**, not an actual prompt fed to an LLM. The intelligence is built directly into the `EnhancedQueryOrchestrator` code through:

1. **Multi-Collection Detection Patterns**:
   ```python
   multi_collection_patterns = [
       (r"efficacy.*(?:india|indian|cdsco)", ["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
       (r"(?:msi-h|microsatellite.*colorectal)", ["CancerKnowledgeAgent", "DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
   ]
   ```

2. **Entity Extraction Logic**: 
   - Known medical terms dictionaries
   - Regex patterns for drug names, gene names
   - Context-aware cancer type detection

3. **Tool Selection Intelligence**:
   - Query context analysis → appropriate tool selection
   - Multi-agent coordination for complex queries

### Query Processing Flow

```
User Query → Enhanced Analysis → Multi-Agent Routing → Response Synthesis
     ↓              ↓                    ↓                    ↓
"MSI-H efficacy"  Extract:          Route to:          Synthesize from:
"in India"        - MSI-H           - DrugAgent         - drugs collection  
                  - efficacy        - DrugIndiaAgent    - drugs_india collection
                  - India           - CancerAgent       - cancers collection
```

## 🧪 Testing Multi-Collection Queries

### Example Queries to Test

1. **Multi-Collection Database Queries:**
   ```
   "Efficacy of pembrolizumab for MSI-H colorectal cancer in India"
   → Expected: drugs + drugs_india collections
   
   "EGFR mutation treatment options in India"
   → Expected: genes + drugs + drugs_india collections
   
   "HER2 positive breast cancer biomarkers and available drugs"
   → Expected: cancers + genes + drugs collections
   ```

2. **External Source Integration:**
   ```
   "Latest research on immunotherapy for lung cancer"
   → Expected: PubMed + Web Search
   
   "Recent clinical trials for BRAF inhibitors"  
   → Expected: Clinical Trials + PubMed
   ```

3. **Single Collection Queries:**
   ```
   "What are the biomarkers for lung cancer?"
   → Expected: cancers collection
   
   "Pembrolizumab side effects"
   → Expected: drugs collection
   ```

## 🎯 Key Features

### 1. Multi-Collection Intelligence
- Automatically detects when queries need multiple database collections
- Synthesizes responses from `drugs` + `drugs_india` for India-specific efficacy queries
- Combines `cancers` + `genes` + `drugs` for comprehensive biomarker-treatment queries

### 2. External Source Integration
- **Web Search**: Latest medical news and updates
- **PubMed**: Scientific literature and research papers
- **Clinical Trials**: Ongoing and completed clinical studies

### 3. Query Complexity Analysis
- Identifies query complexity: "multi-collection" vs "single-source"
- Provides metadata on agents used, collections queried
- Shows successful vs failed responses

### 4. Interactive Chat Interface
- Real-time query processing with progress indicators
- Query history with expandable detailed results
- Example queries organized by category
- Download functionality for detailed responses

## 🔍 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```
   Error: MongoDB connection failed
   Solution: Check MONGODB_URI in .env file
   ```

2. **Missing Dependencies**
   ```
   Error: ModuleNotFoundError
   Solution: pip install -r requirements_streamlit.txt
   ```

3. **MCP Framework Not Found**
   ```
   Error: No module named 'mcp'
   Solution: pip install mcp
   ```

4. **Streamlit Port Already in Use**
   ```
   Error: Port 8501 is already in use
   Solution: Change STREAMLIT_PORT in .env or kill existing process
   ```

### Debug Mode

Enable debug logging in `.env`:
```env
LOG_LEVEL=DEBUG
ENABLE_MCP_DEBUG=true
DEBUG_MODE=true
```

## 📊 Performance Optimization

### Default Settings (Optimized for Responsiveness)
- **Max Entities per Query**: 5
- **Max Intents per Query**: 8
- **Query Cache**: Enabled (1 hour TTL)
- **Concurrent Queries**: 5

### For High-Volume Usage
```env
MAX_CONCURRENT_QUERIES=10
CACHE_TTL_SECONDS=7200
RATE_LIMIT_PER_MINUTE=120
```

## 🔄 System Monitoring

The Streamlit interface provides real-time monitoring:
- **System Status**: Active/Inactive agents
- **Query Statistics**: Success/failure rates
- **Collection Usage**: Which collections are being queried
- **Response Times**: Performance metrics

## 🆘 Support

For issues or questions:
1. Check this guide and the system documentation
2. Review the `system_prompt.md` for architecture details
3. Enable debug mode for detailed logging
4. Examine the query orchestrator logs for routing issues

## 🎉 Success Indicators

The system is working correctly when:
1. ✅ Streamlit app loads without errors
2. ✅ MongoDB connection successful
3. ✅ Query orchestrator initializes all 7 agents
4. ✅ Multi-collection queries return comprehensive results
5. ✅ Example queries work as expected 
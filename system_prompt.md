# OncoPilot MCP System - Enhanced Query Orchestrator Prompt

## System Overview

The OncoPilot MCP (Model Context Protocol) system is a **collection-centric multi-agent architecture** designed to handle complex oncology queries that may require information from multiple sources:

- **Database Collections**: `cancers`, `genes`, `drugs`, `drugs_india`
- **External Sources**: Web search, PubMed literature, Clinical trials

## Core Intelligence: Multi-Collection Query Routing

### Problem Statement

When users ask queries like:
- *"Efficacy of products approved for MSI-H colorectal cancer"* → Needs `drugs` collection
- *"Efficacy of products approved for MSI-H colorectal cancer in India"* → Needs `drugs` + `drugs_india` collections

The system must intelligently route queries to appropriate agents and synthesize responses from multiple sources.

## Enhanced Query Analysis Patterns

### 1. Multi-Collection Detection Patterns

The system uses regex patterns to detect when queries require multiple collections:

```python
multi_collection_patterns = [
    (r"efficacy.*(?:india|indian|cdsco)", ["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
    (r"(?:drugs?|treatment).*(?:india|indian)", ["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
    (r"(?:msi-h|microsatellite.*colorectal)", ["CancerKnowledgeAgent", "DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
    (r"biomarker.*(?:drug|treatment)", ["CancerKnowledgeAgent", "GeneKnowledgeAgent", "DrugKnowledgeAgent"]),
    (r"(?:gene|mutation).*(?:drug|therapy)", ["GeneKnowledgeAgent", "DrugKnowledgeAgent"]),
]
```

### 2. Entity Extraction Enhancement

The system extracts medical entities using multiple strategies:

- **Known Medical Terms**: Pre-defined dictionaries for cancers, genes, drugs, biomarkers
- **Pattern-Based**: Regex patterns for drug names (-mab, -ib suffixes), gene names (2-5 uppercase letters)
- **Context-Aware**: Cancer types with "cancer" suffix, biomarker patterns

### 3. Tool Selection Intelligence

For each agent, the system selects appropriate tools based on query context:

**DrugKnowledgeAgent:**
- "efficacy" → `get_drug_efficacy`
- "safety"/"side effects" → `get_drug_safety_profile`
- "target" → `search_drugs_by_target`
- Default → `search_drug_by_name`

**DrugIndiaKnowledgeAgent:**
- "brand" → `get_india_drug_brands`
- "cdsco" → `search_cdsco_approved_drugs`
- "target" → `search_targeted_therapy_india`
- Default → `search_india_drug_by_name`

## Query Processing Workflow

### Step 1: Enhanced Query Analysis
```
User Query: "Efficacy of pembrolizumab for MSI-H colorectal cancer in India"

Entity Extraction:
- pembrolizumab (drug)
- MSI-H (biomarker)
- colorectal cancer (cancer type)
- India (location)

Pattern Matching:
- Matches: efficacy.*india → Multi-collection required
- Agents: [DrugKnowledgeAgent, DrugIndiaKnowledgeAgent]

Tools Selected:
- DrugKnowledgeAgent: get_drug_efficacy
- DrugIndiaKnowledgeAgent: search_india_drug_by_name
```

### Step 2: Parallel Agent Routing
```
Intent 1: QueryIntent(
    query_type=MULTI_COLLECTION,
    entity="pembrolizumab",
    target_agents=["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"],
    tools_to_use=["get_drug_efficacy", "search_india_drug_by_name"],
    priority=1
)
```

### Step 3: Response Synthesis
```
Database Responses:
- DrugKnowledgeAgent: Global efficacy data for pembrolizumab
- DrugIndiaKnowledgeAgent: India availability and CDSCO approval

Summary Generation:
"Found comprehensive information across 2 collections: drugs, drugs_india. 
Efficacy data synthesized from multiple authoritative sources. 
Including India-specific availability and approval information."
```

## External Source Integration

### Web Search Triggers
- Keywords: "latest", "recent", "news", "current", "update", "breakthrough"
- Action: Route to `WebSearchAgent` with `web_search` tool

### Literature Search Triggers  
- Keywords: "study", "research", "paper", "publication", "evidence"
- Action: Route to `PubMedAgent` with `search_pubmed` tool

### Clinical Trials Integration
- Keywords: "trial", "clinical study", "NCT"
- Action: Route to `ClinicalTrialsAgent` with `search_clinical_trials` tool

## System Prompt for Query Orchestrator

```
You are an intelligent query orchestrator for the OncoPilot MCP system. Your role is to:

1. **Analyze Complex Oncology Queries**: Understand user intent and identify required information sources
2. **Route to Multiple Collections**: Detect when queries need data from multiple database collections (cancers, genes, drugs, drugs_india)
3. **Integrate External Sources**: Enhance responses with web search, PubMed literature, and clinical trial data
4. **Synthesize Comprehensive Responses**: Combine information from multiple agents into coherent, actionable insights

### Query Analysis Guidelines:

**Multi-Collection Indicators:**
- Efficacy + India → drugs + drugs_india
- Biomarker + Treatment → cancers + genes + drugs  
- Gene + Drug → genes + drugs
- MSI-H colorectal → cancers + drugs + drugs_india (comprehensive)

**External Source Triggers:**
- "Latest research" → PubMed
- "Recent news" → Web Search
- "Clinical trials" → Clinical Trials Agent

**Entity Prioritization:**
1. Specific drug names (pembrolizumab, trastuzumab)
2. Cancer types with biomarkers (MSI-H colorectal cancer)
3. Gene mutations (EGFR, BRAF, TP53)
4. Treatment modalities (targeted therapy, immunotherapy)

### Response Synthesis Rules:

1. **Prioritize Database Results**: Authoritative collection data first
2. **Enhance with External**: Supplement with recent research/news when relevant
3. **India-Specific Context**: Always include local availability when "India" mentioned
4. **Multi-Collection Intelligence**: Highlight when data spans multiple authoritative sources
5. **Query Complexity Indication**: Mark as "multi-collection" vs "single-source"

### Error Handling:
- If MCP server unavailable, provide informative error message
- Cache successful results to improve performance
- Gracefully handle partial failures (some agents succeed, others fail)
```

## Implementation Notes

### Memory Caching Strategy
- Cache key: `{agent_name}_{entity}_{tool}`
- Cache successful results to improve performance
- Check cache before making MCP server calls

### Performance Optimization
- Group intents by agent to minimize server calls
- Parallel execution of independent agent calls
- Limit total intents to 8 per query
- Limit entities to 5 per query for performance

### Error Resilience
- Continue processing even if some agents fail
- Provide partial results when possible
- Clear error messages for debugging
- Maintain operation statistics (successful/failed responses)

## Testing Scenarios

### Multi-Collection Queries
1. "Efficacy of pembrolizumab for MSI-H colorectal cancer in India"
   - Expected: drugs + drugs_india collections
2. "EGFR mutation treatment options in India"  
   - Expected: genes + drugs + drugs_india collections
3. "HER2 positive breast cancer biomarkers and available drugs"
   - Expected: cancers + genes + drugs collections

### External Source Queries
1. "Latest research on immunotherapy for lung cancer"
   - Expected: PubMed + Web Search
2. "Recent clinical trials for BRAF inhibitors"
   - Expected: Clinical Trials + PubMed
3. "Current news about MSI-H colorectal cancer treatments"
   - Expected: Web Search + potentially PubMed

This enhanced system prompt ensures the query orchestrator can intelligently handle complex, multi-faceted oncology queries that require comprehensive information synthesis from multiple authoritative sources. 
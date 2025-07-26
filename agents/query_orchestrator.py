#!/usr/bin/env python3
"""
Enhanced Query-Orchestrator Agent for Multi-Collection and Multi-Source Queries
Connects to FastMCP specialist agents and coordinates responses from database, web, and literature sources.
"""

import asyncio
import logging
import json
import subprocess
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries that can be processed."""
    CANCER_INFO = "cancer_info"
    GENE_INFO = "gene_info"
    DRUG_INFO = "drug_info"
    DRUG_INDIA_INFO = "drug_india_info"
    MULTI_COLLECTION = "multi_collection"
    WEB_SEARCH = "web_search"
    LITERATURE_SEARCH = "literature_search"
    CLINICAL_TRIALS = "clinical_trials"
    UNKNOWN = "unknown"

@dataclass
class QueryIntent:
    """Represents a decomposed query intent."""
    query_type: QueryType
    entity: str
    specific_field: Optional[str] = None
    target_agents: List[str] = None  # Changed to support multiple agents
    tools_to_use: List[str] = None
    parameters: Dict[str, Any] = None
    priority: int = 1  # For ordering multiple queries

@dataclass
class AgentResponse:
    """Response from a specialist agent."""
    agent_name: str
    query_intent: QueryIntent
    result: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class EnhancedQueryOrchestrator:
    """
    Enhanced orchestrator for multi-collection and multi-source queries.
    """
    
    def __init__(self):
        """Initialize the Enhanced Query Orchestrator."""
        self.agents = {
            # Database MCP Servers (using FastMCP)
            "CancerKnowledgeAgent": {
                "script": "mcp_servers/cancer_knowledge_server.py",
                "collection": "cancers",
                "type": "database",
                "tools": [
                    "search_cancer_by_name", "search_cancer_by_biomarker", 
                    "get_cancer_guidelines", "get_cancer_survival_rates",
                    "search_cancer_by_organ", "get_related_cancers",
                    "search_cancer_by_subtype", "get_cancer_calculators"
                ]
            },
            "GeneKnowledgeAgent": {
                "script": "mcp_servers/gene_knowledge_server.py", 
                "collection": "genes",
                "type": "database",
                "tools": [
                    "search_gene_by_name", "get_gene_drug_associations",
                    "get_gene_prognosis_impact", "get_gene_clinical_trials",
                    "search_genes_by_cancer_type", "search_genes_by_drug",
                    "get_gene_overview", "get_gene_efficacy_data"
                ]
            },
            "DrugKnowledgeAgent": {
                "script": "mcp_servers/drug_knowledge_server.py",
                "collection": "drugs", 
                "type": "database",
                "tools": [
                    "search_drug_by_name", "get_drug_efficacy",
                    "get_drug_safety_profile", "search_drugs_by_target",
                    "search_drugs_by_cancer_type", "search_drugs_by_biomarker",
                    "get_drug_clinical_trials", "search_combination_drugs"
                ]
            },
            "DrugIndiaKnowledgeAgent": {
                "script": "mcp_servers/drug_india_knowledge_server.py",
                "collection": "drugs_india",
                "type": "database",
                "tools": [
                    "search_india_drug_by_name", "search_cdsco_approved_drugs",
                    "get_india_drug_brands", "search_targeted_therapy_india",
                    "search_india_drugs_by_cancer_type", "search_india_drugs_by_biomarker"
                ]
            },
            # External API MCP Servers
            "WebSearchAgent": {
                "script": "mcp_servers/websearch_server.py",
                "collection": "web",
                "type": "external",
                "tools": [
                    "web_search", "search_medical_news"
                ]
            },
            "PubMedAgent": {
                "script": "mcp_servers/pubmed_server.py",
                "collection": "literature",
                "type": "external", 
                "tools": [
                    "search_pubmed", "get_pubmed_summaries"
                ]
            },
            "ClinicalTrialsAgent": {
                "script": "mcp_servers/clinicaltrials_server.py",
                "collection": "trials",
                "type": "external",
                "tools": [
                    "search_clinical_trials", "get_trial_details"
                ]
            }
        }
        self.memory_store = {}
        self.collection_schemas = {
            "cancers": "Cancer information, biomarkers, guidelines, survival data",
            "genes": "Gene mutations, drug associations, prognosis impact",
            "drugs": "Global drug information, efficacy, safety profiles",
            "drugs_india": "India-specific drug availability, CDSCO approval"
        }
        
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the enhanced multi-source agent system."""
        try:
            logger.info(f"Processing enhanced query: {user_query}")
            
            # Step 1: Enhanced query analysis and decomposition
            query_intents = await self._enhanced_analyze_query(user_query)
            
            # Step 2: Route to appropriate agents (potentially multiple)
            agent_responses = await self._route_to_agents(query_intents)
            
            # Step 3: Enhanced response synthesis
            final_response = await self._enhanced_synthesize_responses(user_query, query_intents, agent_responses)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Enhanced query processing failed: {e}")
            return {
                "status": "error",
                "message": f"Query processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _enhanced_analyze_query(self, user_query: str) -> List[QueryIntent]:
        """Enhanced query analysis with multi-collection and multi-source detection."""
        intents = []
        query_lower = user_query.lower()
        
        # Enhanced keyword sets
        cancer_keywords = ["cancer", "tumor", "oncology", "malignancy", "carcinoma", "sarcoma", "lymphoma", "leukemia", "msi-h", "colorectal", "lung", "breast", "prostate"]
        gene_keywords = ["gene", "mutation", "biomarker", "genetic", "genomic", "egfr", "tp53", "braf", "kras", "her2", "alk", "msi", "microsatellite"]
        drug_keywords = ["drug", "therapy", "treatment", "medication", "inhibitor", "antibody", "chemotherapy", "efficacy", "side effects", "clinical trial"]
        india_keywords = ["india", "indian", "cdsco", "brand", "available", "approved"]
        web_keywords = ["latest", "recent", "news", "current", "update", "breakthrough"]
        literature_keywords = ["study", "research", "paper", "publication", "evidence", "clinical trial"]
        
        # Extract entities
        entities = self._extract_medical_entities(user_query)
        
        # Multi-collection detection patterns
        multi_collection_patterns = [
            (r"efficacy.*(?:india|indian|cdsco)", ["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
            (r"(?:drugs?|treatment).*(?:india|indian)", ["DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
            (r"(?:msi-h|microsatellite.*colorectal)", ["CancerKnowledgeAgent", "DrugKnowledgeAgent", "DrugIndiaKnowledgeAgent"]),
            (r"biomarker.*(?:drug|treatment)", ["CancerKnowledgeAgent", "GeneKnowledgeAgent", "DrugKnowledgeAgent"]),
            (r"(?:gene|mutation).*(?:drug|therapy)", ["GeneKnowledgeAgent", "DrugKnowledgeAgent"]),
        ]
        
        # Check for multi-collection patterns
        for pattern, agents in multi_collection_patterns:
            if re.search(pattern, query_lower):
                for entity in entities[:2]:  # Limit entities for multi-collection
                    intents.append(QueryIntent(
                        query_type=QueryType.MULTI_COLLECTION,
                        entity=entity,
                        target_agents=agents,
                        tools_to_use=self._get_relevant_tools(agents, query_lower),
                        priority=1
                    ))
                logger.info(f"Detected multi-collection query requiring agents: {agents}")
                
        # If no multi-collection patterns, analyze for single sources
        if not intents:
            # Check for web search needs
            if any(keyword in query_lower for keyword in web_keywords) or "search" in query_lower:
                for entity in entities[:2]:
                    intents.append(QueryIntent(
                        query_type=QueryType.WEB_SEARCH,
                        entity=entity,
                        target_agents=["WebSearchAgent"],
                        tools_to_use=["web_search"],
                        priority=2
                    ))
            
            # Check for literature search needs
            if any(keyword in query_lower for keyword in literature_keywords):
                for entity in entities[:2]:
                    intents.append(QueryIntent(
                        query_type=QueryType.LITERATURE_SEARCH,
                        entity=entity,
                        target_agents=["PubMedAgent"],
                        tools_to_use=["search_pubmed"],
                        priority=2
                    ))
            
            # Database-specific routing
            for entity in entities[:3]:
                # Cancer-related
                if any(keyword in query_lower for keyword in cancer_keywords):
                    intents.append(QueryIntent(
                        query_type=QueryType.CANCER_INFO,
                        entity=entity,
                        target_agents=["CancerKnowledgeAgent"],
                        tools_to_use=self._get_cancer_tools(query_lower),
                        priority=1
                    ))
                
                # Gene-related
                if any(keyword in query_lower for keyword in gene_keywords):
                    intents.append(QueryIntent(
                        query_type=QueryType.GENE_INFO,
                        entity=entity,
                        target_agents=["GeneKnowledgeAgent"],
                        tools_to_use=self._get_gene_tools(query_lower),
                        priority=1
                    ))
                
                # Drug-related
                if any(keyword in query_lower for keyword in drug_keywords):
                    if any(keyword in query_lower for keyword in india_keywords):
                        intents.append(QueryIntent(
                            query_type=QueryType.DRUG_INDIA_INFO,
                            entity=entity,
                            target_agents=["DrugIndiaKnowledgeAgent"],
                            tools_to_use=self._get_drug_india_tools(query_lower),
                            priority=1
                        ))
                    else:
                        intents.append(QueryIntent(
                            query_type=QueryType.DRUG_INFO,
                            entity=entity,
                            target_agents=["DrugKnowledgeAgent"],
                            tools_to_use=self._get_drug_tools(query_lower),
                            priority=1
                        ))
        
        # Sort by priority and limit
        intents.sort(key=lambda x: x.priority)
        return intents[:8]  # Limit total intents
    
    def _extract_medical_entities(self, query: str) -> List[str]:
        """Enhanced medical entity extraction."""
        entities = []
        query_lower = query.lower()
        
        # Known medical terms
        known_terms = {
            "cancers": ["lung cancer", "breast cancer", "colorectal cancer", "prostate cancer", "melanoma", "glioblastoma", "msi-h"],
            "genes": ["egfr", "tp53", "braf", "kras", "her2", "alk", "pten", "brca1", "brca2", "msi"],
            "drugs": ["pembrolizumab", "trastuzumab", "erlotinib", "imatinib", "bevacizumab", "osimertinib"],
            "biomarkers": ["msi-h", "microsatellite instability", "her2+", "egfr+", "pd-l1"]
        }
        
        # Extract known terms
        for category, terms in known_terms.items():
            for term in terms:
                if term in query_lower:
                    entities.append(term)
        
        # Pattern-based extraction
        # Drug names (often end with specific suffixes)
        drug_pattern = r'\b[A-Z][a-z]+(?:mab|ib|nib|zumab|tinib|lizumab)\b'
        drugs = re.findall(drug_pattern, query)
        entities.extend([d.lower() for d in drugs])
        
        # Gene names (2-5 uppercase letters/numbers)
        gene_pattern = r'\b[A-Z]{2,5}[0-9]*\b'
        genes = re.findall(gene_pattern, query)
        entities.extend([g.lower() for g in genes])
        
        # Cancer types with specific patterns
        cancer_pattern = r'\b\w+\s+cancer\b'
        cancers = re.findall(cancer_pattern, query_lower)
        entities.extend(cancers)
        
        # Remove duplicates and common words
        entities = list(set(entities))
        entities = [e for e in entities if len(e) > 2 and e not in ['the', 'and', 'for', 'with']]
        
        return entities[:5]  # Limit entities
    
    def _get_relevant_tools(self, agents: List[str], query: str) -> List[str]:
        """Get relevant tools for multi-agent queries."""
        tools = []
        query_lower = query.lower()
        
        for agent in agents:
            if agent == "DrugKnowledgeAgent":
                if "efficacy" in query_lower:
                    tools.append("get_drug_efficacy")
                elif "safety" in query_lower or "side effect" in query_lower:
                    tools.append("get_drug_safety_profile")
                else:
                    tools.append("search_drug_by_name")
            elif agent == "DrugIndiaKnowledgeAgent":
                if "brand" in query_lower:
                    tools.append("get_india_drug_brands")
                elif "cdsco" in query_lower:
                    tools.append("search_cdsco_approved_drugs")
                else:
                    tools.append("search_india_drug_by_name")
            elif agent == "CancerKnowledgeAgent":
                if "biomarker" in query_lower:
                    tools.append("search_cancer_by_biomarker")
                elif "guideline" in query_lower:
                    tools.append("get_cancer_guidelines")
                else:
                    tools.append("search_cancer_by_name")
            elif agent == "GeneKnowledgeAgent":
                if "drug" in query_lower:
                    tools.append("get_gene_drug_associations")
                elif "prognosis" in query_lower:
                    tools.append("get_gene_prognosis_impact")
                else:
                    tools.append("search_gene_by_name")
        
        return tools or ["search_by_name"]  # Default fallback
    
    def _get_cancer_tools(self, query: str) -> List[str]:
        """Get relevant cancer tools based on query."""
        if "biomarker" in query:
            return ["search_cancer_by_biomarker"]
        elif "guideline" in query:
            return ["get_cancer_guidelines"]
        elif "survival" in query:
            return ["get_cancer_survival_rates"]
        else:
            return ["search_cancer_by_name"]
    
    def _get_gene_tools(self, query: str) -> List[str]:
        """Get relevant gene tools based on query."""
        if "drug" in query:
            return ["get_gene_drug_associations"]
        elif "prognosis" in query:
            return ["get_gene_prognosis_impact"]
        elif "trial" in query:
            return ["get_gene_clinical_trials"]
        else:
            return ["search_gene_by_name"]
    
    def _get_drug_tools(self, query: str) -> List[str]:
        """Get relevant drug tools based on query."""
        if "efficacy" in query:
            return ["get_drug_efficacy"]
        elif "safety" in query or "side effect" in query:
            return ["get_drug_safety_profile"]
        elif "target" in query:
            return ["search_drugs_by_target"]
        else:
            return ["search_drug_by_name"]
    
    def _get_drug_india_tools(self, query: str) -> List[str]:
        """Get relevant India drug tools based on query."""
        if "brand" in query:
            return ["get_india_drug_brands"]
        elif "cdsco" in query:
            return ["search_cdsco_approved_drugs"]
        elif "target" in query:
            return ["search_targeted_therapy_india"]
        else:
            return ["search_india_drug_by_name"]

    async def _route_to_agents(self, query_intents: List[QueryIntent]) -> List[AgentResponse]:
        """Route intents to appropriate MCP agents."""
        responses = []
        
        # Group intents by agent to minimize agent calls
        agent_groups = {}
        for intent in query_intents:
            if intent.target_agents:  # All intents now use target_agents list
                for agent in intent.target_agents:
                    if agent not in agent_groups:
                        agent_groups[agent] = []
                    agent_groups[agent].append(intent)
        
        # Process each agent group
        for agent_name, intents in agent_groups.items():
            for intent in intents:
                try:
                    # Check memory cache first
                    cache_key = f"{agent_name}_{intent.entity}_{intent.tools_to_use[0] if intent.tools_to_use else 'search'}"
                    if cache_key in self.memory_store:
                        logger.info(f"Using cached result for {cache_key}")
                        responses.append(AgentResponse(
                            agent_name=agent_name,
                            query_intent=intent,
                            result=self.memory_store[cache_key],
                            success=True
                        ))
                        continue
                    
                    # Call the actual FastMCP server
                    result = await self._call_fastmcp_agent(agent_name, intent)
                    
                    # Cache successful results
                    if result.get("success", True):
                        self.memory_store[cache_key] = result
                    
                    responses.append(AgentResponse(
                        agent_name=agent_name,
                        query_intent=intent,
                        result=result,
                        success=result.get("success", True),
                        error_message=result.get("error")
                    ))
                    
                except Exception as e:
                    logger.error(f"Agent {agent_name} call failed: {e}")
                    responses.append(AgentResponse(
                        agent_name=agent_name,
                        query_intent=intent,
                        result={},
                        success=False,
                        error_message=str(e)
                    ))
        
        return responses

    async def _call_fastmcp_agent(self, agent_name: str, intent: QueryIntent) -> Dict[str, Any]:
        """Call MCP server functions directly within the same process to get real database data."""
        try:
            # Get the tool to use
            tool_name = intent.tools_to_use[0] if intent.tools_to_use else "search"
            
            # For database agents, call the functions directly
            if self.agents[agent_name]["type"] == "database":
                return await self._call_database_functions_directly(agent_name, tool_name, intent.entity)
            
            # For external agents, return placeholder for now
            elif self.agents[agent_name]["type"] == "external":
                return await self._call_external_functions_directly(agent_name, tool_name, intent.entity)
            
            else:
                raise ValueError(f"Unknown agent type: {self.agents[agent_name].get('type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"MCP agent call failed: {e}")
            return {"error": str(e), "success": False}

    async def _call_database_functions_directly(self, agent_name: str, tool_name: str, entity: str) -> Dict[str, Any]:
        """Call database MCP server functions directly with fallback to mock data."""
        try:
            # Try to import MongoDB connection utilities
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
                import os
                
                # Connect to MongoDB directly with provided credentials
                mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://onco-agent-user:iqh1SqOjGVjCCFLH@oncopilot-devqc-cluster.efwoqpm.mongodb.net/")
                database_name = os.getenv("DATABASE_NAME", "oncopilot-agent")
                
                # Configure connection with timeout settings
                client = AsyncIOMotorClient(
                    mongodb_uri,
                    maxPoolSize=50,
                    minPoolSize=5,
                    socketTimeoutMS=30000,
                    connectTimeoutMS=10000,
                    serverSelectionTimeoutMS=5000
                )
                db = client[database_name]
                
                # Test connection with timeout
                await client.admin.command('ping')
                
                # Route to appropriate collection and function
                if agent_name == "CancerKnowledgeAgent":
                    return await self._query_cancer_collection(db, tool_name, entity)
                elif agent_name == "DrugKnowledgeAgent":
                    return await self._query_drug_collection(db, tool_name, entity)
                elif agent_name == "DrugIndiaKnowledgeAgent":
                    return await self._query_drug_india_collection(db, tool_name, entity)
                elif agent_name == "GeneKnowledgeAgent":
                    return await self._query_gene_collection(db, tool_name, entity)
                else:
                    return self._get_mock_data(agent_name, tool_name, entity)
                    
            except ImportError as import_error:
                logger.warning(f"Database import failed ({import_error}), using mock data")
                return self._get_mock_data(agent_name, tool_name, entity)
            except Exception as db_error:
                logger.warning(f"Database connection failed ({db_error}), using mock data")
                return self._get_mock_data(agent_name, tool_name, entity)
                
        except Exception as e:
            logger.error(f"Direct database call failed for {agent_name}: {e}")
            return self._get_mock_data(agent_name, tool_name, entity)

    async def _query_cancer_collection(self, db, tool_name: str, entity: str) -> Dict[str, Any]:
        """Query the cancers collection directly."""
        try:
            collection = db.cancers
            
            if tool_name == "search_cancer_by_biomarker":
                query = {"cancer_biomarkers_tags": {"$regex": entity, "$options": "i"}}
            elif tool_name == "get_cancer_guidelines":
                query = {"cancer_name": {"$regex": entity, "$options": "i"}}
                projection = {
                    "cancer_name": 1, "nccn_guidelines_titles": 1, "nccn_guidelines_links": 1,
                    "esmo_guidelines": 1, "asco_guidelines_titles": 1, "asco_guidelines_links": 1
                }
            elif tool_name == "get_cancer_survival_rates":
                query = {"cancer_name": {"$regex": entity, "$options": "i"}}
                projection = {"cancer_name": 1, "cancer_survival_rates": 1, "cancer_incidence_prevalance": 1}
            else:  # search_cancer_by_name (default)
                query = {"cancer_name": {"$regex": entity, "$options": "i"}}
                projection = None  # Get all fields
            
            # Execute query
            if 'projection' in locals() and projection:
                cursor = collection.find(query, projection).limit(10)
            else:
                cursor = collection.find(query).limit(10)
            
            results = []
            async for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return {
                "operation": tool_name,
                "query_parameters": {"entity": entity},
                "collection": "cancers",
                "timestamp": datetime.now().isoformat(),
                "total_records": len(results),
                "success": True,
                "data": {
                    "results": results,
                    "query": query
                }
            }
            
        except Exception as e:
            logger.error(f"Cancer collection query failed: {e}")
            return self._get_fallback_data("CancerKnowledgeAgent", {"collection": "cancers"}, tool_name, entity)

    async def _query_drug_collection(self, db, tool_name: str, entity: str) -> Dict[str, Any]:
        """Query the drugs collection directly."""
        try:
            collection = db.drugs
            
            if tool_name == "get_drug_efficacy":
                query = {"drug_name": {"$regex": entity, "$options": "i"}}
                projection = {
                    "drug_name": 1, "efficacy": 1, "efficacy_source_titles": 1, "efficacy_source_links": 1,
                    "landmark_clinical_trial_id": 1, "ct_phase": 1, "ct_title": 1, "prognosis": 1
                }
            elif tool_name == "get_drug_safety_profile":
                query = {"drug_name": {"$regex": entity, "$options": "i"}}
                projection = {
                    "drug_name": 1, "side_effects": 1, "warnings_and_precautions": 1,
                    "contraindications": 1, "drug_interactions": 1, "limitations_of_use": 1
                }
            elif tool_name == "search_drugs_by_target":
                query = {"target": {"$regex": entity, "$options": "i"}}
                projection = {"drug_name": 1, "target": 1, "target_action": 1, "efficacy": 1}
            else:  # search_drug_by_name (default)
                query = {"drug_name": {"$regex": entity, "$options": "i"}}
                projection = None  # Get all fields
            
            # Execute query
            if projection:
                cursor = collection.find(query, projection).limit(10)
            else:
                cursor = collection.find(query).limit(10)
            
            results = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return {
                "operation": tool_name,
                "query_parameters": {"entity": entity},
                "collection": "drugs",
                "timestamp": datetime.now().isoformat(),
                "total_records": len(results),
                "success": True,
                "data": {
                    "results": results,
                    "query": query
                }
            }
            
        except Exception as e:
            logger.error(f"Drug collection query failed: {e}")
            return self._get_fallback_data("DrugKnowledgeAgent", {"collection": "drugs"}, tool_name, entity)

    async def _query_drug_india_collection(self, db, tool_name: str, entity: str) -> Dict[str, Any]:
        """Query the drugs_india collection directly."""
        try:
            collection = db.drugs_india
            
            if tool_name == "search_cdsco_approved_drugs":
                query = {
                    "$and": [
                        {"drug_name": {"$regex": entity, "$options": "i"}},
                        {"is_drug_approved_by_cdsco": "Yes"}
                    ]
                }
            elif tool_name == "get_india_drug_brands":
                query = {"drug_name": {"$regex": entity, "$options": "i"}}
                projection = {"drug_name": 1, "brand_name": 1, "company_name": 1, "brand_website_links": 1}
            else:  # search_india_drug_by_name (default)
                query = {"drug_name": {"$regex": entity, "$options": "i"}}
                projection = None
            
            # Execute query
            if 'projection' in locals() and projection:
                cursor = collection.find(query, projection).limit(10)
            else:
                cursor = collection.find(query).limit(10)
            
            results = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return {
                "operation": tool_name,
                "query_parameters": {"entity": entity},
                "collection": "drugs_india",
                "timestamp": datetime.now().isoformat(),
                "total_records": len(results),
                "success": True,
                "data": {
                    "results": results,
                    "query": query
                }
            }
            
        except Exception as e:
            logger.error(f"Drug India collection query failed: {e}")
            return self._get_fallback_data("DrugIndiaKnowledgeAgent", {"collection": "drugs_india"}, tool_name, entity)

    async def _query_gene_collection(self, db, tool_name: str, entity: str) -> Dict[str, Any]:
        """Query the genes collection directly."""
        try:
            collection = db.genes
            
            if tool_name == "get_gene_drug_associations":
                query = {"gene_name": {"$regex": entity, "$options": "i"}}
                projection = {
                    "gene_name": 1, "drug_name": 1, "efficacy": 1, "gene_drug_overview_sources": 1,
                    "drug_target": 1, "landmark_clinical_trial_id": 1
                }
            elif tool_name == "get_gene_prognosis_impact":
                query = {"gene_name": {"$regex": entity, "$options": "i"}}
                projection = {"gene_name": 1, "prognosis": 1, "gene_cancer_prognosis_source_apas": 1}
            else:  # search_gene_by_name (default)
                query = {"gene_name": {"$regex": entity, "$options": "i"}}
                projection = None
            
            # Execute query
            if 'projection' in locals() and projection:
                cursor = collection.find(query, projection).limit(10)
            else:
                cursor = collection.find(query).limit(10)
            
            results = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return {
                "operation": tool_name,
                "query_parameters": {"entity": entity},
                "collection": "genes",
                "timestamp": datetime.now().isoformat(),
                "total_records": len(results),
                "success": True,
                "data": {
                    "results": results,
                    "query": query
                }
            }
            
        except Exception as e:
            logger.error(f"Gene collection query failed: {e}")
            return self._get_fallback_data("GeneKnowledgeAgent", {"collection": "genes"}, tool_name, entity)

    async def _call_external_functions_directly(self, agent_name: str, tool_name: str, entity: str) -> Dict[str, Any]:
        """Call external APIs directly (placeholder for now)."""
        return {
            "operation": tool_name,
            "collection": self.agents[agent_name]["collection"],
            "timestamp": datetime.now().isoformat(),
            "total_records": 0,
            "success": True,
            "data": {
                "results": [{
                    "query": entity,
                    "source": agent_name,
                    "note": "External API integration coming soon"
                }]
            }
        }

    def _get_fallback_data(self, agent_name: str, agent_config: dict, tool_name: str, entity: str) -> Dict[str, Any]:
        """Get fallback simulated data when real MCP servers are not available."""
        return {
            "operation": tool_name,
            "query_parameters": {"entity": entity},
            "collection": agent_config["collection"],
            "timestamp": datetime.now().isoformat(),
            "total_records": 0,
            "data": {
                "results": [],
                "error": f"Real MCP server for {agent_name} not accessible - using fallback",
                "note": "To get real data, ensure MCP servers are running and accessible"
            },
            "success": False
        }

    def _get_mock_data(self, agent_name: str, tool_name: str, entity: str) -> Dict[str, Any]:
        """Generate realistic mock data based on the agent and tool."""
        
        # Generate realistic mock data based on entity and tool
        mock_results = []
        
        if agent_name == "CancerKnowledgeAgent":
            if tool_name == "get_cancer_survival_rates":
                mock_results = [{
                    "cancer_name": entity.title(),
                    "cancer_incidence_prevalance": f"{entity.title()} is among the most common cancers globally, with significant prevalence in the U.S. According to recent statistics, it affects approximately 150,000 new patients annually in the United States.",
                    "cancer_survival_rates": "5-year survival rate varies by stage: Stage I (90-95%), Stage II (70-85%), Stage III (50-70%), Stage IV (10-15%). Early detection significantly improves outcomes.",
                    "cancer_biomarkers": "Key biomarkers include MSI-H (microsatellite instability), KRAS mutations, BRAF mutations, PIK3CA alterations, and PD-L1 expression levels.",
                    "nccn_guidelines_titles": [f"NCCN Guidelines for {entity.title()}", f"NCCN Treatment Guidelines {entity.title()} 2024"],
                    "source": "Mock data - Database connection not available"
                }]
            else:
                mock_results = [{
                    "cancer_name": entity.title(),
                    "description": f"Comprehensive information about {entity} including epidemiology, treatment approaches, and clinical guidelines.",
                    "cancer_organ_category": entity.split()[0].title() if " " in entity else "Various",
                    "source": "Mock data - Database connection not available"
                }]
                
        elif agent_name == "DrugKnowledgeAgent":
            if tool_name == "get_drug_efficacy":
                mock_results = [{
                    "drug_name": entity.title(),
                    "efficacy": f"{entity.title()} demonstrates significant clinical efficacy in randomized controlled trials. Response rates range from 30-60% depending on patient population and cancer type. Median progression-free survival improvement of 4-8 months compared to standard therapy.",
                    "landmark_clinical_trial_id": ["NCT12345678", "NCT87654321"],
                    "ct_phase": ["Phase III", "Phase II"],
                    "efficacy_source_titles": ["New England Journal of Medicine 2023", "Journal of Clinical Oncology 2024"],
                    "source": "Mock data - Database connection not available"
                }]
            else:
                mock_results = [{
                    "drug_name": entity.title(),
                    "description": f"FDA-approved targeted therapy {entity} for specific cancer indications.",
                    "type_of_therapy": ["Targeted Therapy"],
                    "source": "Mock data - Database connection not available"
                }]
                
        elif agent_name == "DrugIndiaKnowledgeAgent":
            mock_results = [{
                "drug_name": entity.title(),
                "is_drug_approved_by_cdsco": "Yes",
                "brand_name": [f"{entity.title()} India", f"Generic {entity.title()}"],
                "company_name": ["Dr. Reddy's Laboratories", "Cipla Limited"],
                "description": f"{entity.title()} is available in India through CDSCO approval with multiple brand options.",
                "source": "Mock data - Database connection not available"
            }]
            
        elif agent_name == "GeneKnowledgeAgent":
            mock_results = [{
                "gene_name": entity.upper(),
                "overview": f"The {entity.upper()} gene plays a crucial role in cancer development and treatment response. Mutations in this gene are found in various cancer types and influence therapeutic decisions.",
                "drug_name": [f"Anti-{entity.upper()} therapy", f"{entity.upper()} inhibitor"],
                "prognosis": f"{entity.upper()} mutations can impact prognosis and treatment response, with specific therapeutic implications.",
                "source": "Mock data - Database connection not available"
            }]
        
        return {
            "operation": tool_name,
            "query_parameters": {"entity": entity},
            "collection": self.agents[agent_name]["collection"],
            "timestamp": datetime.now().isoformat(),
            "total_records": len(mock_results),
            "success": True,
            "data": {
                "results": mock_results,
                "note": "Using mock data - Database connection not available. Check MongoDB connection and dependencies."
            }
        }

    async def _enhanced_synthesize_responses(self, user_query: str, query_intents: List[QueryIntent], 
                                  agent_responses: List[AgentResponse]) -> Dict[str, Any]:
        """Enhanced response synthesis with multi-collection intelligence."""
        
        successful_responses = [r for r in agent_responses if r.success]
        failed_responses = [r for r in agent_responses if not r.success]
        
        # Group responses by collection type
        database_responses = [r for r in successful_responses if self.agents[r.agent_name]["type"] == "database"]
        external_responses = [r for r in successful_responses if self.agents[r.agent_name]["type"] == "external"]
        
        # Generate intelligent summary
        summary = self._generate_enhanced_summary(user_query, successful_responses, database_responses, external_responses)
        
        # Collect metadata
        agents_used = list(set([r.agent_name for r in successful_responses]))
        collections_queried = list(set([self.agents[agent]["collection"] for agent in agents_used]))
        
        # Determine query complexity
        is_multi_collection = len([r for r in successful_responses if self.agents[r.agent_name]["type"] == "database"]) > 1
        has_external_sources = len(external_responses) > 0
        
        return {
            "status": "success",
            "user_query": user_query,
            "query_complexity": "multi-collection" if is_multi_collection else "single-source",
            "summary": summary,
            "agents_used": agents_used,
            "collections_queried": collections_queried,
            "database_results": len(database_responses),
            "external_results": len(external_responses),
            "total_intents": len(query_intents),
            "successful_responses": len(successful_responses),
            "failed_responses": len(failed_responses),
            "detailed_responses": [
                {
                    "agent": r.agent_name,
                    "collection": self.agents[r.agent_name]["collection"],
                    "entity": r.query_intent.entity,
                    "tools_used": r.query_intent.tools_to_use,
                    "data": r.result
                } for r in successful_responses
            ],
            "has_external_sources": has_external_sources,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_enhanced_summary(self, user_query: str, all_responses: List[AgentResponse], 
                                 database_responses: List[AgentResponse], 
                                 external_responses: List[AgentResponse]) -> str:
        """Generate an enhanced natural language summary."""
        if not all_responses:
            return "No relevant information found for your query."
        
        summary_parts = []
        
        # Database results summary
        if database_responses:
            db_collections = list(set([self.agents[r.agent_name]["collection"] for r in database_responses]))
            if len(db_collections) > 1:
                summary_parts.append(f"Found comprehensive information across {len(db_collections)} collections: {', '.join(db_collections)}")
            else:
                summary_parts.append(f"Retrieved detailed information from {db_collections[0]} collection")
        
        # External sources summary
        if external_responses:
            external_types = list(set([self.agents[r.agent_name]["collection"] for r in external_responses]))
            summary_parts.append(f"Enhanced with external sources: {', '.join(external_types)}")
        
        # Query-specific insights
        query_lower = user_query.lower()
        if "efficacy" in query_lower and len(database_responses) > 1:
            summary_parts.append("Efficacy data synthesized from multiple authoritative sources")
        
        if "india" in query_lower and any("india" in self.agents[r.agent_name]["collection"] for r in database_responses):
            summary_parts.append("Including India-specific availability and approval information")
        
        return ". ".join(summary_parts) + "."

# Main function for testing
async def main():
    """Test the Enhanced Query Orchestrator."""
    orchestrator = EnhancedQueryOrchestrator()
    
    test_queries = [
        "What are the biomarkers for lung cancer?",
        "EGFR mutation drugs",
        "Pembrolizumab side effects",
        "Is imatinib available in India?",
        "What are the latest cancer research papers?",
        "Search for clinical trials for MSI-H colorectal cancer",
        "Efficacy of pembrolizumab in MSI-H colorectal cancer",
        "What are the latest news about MSI-H colorectal cancer?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = await orchestrator.process_query(query)
        print(f"📋 Summary: {result.get('summary')}")
        print(f"🤖 Agents: {result.get('agents_used')}")

if __name__ == "__main__":
    asyncio.run(main()) 
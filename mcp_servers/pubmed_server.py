#!/usr/bin/env python3
"""
PubMed Literature Search MCP Server
Provides tools to search PubMed and retrieve publication information for oncology research.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import httpx
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types
from mcp.server.models import InitializationOptions
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NCBI API configuration
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_API_KEY = os.getenv("NCBI_API_KEY")  # Optional API key

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class PubMedKnowledgeServer:
    def __init__(self):
        self.client = None
        self.server = Server("pubmed-literature-agent")
        
    def setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available PubMed literature search tools."""
            return [
                Tool(
                    name="search_pubmed",
                    description="Search PubMed for articles matching a query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string (e.g., 'lung cancer EGFR')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_pubmed_summaries",
                    description="Get summary information for specific PubMed articles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pmids": {
                                "type": "string",
                                "description": "Comma-separated list of PubMed IDs (e.g., '12345678,87654321')"
                            }
                        },
                        "required": ["pmids"]
                    }
                ),
                Tool(
                    name="search_oncology_literature",
                    description="Search PubMed for oncology-specific literature",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cancer_type": {
                                "type": "string",
                                "description": "Type of cancer (e.g., 'lung cancer', 'breast cancer')"
                            },
                            "gene": {
                                "type": "string",
                                "description": "Gene name (optional, e.g., 'EGFR', 'TP53')"
                            },
                            "drug": {
                                "type": "string", 
                                "description": "Drug name (optional, e.g., 'pembrolizumab')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["cancer_type"]
                    }
                ),
                Tool(
                    name="get_related_articles",
                    description="Find articles related to a specific PubMed article",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pmid": {
                                "type": "string",
                                "description": "PubMed ID of the reference article"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of related articles (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["pmid"]
                    }
                ),
                Tool(
                    name="get_pubmed_abstracts",
                    description="Get full abstracts for PubMed articles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pmids": {
                                "type": "string",
                                "description": "Comma-separated list of PubMed IDs"
                            }
                        },
                        "required": ["pmids"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool execution."""
            try:
                result = await self._execute_tool(name, arguments)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, cls=JSONEncoder, indent=2)
                )]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]

    async def _execute_tool(self, name: str, arguments: dict) -> dict:
        """Execute the specified tool with given arguments."""
        
        if name == "search_pubmed":
            return await self._search_pubmed(arguments)
        elif name == "get_pubmed_summaries":
            return await self._get_pubmed_summaries(arguments)
        elif name == "search_oncology_literature":
            return await self._search_oncology_literature(arguments)
        elif name == "get_related_articles":
            return await self._get_related_articles(arguments)
        elif name == "get_pubmed_abstracts":
            return await self._get_pubmed_abstracts(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _search_pubmed(self, arguments: dict) -> dict:
        """Search PubMed for articles matching the query."""
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)
        
        try:
            search_url = f"{NCBI_BASE_URL}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max_results
            }
            
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                search_result = data.get("esearchresult", {})
                pmids = search_result.get("idlist", [])
                count = search_result.get("count", "0")
                
                return {
                    "query": query,
                    "total_count": int(count),
                    "returned_count": len(pmids),
                    "pmids": pmids,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _search_pubmed: {e}")
            return {"error": str(e)}

    async def _get_pubmed_summaries(self, arguments: dict) -> dict:
        """Get summary information for PubMed articles."""
        pmids = arguments["pmids"]
        
        try:
            summary_url = f"{NCBI_BASE_URL}/esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": pmids,
                "retmode": "json"
            }
            
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(summary_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                result = data.get("result", {})
                
                # Extract article summaries
                articles = []
                for pmid in pmids.split(","):
                    pmid = pmid.strip()
                    if pmid in result:
                        article_data = result[pmid]
                        article = {
                            "pmid": pmid,
                            "title": article_data.get("title", ""),
                            "authors": [author.get("name", "") for author in article_data.get("authors", [])],
                            "source": article_data.get("source", ""),
                            "pubdate": article_data.get("pubdate", ""),
                            "doi": article_data.get("elocationid", "")
                        }
                        articles.append(article)
                
                return {
                    "pmids": pmids,
                    "articles": articles,
                    "count": len(articles),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _get_pubmed_summaries: {e}")
            return {"error": str(e)}

    async def _search_oncology_literature(self, arguments: dict) -> dict:
        """Search PubMed for oncology-specific articles."""
        cancer_type = arguments["cancer_type"]
        gene = arguments.get("gene")
        drug = arguments.get("drug")
        max_results = arguments.get("max_results", 10)
        
        try:
            # Build oncology-specific query
            query_parts = [cancer_type]
            
            if gene:
                query_parts.append(gene)
            if drug:
                query_parts.append(drug)
            
            # Add oncology-specific terms
            query_parts.append("(oncology OR cancer OR tumor OR neoplasm)")
            
            query = " AND ".join(query_parts)
            
            # Search for PMIDs
            search_result = await self._search_pubmed({"query": query, "max_results": max_results})
            
            if "error" in search_result:
                return search_result
            
            pmids = search_result.get("pmids", [])
            
            if not pmids:
                return {
                    "query": query,
                    "cancer_type": cancer_type,
                    "gene": gene,
                    "drug": drug,
                    "message": "No articles found for this query",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get summaries for the PMIDs
            summaries_result = await self._get_pubmed_summaries({"pmids": ",".join(pmids)})
            
            return {
                "query": query,
                "cancer_type": cancer_type,
                "gene": gene,
                "drug": drug,
                "total_count": search_result.get("total_count", 0),
                "returned_count": len(summaries_result.get("articles", [])),
                "articles": summaries_result.get("articles", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _search_oncology_literature: {e}")
            return {"error": str(e)}

    async def _get_related_articles(self, arguments: dict) -> dict:
        """Get articles related to a specific PubMed ID."""
        pmid = arguments["pmid"]
        max_results = arguments.get("max_results", 5)
        
        try:
            link_url = f"{NCBI_BASE_URL}/elink.fcgi"
            params = {
                "dbfrom": "pubmed",
                "db": "pubmed",
                "id": pmid,
                "retmode": "json",
                "linkname": "pubmed_pubmed"
            }
            
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(link_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                linksets = data.get("linksets", [])
                
                if not linksets:
                    return {
                        "reference_pmid": pmid,
                        "message": "No related articles found",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Get related PMIDs
                related_pmids = []
                for linkset in linksets:
                    linksetdbs = linkset.get("linksetdbs", [])
                    for linksetdb in linksetdbs:
                        links = linksetdb.get("links", [])
                        related_pmids.extend(links[:max_results])
                
                # Limit to max_results
                related_pmids = related_pmids[:max_results]
                
                if not related_pmids:
                    return {
                        "reference_pmid": pmid,
                        "message": "No related articles found",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Get summaries for related articles
                summaries_result = await self._get_pubmed_summaries({"pmids": ",".join(related_pmids)})
                
                return {
                    "reference_pmid": pmid,
                    "related_articles": summaries_result.get("articles", []),
                    "count": len(summaries_result.get("articles", [])),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _get_related_articles: {e}")
            return {"error": str(e)}

    async def _get_pubmed_abstracts(self, arguments: dict) -> dict:
        """Get full abstracts for PubMed articles."""
        pmids = arguments["pmids"]
        
        try:
            fetch_url = f"{NCBI_BASE_URL}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": pmids,
                "retmode": "xml",
                "rettype": "abstract"
            }
            
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(fetch_url, params=params)
                response.raise_for_status()
                
                return {
                    "pmids": pmids,
                    "abstracts_xml": response.text,
                    "format": "XML",
                    "note": "Parse XML for structured abstract data",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _get_pubmed_abstracts: {e}")
            return {"error": str(e)}

async def main():
    """Main entry point for the PubMed Literature MCP server."""
    pubmed_server = PubMedKnowledgeServer()
    pubmed_server.setup_handlers()
    
    # Initialize server
    options = InitializationOptions(
        server_name="pubmed-literature-agent",
        server_version="1.0.0",
        capabilities=pubmed_server.server.get_capabilities()
    )
    
    async with pubmed_server.server.run_server() as server:
        logger.info("PubMed Literature Agent MCP Server started")
        try:
            await server.run()
        except KeyboardInterrupt:
            logger.info("PubMed Literature Agent MCP Server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 
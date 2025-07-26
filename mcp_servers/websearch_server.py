#!/usr/bin/env python3
"""
Web Search MCP Server for General Information Retrieval
Provides tools to search the web for oncology-related information.
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

# Search API configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # Optional SerpAPI key

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class WebSearchKnowledgeServer:
    def __init__(self):
        self.server = Server("websearch-general-agent")
        
    def setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available web search tools."""
            return [
                Tool(
                    name="web_search",
                    description="Search the web for general information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_medical_news",
                    description="Search for medical and oncology news",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Medical news search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_drug_information",
                    description="Search for drug information online",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "drug_name": {
                                "type": "string",
                                "description": "Name of the drug to search for"
                            }
                        },
                        "required": ["drug_name"]
                    }
                ),
                Tool(
                    name="search_treatment_guidelines",
                    description="Search for cancer treatment guidelines",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cancer_type": {
                                "type": "string",
                                "description": "Type of cancer"
                            },
                            "organization": {
                                "type": "string",
                                "description": "Guideline organization (optional, e.g., 'NCCN', 'ASCO')"
                            }
                        },
                        "required": ["cancer_type"]
                    }
                ),
                Tool(
                    name="search_biomarker_info",
                    description="Search for biomarker information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "biomarker": {
                                "type": "string",
                                "description": "Biomarker name (e.g., 'EGFR', 'HER2')"
                            },
                            "cancer_type": {
                                "type": "string",
                                "description": "Associated cancer type (optional)"
                            }
                        },
                        "required": ["biomarker"]
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
        
        if name == "web_search":
            return await self._web_search(arguments)
        elif name == "search_medical_news":
            return await self._search_medical_news(arguments)
        elif name == "search_drug_information":
            return await self._search_drug_information(arguments)
        elif name == "search_treatment_guidelines":
            return await self._search_treatment_guidelines(arguments)
        elif name == "search_biomarker_info":
            return await self._search_biomarker_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _web_search(self, arguments: dict) -> dict:
        """Search the web for general information."""
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)
        
        try:
            if SERPAPI_KEY:
                # Use SerpAPI if available
                return await self._serpapi_search(query, max_results)
            else:
                # Fallback to mock search results
                return {
                    "query": query,
                    "max_results": max_results,
                    "results": [
                        {
                            "title": f"Mock result for: {query}",
                            "url": "https://example.com",
                            "description": "Mock search result - SerpAPI key not configured"
                        }
                    ],
                    "total_results": 1,
                    "note": "SerpAPI key not configured - showing mock results",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _web_search: {e}")
            return {"error": str(e)}

    async def _serpapi_search(self, query: str, max_results: int) -> dict:
        """Perform search using SerpAPI."""
        try:
            search_url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": SERPAPI_KEY,
                "engine": "google",
                "num": max_results
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                organic_results = data.get("organic_results", [])
                
                results = []
                for result in organic_results[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "description": result.get("snippet", "")
                    })
                
                return {
                    "query": query,
                    "max_results": max_results,
                    "results": results,
                    "total_results": len(results),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _serpapi_search: {e}")
            return {"error": str(e)}

    async def _search_medical_news(self, arguments: dict) -> dict:
        """Search for medical and oncology news."""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        
        # Add medical context to the query
        medical_query = f"{query} medical news oncology cancer"
        
        return await self._web_search({"query": medical_query, "max_results": max_results})

    async def _search_drug_information(self, arguments: dict) -> dict:
        """Search for drug information online."""
        drug_name = arguments["drug_name"]
        
        # Build drug-specific query
        drug_query = f"{drug_name} drug information mechanism action side effects"
        
        return await self._web_search({"query": drug_query, "max_results": 10})

    async def _search_treatment_guidelines(self, arguments: dict) -> dict:
        """Search for cancer treatment guidelines."""
        cancer_type = arguments["cancer_type"]
        organization = arguments.get("organization")
        
        # Build guidelines query
        if organization:
            guidelines_query = f"{cancer_type} treatment guidelines {organization}"
        else:
            guidelines_query = f"{cancer_type} treatment guidelines NCCN ASCO ESMO"
        
        return await self._web_search({"query": guidelines_query, "max_results": 10})

    async def _search_biomarker_info(self, arguments: dict) -> dict:
        """Search for biomarker information."""
        biomarker = arguments["biomarker"]
        cancer_type = arguments.get("cancer_type")
        
        # Build biomarker query
        if cancer_type:
            biomarker_query = f"{biomarker} biomarker {cancer_type} testing significance"
        else:
            biomarker_query = f"{biomarker} biomarker cancer testing significance"
        
        return await self._web_search({"query": biomarker_query, "max_results": 10})

async def main():
    """Main entry point for the Web Search MCP server."""
    websearch_server = WebSearchKnowledgeServer()
    websearch_server.setup_handlers()
    
    # Initialize server
    options = InitializationOptions(
        server_name="websearch-general-agent",
        server_version="1.0.0",
        capabilities=websearch_server.server.get_capabilities()
    )
    
    async with websearch_server.server.run_server() as server:
        logger.info("Web Search General Agent MCP Server started")
        try:
            await server.run()
        except KeyboardInterrupt:
            logger.info("Web Search General Agent MCP Server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 
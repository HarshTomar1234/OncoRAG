#!/usr/bin/env python3
"""
ClinicalTrials.gov MCP Server for Clinical Trial Search
Provides tools to search and retrieve clinical trial information for oncology research.
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

# ClinicalTrials.gov API configuration
CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ClinicalTrialsKnowledgeServer:
    def __init__(self):
        self.server = Server("clinicaltrials-search-agent")
        
    def setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available clinical trials search tools."""
            return [
                Tool(
                    name="search_clinical_trials",
                    description="Search ClinicalTrials.gov for trials matching criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "condition": {
                                "type": "string",
                                "description": "Medical condition or disease (e.g., 'lung cancer')"
                            },
                            "intervention": {
                                "type": "string",
                                "description": "Intervention or treatment (optional, e.g., 'pembrolizumab')"
                            },
                            "status": {
                                "type": "string",
                                "description": "Trial status (optional, e.g., 'Recruiting', 'Active')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["condition"]
                    }
                ),
                Tool(
                    name="get_trial_details",
                    description="Get detailed information for a specific clinical trial",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "nct_id": {
                                "type": "string",
                                "description": "NCT ID of the clinical trial (e.g., 'NCT01234567')"
                            }
                        },
                        "required": ["nct_id"]
                    }
                ),
                Tool(
                    name="search_oncology_trials",
                    description="Search for oncology-specific clinical trials",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cancer_type": {
                                "type": "string",
                                "description": "Type of cancer (e.g., 'lung cancer', 'breast cancer')"
                            },
                            "drug": {
                                "type": "string",
                                "description": "Drug name (optional, e.g., 'pembrolizumab')"
                            },
                            "gene": {
                                "type": "string",
                                "description": "Gene target (optional, e.g., 'EGFR')"
                            },
                            "status": {
                                "type": "string",
                                "description": "Trial status (default: 'Recruiting')",
                                "default": "Recruiting"
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
                    name="get_trial_locations",
                    description="Get location information for a clinical trial",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "nct_id": {
                                "type": "string",
                                "description": "NCT ID of the clinical trial"
                            },
                            "country": {
                                "type": "string",
                                "description": "Filter by country (optional)"
                            },
                            "state": {
                                "type": "string",
                                "description": "Filter by state (optional)"
                            }
                        },
                        "required": ["nct_id"]
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
        
        if name == "search_clinical_trials":
            return await self._search_clinical_trials(arguments)
        elif name == "get_trial_details":
            return await self._get_trial_details(arguments)
        elif name == "search_oncology_trials":
            return await self._search_oncology_trials(arguments)
        elif name == "get_trial_locations":
            return await self._get_trial_locations(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _search_clinical_trials(self, arguments: dict) -> dict:
        """Search ClinicalTrials.gov for trials matching criteria."""
        condition = arguments["condition"]
        intervention = arguments.get("intervention")
        status = arguments.get("status")
        max_results = arguments.get("max_results", 10)
        
        try:
            search_url = f"{CLINICALTRIALS_BASE_URL}/studies"
            params = {
                "query.cond": condition,
                "format": "json",
                "pageSize": max_results
            }
            
            if intervention:
                params["query.intr"] = intervention
            if status:
                params["filter.overallStatus"] = status
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                studies = data.get("studies", [])
                
                # Extract key information from each study
                trials = []
                for study in studies:
                    protocol_section = study.get("protocolSection", {})
                    identification_module = protocol_section.get("identificationModule", {})
                    status_module = protocol_section.get("statusModule", {})
                    design_module = protocol_section.get("designModule", {})
                    
                    trial = {
                        "nct_id": identification_module.get("nctId", ""),
                        "title": identification_module.get("briefTitle", ""),
                        "status": status_module.get("overallStatus", ""),
                        "phase": design_module.get("phases", []),
                        "start_date": status_module.get("startDateStruct", {}).get("date", ""),
                        "completion_date": status_module.get("completionDateStruct", {}).get("date", ""),
                        "enrollment": design_module.get("enrollmentInfo", {}).get("count", 0)
                    }
                    trials.append(trial)
                
                return {
                    "query": {
                        "condition": condition,
                        "intervention": intervention,
                        "status": status
                    },
                    "total_count": data.get("totalCount", 0),
                    "returned_count": len(trials),
                    "trials": trials,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _search_clinical_trials: {e}")
            return {"error": str(e)}

    async def _get_trial_details(self, arguments: dict) -> dict:
        """Get detailed information for a specific clinical trial."""
        nct_id = arguments["nct_id"]
        
        try:
            detail_url = f"{CLINICALTRIALS_BASE_URL}/studies/{nct_id}"
            params = {"format": "json"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(detail_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                studies = data.get("studies", [])
                
                if not studies:
                    return {
                        "nct_id": nct_id,
                        "error": "Trial not found",
                        "timestamp": datetime.now().isoformat()
                    }
                
                study = studies[0]
                protocol_section = study.get("protocolSection", {})
                
                # Extract comprehensive trial details
                identification_module = protocol_section.get("identificationModule", {})
                status_module = protocol_section.get("statusModule", {})
                design_module = protocol_section.get("designModule", {})
                arms_module = protocol_section.get("armsInterventionsModule", {})
                eligibility_module = protocol_section.get("eligibilityModule", {})
                contacts_module = protocol_section.get("contactsLocationsModule", {})
                
                trial_details = {
                    "nct_id": identification_module.get("nctId", ""),
                    "title": identification_module.get("briefTitle", ""),
                    "official_title": identification_module.get("officialTitle", ""),
                    "status": status_module.get("overallStatus", ""),
                    "phase": design_module.get("phases", []),
                    "study_type": design_module.get("studyType", ""),
                    "allocation": design_module.get("designInfo", {}).get("allocation", ""),
                    "intervention_model": design_module.get("designInfo", {}).get("interventionModel", ""),
                    "primary_purpose": design_module.get("designInfo", {}).get("primaryPurpose", ""),
                    "masking": design_module.get("designInfo", {}).get("maskingInfo", {}),
                    "enrollment": design_module.get("enrollmentInfo", {}),
                    "start_date": status_module.get("startDateStruct", {}),
                    "completion_date": status_module.get("completionDateStruct", {}),
                    "interventions": arms_module.get("interventions", []),
                    "arms": arms_module.get("armGroups", []),
                    "eligibility_criteria": eligibility_module.get("eligibilityCriteria", ""),
                    "minimum_age": eligibility_module.get("minimumAge", ""),
                    "maximum_age": eligibility_module.get("maximumAge", ""),
                    "gender": eligibility_module.get("sex", ""),
                    "healthy_volunteers": eligibility_module.get("healthyVolunteers", False),
                    "locations": contacts_module.get("locations", [])
                }
                
                return {
                    "nct_id": nct_id,
                    "trial_details": trial_details,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in _get_trial_details: {e}")
            return {"error": str(e)}

    async def _search_oncology_trials(self, arguments: dict) -> dict:
        """Search for oncology-specific clinical trials."""
        cancer_type = arguments["cancer_type"]
        drug = arguments.get("drug")
        gene = arguments.get("gene")
        status = arguments.get("status", "Recruiting")
        max_results = arguments.get("max_results", 10)
        
        try:
            # Build oncology-specific query
            condition = cancer_type
            intervention = None
            
            if drug and gene:
                intervention = f"{drug} OR {gene}"
            elif drug:
                intervention = drug
            elif gene:
                intervention = gene
            
            # Use the general search with oncology-specific parameters
            search_args = {
                "condition": condition,
                "intervention": intervention,
                "status": status,
                "max_results": max_results
            }
            
            result = await self._search_clinical_trials(search_args)
            
            # Add oncology-specific metadata
            if "error" not in result:
                result["oncology_search"] = {
                    "cancer_type": cancer_type,
                    "drug": drug,
                    "gene": gene,
                    "status": status
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _search_oncology_trials: {e}")
            return {"error": str(e)}

    async def _get_trial_locations(self, arguments: dict) -> dict:
        """Get location information for a clinical trial."""
        nct_id = arguments["nct_id"]
        country = arguments.get("country")
        state = arguments.get("state")
        
        try:
            # Get trial details first
            detail_result = await self._get_trial_details({"nct_id": nct_id})
            
            if "error" in detail_result:
                return detail_result
            
            trial_details = detail_result.get("trial_details", {})
            all_locations = trial_details.get("locations", [])
            
            # Filter locations if specified
            filtered_locations = []
            for location in all_locations:
                location_country = location.get("country", "")
                location_state = location.get("state", "")
                
                if country and country.lower() not in location_country.lower():
                    continue
                if state and state.lower() not in location_state.lower():
                    continue
                
                filtered_locations.append({
                    "facility": location.get("facility", ""),
                    "city": location.get("city", ""),
                    "state": location.get("state", ""),
                    "country": location.get("country", ""),
                    "zip": location.get("zip", ""),
                    "status": location.get("status", ""),
                    "contacts": location.get("contacts", [])
                })
            
            return {
                "nct_id": nct_id,
                "filter": {
                    "country": country,
                    "state": state
                },
                "total_locations": len(all_locations),
                "filtered_locations": len(filtered_locations),
                "locations": filtered_locations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in _get_trial_locations: {e}")
            return {"error": str(e)}

async def main():
    """Main entry point for the ClinicalTrials.gov MCP server."""
    trials_server = ClinicalTrialsKnowledgeServer()
    trials_server.setup_handlers()
    
    # Initialize server
    options = InitializationOptions(
        server_name="clinicaltrials-search-agent",
        server_version="1.0.0",
        capabilities=trials_server.server.get_capabilities()
    )
    
    async with trials_server.server.run_server() as server:
        logger.info("ClinicalTrials.gov Search Agent MCP Server started")
        try:
            await server.run()
        except KeyboardInterrupt:
            logger.info("ClinicalTrials.gov Search Agent MCP Server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 
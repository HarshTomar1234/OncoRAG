
"""
CancerKnowledgeAgent MCP Server
Manages the 'cancers' collection in MongoDB using official MCP Python SDK FastMCP.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from mcp.server.fastmcp import FastMCP
from bson import ObjectId
import json
import os
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database connection
db_client = None
db = None

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create FastMCP server
mcp = FastMCP("CancerKnowledgeAgent")

async def connect_to_db():
    """Connect to MongoDB database."""
    global db_client, db
    try:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://onco-agent-user:iqh1SqOjGVjCCFLH@oncopilot-devqc-cluster.efwoqpm.mongodb.net/")
        database_name = os.getenv("DATABASE_NAME", "oncopilot-agent")
        
        db_client = AsyncIOMotorClient(mongodb_uri)
        db = db_client[database_name]
        
        # Test connection
        await db_client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {database_name}")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

async def close_db_connection():
    """Close MongoDB connection."""
    global db_client
    if db_client:
        db_client.close()
        logger.info("MongoDB connection closed")

def format_response(data: dict, operation: str, query_params: dict = None) -> dict:
    """Format response with metadata."""
    return {
        "operation": operation,
        "query_parameters": query_params or {},
        "collection": "cancers",
        "timestamp": datetime.now().isoformat(),
        "total_records": len(data.get("results", [])) if isinstance(data.get("results"), list) else 1,
        "data": data
    }

@mcp.tool()
async def search_cancer_by_name(cancer_name: str) -> str:
    """Search for cancer information by name in the cancers collection."""
    try:
        if not db:
            await connect_to_db()
        
        query = {
            "cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}
        }
        
        cursor = db.cancers.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_cancer_by_name", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Search failed: {str(e)}",
            "operation": "search_cancer_by_name",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_cancer_by_biomarker(biomarker: str) -> str:
    """Search for cancers associated with a specific biomarker."""
    try:
        if not db:
            await connect_to_db()
        
        query = {
            "$or": [
                {"cancer_biomarkers_tags": {"$regex": biomarker.strip(), "$options": "i"}},
                {"cancer_biomarkers": {"$regex": biomarker.strip(), "$options": "i"}}
            ]
        }
        
        cursor = db.cancers.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_cancer_by_biomarker", {"biomarker": biomarker})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Biomarker search failed: {str(e)}",
            "operation": "search_cancer_by_biomarker",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_cancer_guidelines(cancer_name: str) -> str:
    """Get clinical guidelines for a specific cancer type."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}}
        projection = {
            "cancer_name": 1,
            "md_anderson_guidelines": 1,
            "esmo_guidelines": 1,
            "nccn_guidelines_titles": 1,
            "nccn_guidelines_links": 1,
            "asco_guidelines_titles": 1,
            "asco_guidelines_links": 1
        }
        
        cursor = db.cancers.find(query, projection).limit(5)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_cancer_guidelines", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Guidelines retrieval failed: {str(e)}",
            "operation": "get_cancer_guidelines",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_cancer_incidence_prevalence(cancer_name: str) -> str:
    """Get incidence and prevalence data for a specific cancer."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}}
        projection = {
            "cancer_name": 1,
            "cancer_incidence_prevalance": 1,
            "cancer_organ_category": 1
        }
        
        cursor = db.cancers.find(query, projection).limit(5)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_cancer_incidence_prevalence", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Incidence data retrieval failed: {str(e)}",
            "operation": "get_cancer_incidence_prevalence",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_cancer_survival_rates(cancer_name: str) -> str:
    """Get survival rates and prognostic information for a cancer type."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}}
        projection = {
            "cancer_name": 1,
            "cancer_survival_rates": 1,
            "cancer_types": 1,
            "subtypes": 1
        }
        
        cursor = db.cancers.find(query, projection).limit(5)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_cancer_survival_rates", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Survival rates retrieval failed: {str(e)}",
            "operation": "get_cancer_survival_rates",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_cancer_by_organ(organ: str) -> str:
    """Search for cancers by organ/body system."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"cancer_organ_category": {"$regex": organ.strip(), "$options": "i"}}
        
        cursor = db.cancers.find(query).limit(15)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_cancer_by_organ", {"organ": organ})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Organ search failed: {str(e)}",
            "operation": "search_cancer_by_organ",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_related_cancers(cancer_name: str) -> str:
    """Find related or similar cancer types."""
    try:
        if not db:
            await connect_to_db()
        
        # First find the specific cancer
        cancer_doc = await db.cancers.find_one(
            {"cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}}
        )
        
        if not cancer_doc:
            return json.dumps({"error": "Cancer not found", "cancer_name": cancer_name}, indent=2)
        
        # Find related cancers by tags or organ category
        query = {
            "$or": [
                {"related_cancers_tags": {"$in": cancer_doc.get("related_cancers_tags", [])}},
                {"cancer_organ_category": cancer_doc.get("cancer_organ_category")},
                {"cancer_biomarkers_tags": {"$in": cancer_doc.get("cancer_biomarkers_tags", [])}}
            ],
            "_id": {"$ne": cancer_doc["_id"]}  # Exclude the original cancer
        }
        
        cursor = db.cancers.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {
            "original_cancer": cancer_doc,
            "related_cancers": results,
            "query": query
        }
        formatted_response = format_response(response_data, "get_related_cancers", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Related cancers search failed: {str(e)}",
            "operation": "get_related_cancers",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_cancer_by_subtype(subtype: str) -> str:
    """Search for cancers by subtype or classification."""
    try:
        if not db:
            await connect_to_db()
        
        query = {
            "$or": [
                {"subtypes_tags": {"$regex": subtype.strip(), "$options": "i"}},
                {"subtypes": {"$regex": subtype.strip(), "$options": "i"}},
                {"cancer_types": {"$regex": subtype.strip(), "$options": "i"}}
            ]
        }
        
        cursor = db.cancers.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_cancer_by_subtype", {"subtype": subtype})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Subtype search failed: {str(e)}",
            "operation": "search_cancer_by_subtype",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_cancer_calculators(cancer_name: str) -> str:
    """Get clinical calculators and tools for a specific cancer type."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"cancer_name": {"$regex": cancer_name.strip(), "$options": "i"}}
        projection = {
            "cancer_name": 1,
            "md_anderson_calulator_titles": 1,
            "md_anderson_calulator_links": 1
        }
        
        cursor = db.cancers.find(query, projection).limit(5)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_cancer_calculators", {"cancer_name": cancer_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Calculators retrieval failed: {str(e)}",
            "operation": "get_cancer_calculators",
            "collection": "cancers"
        }
        return json.dumps(error_response, indent=2)

# Main function to run the server
def main():
    """Main function to run the cancer knowledge MCP server."""
    import asyncio
    
    async def setup_and_run():
        logger.info("🚀 Starting CancerKnowledgeAgent MCP Server...")
        
        # Connect to database
        if await connect_to_db():
            logger.info("Server ready - MongoDB connected")
        else:
            logger.warning("⚠️ Server starting without MongoDB connection")
        
        # Server will run via mcp.run() which handles its own event loop
        
    try:
        if __name__ == "__main__":
            asyncio.run(setup_and_run())
        
        # Run the FastMCP server (this creates its own event loop)
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if __name__ == "__main__":
            asyncio.run(close_db_connection())

if __name__ == "__main__":
    main() 
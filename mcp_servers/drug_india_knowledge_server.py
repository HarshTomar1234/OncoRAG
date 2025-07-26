#!/usr/bin/env python3
"""
DrugIndiaKnowledgeAgent MCP Server
Manages the 'drugs_india' collection in MongoDB using official MCP Python SDK FastMCP.
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
mcp = FastMCP("DrugIndiaKnowledgeAgent")

async def connect_to_db():
    """Connect to MongoDB database."""
    global db_client, db
    try:
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://REDACTED:REDACTED@REDACTED-CLUSTER.mongodb.net/")
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
        "collection": "drugs_india",
        "timestamp": datetime.now().isoformat(),
        "total_records": len(data.get("results", [])) if isinstance(data.get("results"), list) else 1,
        "data": data
    }

@mcp.tool()
async def search_india_drug_by_name(drug_name: str) -> str:
    """Search for drug information in the India drugs collection."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        cursor = db.drugs_india.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_india_drug_by_name", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"India drug search failed: {str(e)}",
            "operation": "search_india_drug_by_name",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_cdsco_approved_drugs(cancer_type: str = None) -> str:
    """Search for CDSCO approved cancer drugs in India."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"is_drug_approved_by_cdsco": "Yes"}
        if cancer_type:
            query["$or"] = [
                {"cancer_types": {"$regex": cancer_type.strip(), "$options": "i"}},
                {"cancer_types_tags": {"$regex": cancer_type.strip(), "$options": "i"}}
            ]
        
        cursor = db.drugs_india.find(query).limit(20)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_cdsco_approved_drugs", {"cancer_type": cancer_type})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"CDSCO approved drugs search failed: {str(e)}",
            "operation": "search_cdsco_approved_drugs",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_india_drug_brands(drug_name: str) -> str:
    """Get Indian brand names and manufacturers for a drug."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        projection = {
            "drug_name": 1, "brand_name": 1, "company_name": 1, "brand_website_links": 1,
            "is_drug_approved": 1, "is_drug_approved_by_cdsco": 1
        }
        
        cursor = db.drugs_india.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_india_drug_brands", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"India drug brands retrieval failed: {str(e)}",
            "operation": "get_india_drug_brands",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_targeted_therapy_india(target: str = None) -> str:
    """Search for targeted therapy drugs available in India."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"type_of_therapy": {"$regex": "Targeted Therapy", "$options": "i"}}
        if target:
            query["$or"] = [
                {"target": {"$regex": target.strip(), "$options": "i"}},
                {"target_tags": {"$regex": target.strip(), "$options": "i"}}
            ]
        
        cursor = db.drugs_india.find(query).limit(15)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_targeted_therapy_india", {"target": target})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Targeted therapy search failed: {str(e)}",
            "operation": "search_targeted_therapy_india",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_india_drug_pricing_info(drug_name: str) -> str:
    """Get pricing and availability information for drugs in India."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        projection = {
            "drug_name": 1, "brand_name": 1, "company_name": 1, "contact_information": 1,
            "is_drug_approved_by_cdsco": 1, "product_status": 1
        }
        
        cursor = db.drugs_india.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_india_drug_pricing_info", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Pricing info retrieval failed: {str(e)}",
            "operation": "get_india_drug_pricing_info",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_chemotherapy_drugs_india(cancer_type: str = None) -> str:
    """Search for chemotherapy drugs available in India."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"is_chemotherapy_drug": True}
        if cancer_type:
            query["$or"] = [
                {"cancer_types": {"$regex": cancer_type.strip(), "$options": "i"}},
                {"cancer_types_tags": {"$regex": cancer_type.strip(), "$options": "i"}}
            ]
        
        cursor = db.drugs_india.find(query).limit(15)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_chemotherapy_drugs_india", {"cancer_type": cancer_type})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Chemotherapy drugs search failed: {str(e)}",
            "operation": "search_chemotherapy_drugs_india",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_india_drug_biomarkers(drug_name: str) -> str:
    """Get biomarker and companion diagnostic information for India drugs."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        projection = {
            "drug_name": 1, "biomarkers": 1, "biomarkers_tags": 1, "biomarker_description": 1,
            "biomarker_test_score": 1, "biomarker_interpretation": 1, "gene_mutations": 1
        }
        
        cursor = db.drugs_india.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_india_drug_biomarkers", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"India drug biomarkers retrieval failed: {str(e)}",
            "operation": "get_india_drug_biomarkers",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_india_clinical_trials(drug_name: str) -> str:
    """Get clinical trials information for drugs in India."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        projection = {
            "drug_name": 1, "landmark_clinical_trial_id": 1, "ct_phase": 1, "ct_title": 1,
            "ct_publication_titles": 1, "ct_publication_links": 1, "intrial_drug_nct": 1,
            "ongoing_clinical_trials_master_link": 1
        }
        
        cursor = db.drugs_india.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_india_clinical_trials", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"India clinical trials retrieval failed: {str(e)}",
            "operation": "get_india_clinical_trials",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_india_drug_abbreviations(abbreviation: str) -> str:
    """Search for drugs by their abbreviations or short forms."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"abbreviations": {"$regex": abbreviation.strip(), "$options": "i"}}
        cursor = db.drugs_india.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_india_drug_abbreviations", {"abbreviation": abbreviation})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Abbreviations search failed: {str(e)}",
            "operation": "search_india_drug_abbreviations",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_india_drug_mechanism(drug_name: str) -> str:
    """Get mechanism of action and drug class information for India drugs."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"drug_name": {"$regex": drug_name.strip(), "$options": "i"}}
        projection = {
            "drug_name": 1, "mechanism_of_action": 1, "drug_class": 1, "type_of_therapy": 1,
            "target": 1, "target_tags": 1
        }
        
        cursor = db.drugs_india.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_india_drug_mechanism", {"drug_name": drug_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Mechanism info retrieval failed: {str(e)}",
            "operation": "get_india_drug_mechanism",
            "collection": "drugs_india"
        }
        return json.dumps(error_response, indent=2)

# Main function to run the server
def main():
    """Main function to run the drug India knowledge MCP server."""
    import asyncio
    
    async def setup_and_run():
        logger.info("🚀 Starting DrugIndiaKnowledgeAgent MCP Server...")
        
        # Connect to database
        if await connect_to_db():
            logger.info("✅ Server ready - MongoDB connected")
        else:
            logger.warning("⚠️ Server starting without MongoDB connection")
        
    try:
        # Only run database setup if we're the main script
        if __name__ == "__main__":
            asyncio.run(setup_and_run())
        
        # Run the FastMCP server (this creates its own event loop)
        mcp.run()
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if __name__ == "__main__":
            asyncio.run(close_db_connection())

if __name__ == "__main__":
    main() 
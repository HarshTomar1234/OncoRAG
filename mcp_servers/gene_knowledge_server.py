#!/usr/bin/env python3
"""
GeneKnowledgeAgent MCP Server
Manages the 'genes' collection in MongoDB using official MCP Python SDK FastMCP.
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
mcp = FastMCP("GeneKnowledgeAgent")

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
        "collection": "genes",
        "timestamp": datetime.now().isoformat(),
        "total_records": len(data.get("results", [])) if isinstance(data.get("results"), list) else 1,
        "data": data
    }

@mcp.tool()
async def search_gene_by_name(gene_name: str) -> str:
    """Search for gene information by name in the genes collection."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        cursor = db.genes.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_gene_by_name", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Gene search failed: {str(e)}",
            "operation": "search_gene_by_name",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_drug_associations(gene_name: str) -> str:
    """Get drug associations and therapeutic targets for a gene."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "drug_name": 1, "constituent_drugs": 1, "efficacy": 1,
            "brand_name": 1, "company_name": 1, "is_drug_approved": 1, "product_status": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_drug_associations", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Drug associations retrieval failed: {str(e)}",
            "operation": "get_gene_drug_associations",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_prognosis_impact(gene_name: str) -> str:
    """Get prognostic impact and clinical significance of gene mutations."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "prognosis": 1, "cancer_types": 1, "subtypes": 1, "incidence": 1, "overview": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_prognosis_impact", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Prognosis impact retrieval failed: {str(e)}",
            "operation": "get_gene_prognosis_impact",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_clinical_trials(gene_name: str) -> str:
    """Get clinical trials information for a specific gene."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "landmark_clinical_trial_id": 1, "ct_phase": 1, "ct_title": 1,
            "ct_location": 1, "ct_publication_titles": 1, "ct_publication_links": 1, "intrial_drug_nct": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_clinical_trials", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Clinical trials retrieval failed: {str(e)}",
            "operation": "get_gene_clinical_trials",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_genes_by_cancer_type(cancer_type: str) -> str:
    """Search for genes associated with a specific cancer type."""
    try:
        if not db:
            await connect_to_db()
        
        query = {
            "$or": [
                {"cancer_types": {"$regex": cancer_type.strip(), "$options": "i"}},
                {"cancer_types_tags": {"$regex": cancer_type.strip(), "$options": "i"}}
            ]
        }
        
        cursor = db.genes.find(query).limit(15)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_genes_by_cancer_type", {"cancer_type": cancer_type})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Cancer type gene search failed: {str(e)}",
            "operation": "search_genes_by_cancer_type",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_mutations_info(gene_name: str) -> str:
    """Get information about co-occurring mutations and mutation patterns."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "gene_cancer_cooccurring_mutations": 1,
            "gene_cancer_coocurring_mutations_source_apas": 1,
            "gene_cancer_coocurring_mutations_source_links": 1, "ncbi_gene_code_for_gene": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_mutations_info", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Mutations info retrieval failed: {str(e)}",
            "operation": "get_gene_mutations_info",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_drug_targets(gene_name: str) -> str:
    """Get drug target information and mechanism of action for a gene."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "drug_target": 1, "gene_drug_target_sources": 1,
            "drug_overview": 1, "gene_drug_overview_sources": 1, "is_combination": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_drug_targets", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"Drug targets retrieval failed: {str(e)}",
            "operation": "get_gene_drug_targets",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def get_gene_fda_info(gene_name: str) -> str:
    """Get FDA regulatory information for gene-related drugs."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"gene_name": {"$regex": gene_name.strip(), "$options": "i"}}
        projection = {
            "gene_name": 1, "drug_fda_filename": 1, "drug_fda_link": 1,
            "is_drug_approved": 1, "product_status": 1
        }
        
        cursor = db.genes.find(query, projection).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "get_gene_fda_info", {"gene_name": gene_name})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"FDA info retrieval failed: {str(e)}",
            "operation": "get_gene_fda_info",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

@mcp.tool()
async def search_genes_by_ncbi_code(ncbi_code: str) -> str:
    """Search for genes using NCBI gene code."""
    try:
        if not db:
            await connect_to_db()
        
        query = {"ncbi_gene_code_for_gene": {"$regex": ncbi_code.strip(), "$options": "i"}}
        cursor = db.genes.find(query).limit(10)
        results = []
        async for doc in cursor:
            results.append(doc)
        
        response_data = {"results": results, "query": query}
        formatted_response = format_response(response_data, "search_genes_by_ncbi_code", {"ncbi_code": ncbi_code})
        
        return json.dumps(formatted_response, cls=JSONEncoder, indent=2)
        
    except Exception as e:
        error_response = {
            "error": f"NCBI code search failed: {str(e)}",
            "operation": "search_genes_by_ncbi_code",
            "collection": "genes"
        }
        return json.dumps(error_response, indent=2)

# Main function to run the server
def main():
    """Main function to run the gene knowledge MCP server."""
    import asyncio
    
    async def setup_and_run():
        logger.info("🚀 Starting GeneKnowledgeAgent MCP Server...")
        
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
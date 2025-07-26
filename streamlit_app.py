#!/usr/bin/env python3
"""
OncoPilot MCP Collection-Centric System - Streamlit Chat Interface
Multi-collection oncology query interface with database, web search, and literature capabilities.
"""

import asyncio
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.query_orchestrator import EnhancedQueryOrchestrator

# Configure Streamlit page
st.set_page_config(
    page_title="OncoPilot MCP System",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False

@st.cache_resource
def initialize_orchestrator():
    """Initialize the Enhanced Query Orchestrator."""
    try:
        orchestrator = EnhancedQueryOrchestrator()
        return orchestrator, True, "Query Orchestrator initialized successfully"
    except Exception as e:
        return None, False, f"Failed to initialize Query Orchestrator: {str(e)}"

def display_system_info():
    """Display system information in the sidebar."""
    st.sidebar.title("🧬 OncoPilot MCP System")
    st.sidebar.markdown("### System Architecture")
    st.sidebar.markdown("""
    **Collection-Centric Multi-Agent System**
    
    **Database Collections:**
    - 🔬 **Cancers**: Biomarkers, guidelines, survival data
    - 🧬 **Genes**: Mutations, drug associations, prognosis
    - 💊 **Drugs**: Global efficacy, safety profiles
    - 🇮🇳 **Drugs India**: CDSCO approval, local availability
    
    **External Sources:**
    - 🌐 **Web Search**: Latest medical news & updates
    - 📚 **PubMed**: Scientific literature & research
    - 🧪 **Clinical Trials**: Ongoing & completed studies
    """)

def display_query_examples():
    """Display example queries."""
    st.sidebar.markdown("### 📝 Example Queries")
    
    examples = {
        "🔬 Cancer Information": [
            "What are the biomarkers for lung cancer?",
            "NCCN guidelines for breast cancer",
            "MSI-H colorectal cancer survival rates"
        ],
        "🧬 Gene Analysis": [
            "EGFR mutation drugs",
            "TP53 gene prognosis impact",
            "BRAF mutations in melanoma"
        ],
        "💊 Drug Information": [
            "Pembrolizumab efficacy data",
            "Side effects of trastuzumab",
            "Drugs targeting HER2 receptor"
        ],
        "🇮🇳 India-Specific": [
            "Is imatinib available in India?",
            "CDSCO approved cancer drugs",
            "Indian brands of erlotinib"
        ],
        "🔍 Multi-Collection": [
            "Efficacy of pembrolizumab for MSI-H colorectal cancer in India",
            "EGFR mutation treatment options in India",
            "HER2 positive breast cancer biomarkers and drugs"
        ],
        "🌐 External Sources": [
            "Latest cancer research papers",
            "Recent news about immunotherapy",
            "Clinical trials for lung cancer"
        ]
    }
    
    for category, queries in examples.items():
        with st.sidebar.expander(category):
            for query in queries:
                if st.button(query, key=f"example_{hash(query)}"):
                    st.session_state.example_query = query

def format_response_data(response: Dict[str, Any]) -> str:
    """Format the response data for display."""
    try:
        # Extract key information
        summary = response.get('summary', 'No summary available')
        query_complexity = response.get('query_complexity', 'unknown')
        agents_used = response.get('agents_used', [])
        collections_queried = response.get('collections_queried', [])
        
        # Format the response
        formatted = f"""
**Query Analysis:** {query_complexity.replace('_', ' ').title()}

**Summary:** {summary}

**Sources Used:**
- **Collections:** {', '.join(collections_queried) if collections_queried else 'None'}
- **Agents:** {', '.join(agents_used) if agents_used else 'None'}

**Response Details:**
- Database Results: {response.get('database_results', 0)}
- External Results: {response.get('external_results', 0)}
- Total Successful: {response.get('successful_responses', 0)}
- Failed: {response.get('failed_responses', 0)}
"""
        
        # Add detailed responses if available
        detailed_responses = response.get('detailed_responses', [])
        if detailed_responses:
            formatted += "\n**Detailed Results:**\n"
            for i, detail in enumerate(detailed_responses[:3], 1):  # Limit to 3 for display
                agent = detail.get('agent', 'Unknown')
                collection = detail.get('collection', 'Unknown')
                entity = detail.get('entity', 'Unknown')
                tools_used = detail.get('tools_used', [])
                
                formatted += f"""
**Result {i} - {agent}**
- Collection: {collection}
- Entity: {entity}
- Tools: {', '.join(tools_used) if tools_used else 'None'}
"""
                
                # Add sample data if available
                data = detail.get('data', {})
                if isinstance(data, dict) and 'data' in data:
                    sample_data = data['data']
                    if isinstance(sample_data, dict) and 'results' in sample_data:
                        results = sample_data['results']
                        if results and isinstance(results, list):
                            formatted += f"- Records Found: {len(results)}\n"
                            if len(results) > 0:
                                first_result = results[0]
                                if isinstance(first_result, dict):
                                    # Show a few key fields
                                    key_fields = ['name', 'drug_name', 'cancer_name', 'gene_name', 'efficacy', 'description']
                                    for field in key_fields:
                                        if field in first_result:
                                            value = str(first_result[field])[:100]
                                            formatted += f"- {field.replace('_', ' ').title()}: {value}{'...' if len(str(first_result[field])) > 100 else ''}\n"
                                            break
        
        return formatted
        
    except Exception as e:
        return f"Error formatting response: {str(e)}\n\nRaw response: {json.dumps(response, indent=2)}"

async def process_query_async(query: str, orchestrator: EnhancedQueryOrchestrator) -> Dict[str, Any]:
    """Process query asynchronously."""
    return await orchestrator.process_query(query)

def main():
    """Main Streamlit application."""
    
    # Initialize orchestrator
    if not st.session_state.system_initialized:
        with st.spinner("Initializing OncoPilot MCP System..."):
            orchestrator, success, message = initialize_orchestrator()
            if success:
                st.session_state.orchestrator = orchestrator
                st.session_state.system_initialized = True
                st.success(message)
            else:
                st.error(message)
                st.stop()
    
    # Display system info and examples
    display_system_info()
    display_query_examples()
    
    # Main content area
    st.title("🧬 OncoPilot MCP Collection-Centric System")
    st.markdown("**Multi-Agent Oncology Intelligence Platform**")
    
    # System status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", "🟢 Active")
    with col2:
        st.metric("Collections", "4")
    with col3:
        st.metric("External Sources", "3")
    with col4:
        st.metric("Total Agents", "7")
    
    st.markdown("---")
    
    # Chat interface
    st.markdown("### 💬 Chat Interface")
    
    # Query input
    query_input = st.text_input(
        "Enter your oncology query:",
        placeholder="e.g., 'Efficacy of pembrolizumab for MSI-H colorectal cancer in India'",
        help="Ask about cancer types, genes, drugs, treatments, or request web search and literature review."
    )
    
    # Handle example query selection
    if 'example_query' in st.session_state:
        query_input = st.session_state.example_query
        del st.session_state.example_query
        st.rerun()
    
    # Query processing
    col1, col2 = st.columns([1, 4])
    with col1:
        submit_button = st.button("🔍 Submit Query", type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History")
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    if submit_button and query_input.strip():
        if st.session_state.orchestrator:
            # Add query to history
            st.session_state.chat_history.append({
                "type": "user",
                "content": query_input,
                "timestamp": datetime.now()
            })
            
            # Process query
            with st.spinner("🔍 Processing your query across multiple sources..."):
                try:
                    # Run async function
                    response = asyncio.run(process_query_async(query_input, st.session_state.orchestrator))
                    
                    # Add response to history
                    st.session_state.chat_history.append({
                        "type": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    })
                    
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
                    # Add error to history
                    st.session_state.chat_history.append({
                        "type": "error",
                        "content": f"Error: {str(e)}",
                        "timestamp": datetime.now()
                    })
        else:
            st.error("System not initialized. Please refresh the page.")
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 📝 Query History & Results")
        
        for i, entry in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10 entries
            timestamp = entry["timestamp"].strftime("%H:%M:%S")
            
            if entry["type"] == "user":
                st.markdown(f"**🤔 You ({timestamp}):**")
                st.markdown(f"> {entry['content']}")
                
            elif entry["type"] == "assistant":
                st.markdown(f"**🤖 OncoPilot ({timestamp}):**")
                
                # Create expandable sections for detailed view
                response_data = entry["content"]
                
                if isinstance(response_data, dict):
                    formatted_response = format_response_data(response_data)
                    st.markdown(formatted_response)
                    
                    # Expandable raw data
                    with st.expander("🔍 View Raw Response Data"):
                        st.json(response_data)
                        
                    # Download option
                    if st.button(f"💾 Download Response Data", key=f"download_{i}"):
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(response_data, indent=2),
                            file_name=f"oncopilot_response_{timestamp.replace(':', '')}.json",
                            mime="application/json"
                        )
                else:
                    st.markdown(str(response_data))
                    
            elif entry["type"] == "error":
                st.error(f"**❌ Error ({timestamp}):** {entry['content']}")
            
            st.markdown("---")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔬 Collections:** cancers, genes, drugs, drugs_india")
    with col2:
        st.markdown("**🌐 External:** web search, pubmed, clinical trials")
    with col3:
        st.markdown("**🧠 Architecture:** Collection-Centric Multi-Agent")

if __name__ == "__main__":
    main() 
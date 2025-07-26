#!/usr/bin/env python3
"""
Start all MCP servers for the OncoPilot system.
This script launches all database and external MCP servers as separate processes.
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path
from typing import List, Dict

def start_mcp_server(server_name: str, script_path: str, port: int = None) -> subprocess.Popen:
    """Start an individual MCP server with error capture."""
    try:
        # Set environment variables for the subprocess
        env = os.environ.copy()
        if not env.get("MONGODB_URI"):
            env["MONGODB_URI"] = "mongodb+srv://onco-agent-user:iqh1SqOjGVjCCFLH@oncopilot-devqc-cluster.efwoqpm.mongodb.net/"
        if not env.get("DATABASE_NAME"):
            env["DATABASE_NAME"] = "oncopilot-agent"
        
        # Build command
        cmd = [sys.executable, script_path]
        
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True,
            env=env  # Pass environment variables
        )
        
        # Give the process a moment to start
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            print(f"✅ Started {server_name} (PID: {process.pid})")
            return process
        else:
            # Process has already exited, get the error
            stdout, _ = process.communicate()
            print(f"❌ {server_name} failed to start (exit code: {process.returncode})")
            print(f"   Error output: {stdout[:200]}...")  # Show first 200 chars of error
            return None
        
    except Exception as e:
        print(f"❌ Exception starting {server_name}: {e}")
        return None

def test_individual_server(script_path: str, server_name: str):
    """Test running a single server to see detailed error output."""
    print(f"\n🔍 Testing {server_name} individually...")
    
    env = os.environ.copy()
    if not env.get("MONGODB_URI"):
        env["MONGODB_URI"] = "mongodb+srv://onco-agent-user:iqh1SqOjGVjCCFLH@oncopilot-devqc-cluster.efwoqpm.mongodb.net/"
    if not env.get("DATABASE_NAME"):
        env["DATABASE_NAME"] = "oncopilot-agent"
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, "--help"],  # Try help first
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0:
            print(f"✅ {server_name} help command works")
        else:
            print(f"❌ {server_name} help failed:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {server_name} timed out (might be waiting for input)")
    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    required_modules = ['mcp', 'motor', 'bson', 'httpx']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - missing")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    return True

def main():
    """Start all MCP servers with better error handling."""
    print("🧬 Starting OncoPilot MCP Servers")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Please install missing dependencies first")
        return 1
    
    # Define all MCP servers
    servers = [
        {
            "name": "CancerKnowledgeServer",
            "script": "mcp_servers/cancer_knowledge_server.py",
        },
        {
            "name": "GeneKnowledgeServer", 
            "script": "mcp_servers/gene_knowledge_server.py",
        },
        {
            "name": "DrugKnowledgeServer",
            "script": "mcp_servers/drug_knowledge_server.py", 
        },
        {
            "name": "DrugIndiaKnowledgeServer",
            "script": "mcp_servers/drug_india_knowledge_server.py",
        },
        {
            "name": "WebSearchServer",
            "script": "mcp_servers/websearch_server.py",
        },
        {
            "name": "PubMedServer",
            "script": "mcp_servers/pubmed_server.py",
        },
        {
            "name": "ClinicalTrialsServer",
            "script": "mcp_servers/clinicaltrials_server.py",
        }
    ]
    
    # Test a single server first to diagnose issues
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_individual_server(servers[0]["script"], servers[0]["name"])
        return 0
    
    processes = []
    failed_servers = []
    
    # Start each server
    for server in servers:
        script_path = Path(server["script"])
        if not script_path.exists():
            print(f"⚠️  Script not found: {script_path}")
            failed_servers.append(server["name"])
            continue
            
        process = start_mcp_server(server["name"], str(script_path))
        
        if process:
            processes.append({
                "name": server["name"],
                "process": process,
                "script": server["script"]
            })
        else:
            failed_servers.append(server["name"])
    
    if not processes:
        print("\n❌ No servers started successfully!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if MCP framework is installed: pip install mcp")
        print("2. Verify MongoDB connection in environment variables")
        print("3. Test individual server: python start_mcp_servers.py --test")
        print("4. Check server logs for detailed errors")
        return 1
    
    print(f"\n🎉 Started {len(processes)} out of {len(servers)} MCP servers successfully!")
    
    if failed_servers:
        print(f"⚠️  Failed servers: {', '.join(failed_servers)}")
    
    print("\n📊 Running Server Status:")
    for p in processes:
        status = "Running" if p["process"].poll() is None else "Stopped"
        print(f"   {p['name']}: {status} (PID: {p['process'].pid})")
    
    print("\n" + "=" * 50)
    print("💡 Now you can run:")
    print("   python run_streamlit.py")
    print("\n🛑 To stop all servers, press Ctrl+C")
    
    try:
        # Monitor processes
        while True:
            time.sleep(5)
            
            # Check if any processes have died
            for p in processes[:]:
                if p["process"].poll() is not None:
                    # Get the error output
                    try:
                        stdout, stderr = p["process"].communicate(timeout=1)
                        print(f"\n⚠️  {p['name']} stopped (exit code: {p['process'].poll()})")
                        if stdout:
                            print(f"   Output: {stdout[:300]}...")
                    except:
                        print(f"\n⚠️  {p['name']} stopped (exit code: {p['process'].poll()})")
                    
                    processes.remove(p)
            
            if not processes:
                print("\n❌ All MCP servers have stopped. Check the error messages above.")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all MCP servers...")
        
        # Terminate all processes
        for p in processes:
            try:
                p["process"].terminate()
                p["process"].wait(timeout=5)
                print(f"✅ Stopped {p['name']}")
            except subprocess.TimeoutExpired:
                p["process"].kill()
                print(f"🔧 Force-killed {p['name']}")
            except Exception as e:
                print(f"❌ Error stopping {p['name']}: {e}")
    
    print("🏁 All MCP servers stopped.")
    return 0

if __name__ == "__main__":
    exit(main()) 
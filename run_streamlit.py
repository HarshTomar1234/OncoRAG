#!/usr/bin/env python3
"""
OncoPilot MCP System - Streamlit App Runner
Launches the Streamlit interface for the collection-centric oncology query system.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    required_packages = [
        'streamlit',
        'pandas', 
        'bson',
        'httpx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    # Special check for motor (MongoDB async driver)
    try:
        import motor.motor_asyncio
        print("✅ motor (MongoDB async driver)")
    except ImportError:
        print("❌ motor (MongoDB async driver) - missing")
        missing_packages.append('motor')
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print("\n   Or install all requirements:")
        print("   pip install -r requirements_streamlit.txt")
        
        # For motor specifically, give additional help
        if 'motor' in missing_packages:
            print("\n🔧 If motor installation fails, try:")
            print("   pip install --user motor")
            print("   or")
            print("   python -m pip install motor")
        
        return False
    
    print("✅ All required packages are installed!")
    return True

def setup_environment():
    """Setup environment variables and configuration."""
    # Set default MongoDB URI if not provided
    if not os.getenv("MONGODB_URI"):
        os.environ["MONGODB_URI"] = "mongodb+srv://onco-agent-user:iqh1SqOjGVjCCFLH@oncopilot-devqc-cluster.efwoqpm.mongodb.net/"
        print("🔧 Using default MongoDB URI")
    
    if not os.getenv("DATABASE_NAME"):
        os.environ["DATABASE_NAME"] = "oncopilot-agent"
        print("🔧 Using default database name: oncopilot-agent")

def run_streamlit():
    """Run the Streamlit app."""
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ Streamlit app not found at {app_path}")
        return False
    
    print("🚀 Starting OncoPilot MCP Streamlit App...")
    print("🌐 App will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run streamlit with configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--theme.base=light",
            "--theme.primaryColor=#1f77b4",
            "--theme.backgroundColor=#ffffff"
        ]
        
        subprocess.run(cmd, cwd=str(app_path.parent))
        
    except KeyboardInterrupt:
        print("\n\n🛑 Streamlit app stopped by user")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {e}")
        return False
    
    return True

def main():
    """Main function to run the setup and start the app."""
    print("🧬 OncoPilot MCP System - Streamlit Interface")
    print("=" * 50)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "streamlit_app.py").exists():
        print("❌ Please run this script from the Oncology MCP directory")
        print(f"   Current directory: {current_dir}")
        print("   Expected file: streamlit_app.py")
        return 1
    
    # Check requirements
    print("🔍 Checking dependencies...")
    if not check_requirements():
        print("\n💡 After installing dependencies, run this script again")
        return 1
    
    # Setup environment
    setup_environment()
    
    # Run the app
    if run_streamlit():
        print("✅ App started successfully")
        return 0
    else:
        print("❌ Failed to start app")
        return 1

if __name__ == "__main__":
    exit(main()) 
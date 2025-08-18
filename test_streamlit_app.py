#!/usr/bin/env python3
"""
Test script to verify the Streamlit app launches properly
"""

import subprocess
import sys
import time
import webbrowser
import os

def test_streamlit_app():
    """Test that the Streamlit app launches successfully"""
    
    print("🧪 Testing Streamlit App Launch...")
    
    # Check if we're in the right directory
    if not os.path.exists("src/chatbot/app.py"):
        print("❌ Error: app.py not found. Make sure you're in the salesforce-rag-bot directory.")
        return False
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Error: Streamlit not installed. Run: pip install streamlit")
        return False
    
    # Test app import
    try:
        import src.chatbot.app
        print("✅ App imports successfully")
    except Exception as e:
        print(f"❌ Error importing app: {e}")
        return False
    
    print("\n🚀 Launching Streamlit app...")
    print("📝 Instructions:")
    print("1. The app should open in your browser at http://localhost:8501")
    print("2. If it doesn't open automatically, manually navigate to that URL")
    print("3. You should see the Salesforce Schema AI Assistant interface")
    print("4. The app will show configuration warnings if API keys aren't set")
    print("5. Press Ctrl+C in this terminal to stop the app")
    
    try:
        # Launch the app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "src/chatbot/app.py"], 
                      check=True)
    except KeyboardInterrupt:
        print("\n🛑 App stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching app: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_streamlit_app()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
        sys.exit(1)

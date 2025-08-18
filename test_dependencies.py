#!/usr/bin/env python3
"""
Comprehensive dependency test for the Salesforce RAG Bot.
Tests all required packages and their functionality.
"""

import sys
import os
from pathlib import Path

def test_core_dependencies():
    """Test core dependencies for the pipeline."""
    print("🔍 Testing Core Dependencies...")
    
    core_packages = [
        ('pinecone', 'Pinecone'),
        ('openai', 'OpenAI'),
        ('dotenv', 'load_dotenv'),
        ('tiktoken', 'encoding_for_model'),
        ('pandas', 'DataFrame'),
        ('numpy', 'array'),
        ('requests', 'get')
    ]
    
    results = []
    for package, import_name in core_packages:
        try:
            if package == 'dotenv':
                from dotenv import load_dotenv
                print(f"✅ {package} (python-dotenv)")
            elif package == 'pinecone':
                from pinecone import Pinecone
                print(f"✅ {package}")
            elif package == 'openai':
                from openai import OpenAI
                print(f"✅ {package}")
            elif package == 'tiktoken':
                import tiktoken
                tiktoken.encoding_for_model("gpt-4")
                print(f"✅ {package}")
            elif package == 'pandas':
                import pandas as pd
                pd.DataFrame()
                print(f"✅ {package}")
            elif package == 'numpy':
                import numpy as np
                np.array([1, 2, 3])
                print(f"✅ {package}")
            elif package == 'requests':
                import requests
                requests.get
                print(f"✅ {package}")
            results.append(True)
        except ImportError as e:
            print(f"❌ {package}: {e}")
            results.append(False)
        except Exception as e:
            print(f"⚠️  {package}: {e}")
            results.append(False)
    
    return all(results)

def test_langchain_dependencies():
    """Test LangChain ecosystem dependencies."""
    print("\n🔍 Testing LangChain Ecosystem...")
    
    langchain_packages = [
        ('langchain', 'langchain'),
        ('langchain_community', 'langchain_community'),
        ('langchain_openai', 'langchain_openai'),
        ('langchain_anthropic', 'langchain_anthropic'),
        ('langchain_google_genai', 'langchain_google_genai'),
        ('langchain_pinecone', 'langchain_pinecone')
    ]
    
    results = []
    for package, import_name in langchain_packages:
        try:
            __import__(import_name)
            print(f"✅ {package}")
            results.append(True)
        except ImportError as e:
            print(f"❌ {package}: {e}")
            results.append(False)
    
    return all(results)

def test_streamlit():
    """Test Streamlit installation."""
    print("\n🔍 Testing Streamlit...")
    
    try:
        import streamlit as st
        print(f"✅ streamlit {st.__version__}")
        return True
    except ImportError as e:
        print(f"❌ streamlit: {e}")
        return False

def test_llm_providers():
    """Test LLM provider integrations."""
    print("\n🔍 Testing LLM Providers...")
    
    providers = [
        ('anthropic', 'anthropic'),
        ('google.generativeai', 'google.generativeai')
    ]
    
    results = []
    for package, import_name in providers:
        try:
            __import__(import_name)
            print(f"✅ {package}")
            results.append(True)
        except ImportError as e:
            print(f"❌ {package}: {e}")
            results.append(False)
    
    return all(results)

def test_pipeline_script():
    """Test that the pipeline script can be imported."""
    print("\n🔍 Testing Pipeline Script...")
    
    try:
        # Add the pipeline directory to the path
        pipeline_dir = Path(__file__).parent / "src" / "pipeline"
        sys.path.insert(0, str(pipeline_dir))
        
        import build_schema_library_end_to_end
        print("✅ Pipeline script imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Pipeline script: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Pipeline script: {e}")
        return False

def test_requirements_files():
    """Test that requirements files exist and are valid."""
    print("\n🔍 Testing Requirements Files...")
    
    requirements_files = [
        Path(__file__).parent / "requirements.txt",
        Path(__file__).parent / "src" / "chatbot" / "requirements.txt"
    ]
    
    results = []
    for req_file in requirements_files:
        if req_file.exists():
            print(f"✅ {req_file.name} exists")
            results.append(True)
        else:
            print(f"❌ {req_file.name} missing")
            results.append(False)
    
    return all(results)

def test_project_structure():
    """Test that the project structure is correct."""
    print("\n🔍 Testing Project Structure...")
    
    required_dirs = [
        Path(__file__).parent / ".github" / "workflows",
        Path(__file__).parent / "src" / "pipeline",
        Path(__file__).parent / "src" / "chatbot"
    ]
    
    required_files = [
        Path(__file__).parent / "requirements.txt",
        Path(__file__).parent / "Dockerfile",
        Path(__file__).parent / "README.md",
        Path(__file__).parent / "src" / "pipeline" / "build_schema_library_end_to_end.py"
    ]
    
    results = []
    
    # Check directories
    for dir_path in required_dirs:
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ Directory: {dir_path.relative_to(Path(__file__).parent)}")
            results.append(True)
        else:
            print(f"❌ Directory missing: {dir_path.relative_to(Path(__file__).parent)}")
            results.append(False)
    
    # Check files
    for file_path in required_files:
        if file_path.exists() and file_path.is_file():
            print(f"✅ File: {file_path.relative_to(Path(__file__).parent)}")
            results.append(True)
        else:
            print(f"❌ File missing: {file_path.relative_to(Path(__file__).parent)}")
            results.append(False)
    
    return all(results)

def main():
    """Run all dependency tests."""
    print("🚀 Salesforce RAG Bot - Dependency Test Suite")
    print("=" * 60)
    
    tests = [
        ("Core Dependencies", test_core_dependencies),
        ("LangChain Ecosystem", test_langchain_dependencies),
        ("Streamlit", test_streamlit),
        ("LLM Providers", test_llm_providers),
        ("Pipeline Script", test_pipeline_script),
        ("Requirements Files", test_requirements_files),
        ("Project Structure", test_project_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All dependencies are properly installed and working!")
        print("✅ The Salesforce RAG Bot is ready for development.")
        return True
    else:
        print("⚠️  Some dependencies are missing or not working properly.")
        print("💡 Run 'pip install -r requirements.txt' to install missing packages.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

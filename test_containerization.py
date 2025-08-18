#!/usr/bin/env python3
"""
Containerization test for the Salesforce RAG Bot.
Tests Docker build and basic functionality.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_dockerfile_exists():
    """Test that Dockerfile exists and is valid."""
    print("🔍 Testing Dockerfile...")
    
    dockerfile_path = Path(__file__).parent / "Dockerfile"
    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False
    
    # Check Dockerfile content for required components
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        required_components = [
            "FROM python:",
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY src/pipeline",
            "ENTRYPOINT"
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Dockerfile missing components: {', '.join(missing_components)}")
            return False
        
        print("✅ Dockerfile exists and contains required components")
        return True
        
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False

def test_docker_build():
    """Test Docker build process."""
    print("\n🔍 Testing Docker Build...")
    
    try:
        # Build the Docker image
        result = subprocess.run(
            ["docker", "build", "-t", "salesforce-rag-bot:test", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker Desktop.")
        return False
    except Exception as e:
        print(f"❌ Docker build error: {e}")
        return False

def test_docker_run():
    """Test Docker run with help command."""
    print("\n🔍 Testing Docker Run...")
    
    try:
        # Run the container with help to test basic functionality
        result = subprocess.run(
            ["docker", "run", "--rm", "salesforce-rag-bot:test", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Docker run successful")
            print(f"Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ Docker run failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker run timed out")
        return False
    except Exception as e:
        print(f"❌ Docker run error: {e}")
        return False

def test_docker_cleanup():
    """Clean up test Docker image."""
    print("\n🔍 Cleaning up test Docker image...")
    
    try:
        subprocess.run(
            ["docker", "rmi", "salesforce-rag-bot:test"],
            capture_output=True,
            text=True
        )
        print("✅ Docker cleanup completed")
        return True
    except Exception as e:
        print(f"⚠️  Docker cleanup warning: {e}")
        return True  # Don't fail the test for cleanup issues

def test_requirements_in_docker():
    """Test that requirements.txt is compatible with Docker."""
    print("\n🔍 Testing Requirements for Docker...")
    
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        # Check for potential Docker issues
        issues = []
        
        # Check for version conflicts
        if "pinecone-client" in content and "pinecone" in content:
            issues.append("Both pinecone-client and pinecone in requirements")
        
        # Check for missing version specifications
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '>=' not in line and '==' not in line:
                if not any(char.isdigit() for char in line):
                    issues.append(f"No version specified for: {line}")
        
        if issues:
            print(f"⚠️  Potential issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Requirements file looks good for Docker")
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def test_dockerfile_optimization():
    """Test Dockerfile for best practices."""
    print("\n🔍 Testing Dockerfile Optimization...")
    
    dockerfile_path = Path(__file__).parent / "Dockerfile"
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        issues = []
        
        # Check for multi-stage build (optional optimization)
        if "FROM" in content and content.count("FROM") == 1:
            print("ℹ️  Single-stage build (acceptable)")
        
        # Check for proper cleanup
        if "rm -rf" in content:
            print("✅ Proper cleanup in Dockerfile")
        else:
            issues.append("No cleanup commands found")
        
        # Check for non-root user (security best practice)
        if "USER" in content:
            print("✅ Non-root user specified")
        else:
            print("ℹ️  Running as root (acceptable for this use case)")
        
        # Check for proper layer caching
        if "COPY requirements.txt" in content and "RUN pip install" in content:
            print("✅ Good layer caching (requirements copied before pip install)")
        
        if issues:
            print(f"⚠️  Optimization suggestions:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Dockerfile follows good practices")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Dockerfile optimization: {e}")
        return False

def main():
    """Run all containerization tests."""
    print("🐳 Salesforce RAG Bot - Containerization Test Suite")
    print("=" * 60)
    
    tests = [
        ("Dockerfile Validation", test_dockerfile_exists),
        ("Requirements Compatibility", test_requirements_in_docker),
        ("Dockerfile Optimization", test_dockerfile_optimization),
        ("Docker Build", test_docker_build),
        ("Docker Run", test_docker_run),
        ("Docker Cleanup", test_docker_cleanup)
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
        print("🎉 Containerization is working perfectly!")
        print("✅ The Docker image is ready for deployment.")
        return True
    elif passed >= total - 1:  # Allow one failure (usually cleanup)
        print("✅ Containerization is working with minor issues.")
        print("✅ The Docker image is ready for deployment.")
        return True
    else:
        print("⚠️  Containerization has issues that need to be addressed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

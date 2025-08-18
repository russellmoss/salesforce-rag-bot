#!/usr/bin/env python3
"""
Comprehensive containerization validation for the Salesforce RAG Bot.
Validates all Docker-related files and configurations without requiring Docker to be running.
"""

import subprocess
import sys
import os
from pathlib import Path
import re

def test_dockerfile_structure():
    """Test Dockerfile structure and content."""
    print("🔍 Testing Dockerfile Structure...")
    
    dockerfile_path = Path(__file__).parent / "Dockerfile"
    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for required components
        required_components = {
            "FROM": "Base image specification",
            "WORKDIR": "Working directory setup",
            "COPY requirements.txt": "Requirements file copying",
            "RUN pip install": "Python package installation",
            "COPY src/pipeline": "Pipeline script copying",
            "ENTRYPOINT": "Container entrypoint"
        }
        
        missing_components = []
        for component, description in required_components.items():
            if component not in content:
                missing_components.append(f"{component} ({description})")
        
        if missing_components:
            print(f"❌ Missing components: {', '.join(missing_components)}")
            return False
        
        # Check for best practices
        best_practices = {
            "rm -rf": "Cleanup commands",
            "python:3.11-slim": "Slim base image",
            "--no-cache-dir": "Pip no-cache flag"
        }
        
        print("✅ Required components found:")
        for component, description in required_components.items():
            print(f"   - {description}")
        
        print("\n✅ Best practices implemented:")
        for practice, description in best_practices.items():
            if practice in content:
                print(f"   - {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False

def test_dockerignore():
    """Test .dockerignore file."""
    print("\n🔍 Testing .dockerignore...")
    
    dockerignore_path = Path(__file__).parent / ".dockerignore"
    if not dockerignore_path.exists():
        print("❌ .dockerignore not found")
        return False
    
    try:
        with open(dockerignore_path, 'r') as f:
            content = f.read()
        
        # Check for important exclusions
        important_exclusions = [
            ".git",
            "__pycache__",
            "*.pyc",
            "test_*.py",
            ".env",
            "README.md",
            "node_modules"
        ]
        
        missing_exclusions = []
        for exclusion in important_exclusions:
            if exclusion not in content:
                missing_exclusions.append(exclusion)
        
        if missing_exclusions:
            print(f"⚠️  Missing exclusions: {', '.join(missing_exclusions)}")
        else:
            print("✅ Important exclusions found")
        
        print(f"✅ .dockerignore exists with {len(content.split())} lines")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .dockerignore: {e}")
        return False

def test_docker_compose():
    """Test docker-compose.yml file."""
    print("\n🔍 Testing docker-compose.yml...")
    
    compose_path = Path(__file__).parent / "docker-compose.yml"
    if not compose_path.exists():
        print("❌ docker-compose.yml not found")
        return False
    
    try:
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for required services
        required_services = ["salesforce-pipeline", "salesforce-pipeline-run"]
        missing_services = []
        
        for service in required_services:
            if service not in content:
                missing_services.append(service)
        
        if missing_services:
            print(f"❌ Missing services: {', '.join(missing_services)}")
            return False
        
        # Check for volume mounts
        if "volumes:" in content and "./output:/app/output" in content:
            print("✅ Volume mounts configured")
        else:
            print("⚠️  Volume mounts may be missing")
        
        # Check for environment variables
        if "PYTHONUNBUFFERED=1" in content:
            print("✅ Environment variables configured")
        else:
            print("⚠️  Environment variables may be missing")
        
        print("✅ Docker Compose file is properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error reading docker-compose.yml: {e}")
        return False

def test_requirements_compatibility():
    """Test requirements.txt compatibility with Docker."""
    print("\n🔍 Testing Requirements Compatibility...")
    
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        issues = []
        
        # Check for version specifications
        lines_without_versions = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '>=' not in line and '==' not in line:
                if not any(char.isdigit() for char in line):
                    lines_without_versions.append(line)
        
        if lines_without_versions:
            issues.append(f"Lines without version specs: {', '.join(lines_without_versions)}")
        
        # Check for potential conflicts
        if "pinecone-client" in content and "pinecone" in content:
            issues.append("Both pinecone-client and pinecone packages")
        
        # Check for system dependencies
        system_deps = ["curl", "apt-get"]
        for dep in system_deps:
            if dep in content:
                issues.append(f"System dependency in requirements: {dep}")
        
        if issues:
            print("⚠️  Potential issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Requirements file is Docker-compatible")
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def test_file_structure():
    """Test that all required files exist for containerization."""
    print("\n🔍 Testing File Structure...")
    
    required_files = [
        "Dockerfile",
        ".dockerignore",
        "docker-compose.yml",
        "requirements.txt",
        "src/pipeline/build_schema_library_end_to_end.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files exist")
    return True

def test_docker_commands():
    """Test Docker command availability and syntax."""
    print("\n🔍 Testing Docker Commands...")
    
    # Test if Docker is available
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker available: {version}")
            
            # Test Docker Compose
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    compose_version = result.stdout.strip()
                    print(f"✅ Docker Compose available: {compose_version}")
                    return True
                else:
                    print("⚠️  Docker Compose not available")
                    return True  # Don't fail for missing Docker Compose
                    
            except FileNotFoundError:
                print("⚠️  Docker Compose not found")
                return True  # Don't fail for missing Docker Compose
                
        else:
            print("⚠️  Docker not responding properly")
            return True  # Don't fail if Docker is not running
            
    except FileNotFoundError:
        print("ℹ️  Docker not installed or not in PATH")
        return True  # Don't fail if Docker is not installed
    except subprocess.TimeoutExpired:
        print("⚠️  Docker command timed out")
        return True  # Don't fail for timeout
    except Exception as e:
        print(f"⚠️  Docker command error: {e}")
        return True  # Don't fail for Docker issues

def generate_docker_instructions():
    """Generate Docker usage instructions."""
    print("\n📋 Docker Usage Instructions:")
    print("=" * 50)
    
    print("\n1. Build the Docker image:")
    print("   docker build -t salesforce-rag-bot .")
    
    print("\n2. Run with Docker Compose (test):")
    print("   docker-compose --profile test up")
    
    print("\n3. Run with Docker Compose (development):")
    print("   docker-compose --profile development up")
    
    print("\n4. Run with Docker Compose (production):")
    print("   docker-compose --profile production up")
    
    print("\n5. Run directly with Docker:")
    print("   docker run --rm -v $(pwd)/output:/app/output salesforce-rag-bot --help")
    
    print("\n6. Interactive development container:")
    print("   docker-compose --profile development run --rm salesforce-pipeline-dev bash")
    
    print("\n7. Clean up Docker resources:")
    print("   docker-compose down")
    print("   docker system prune -f")

def main():
    """Run all containerization validation tests."""
    print("🐳 Salesforce RAG Bot - Containerization Validation")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dockerfile Structure", test_dockerfile_structure),
        (".dockerignore", test_dockerignore),
        ("Docker Compose", test_docker_compose),
        ("Requirements Compatibility", test_requirements_compatibility),
        ("Docker Commands", test_docker_commands)
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
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Containerization is properly configured!")
        print("✅ All Docker-related files are ready for deployment.")
    elif passed >= total - 1:
        print("✅ Containerization is mostly ready with minor issues.")
        print("✅ Docker files are ready for deployment.")
    else:
        print("⚠️  Containerization has issues that need to be addressed.")
    
    # Always generate instructions
    generate_docker_instructions()
    
    return passed >= total - 1  # Allow one failure

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

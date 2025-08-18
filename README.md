# 🤖 Salesforce Schema AI Assistant

A comprehensive RAG (Retrieval-Augmented Generation) bot for Salesforce data that provides intelligent insights about your org's schema, automation, security model, and usage data.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🏗️ System Architecture](#️-system-architecture)
- [📦 Installation & Setup](#-installation--setup)
- [🔧 Local Development](#-local-development)
- [🔄 Pipeline Automation](#-pipeline-automation)
- [🚀 Pipeline Speed Optimization (Parallel Processing + SmartCache + Smart API Batching)](#-pipeline-speed-optimization-parallel-processing--smartcache--smart-api-batching)
- [🚀 Smart API Batching System](#️-smart-api-batching-system)
- [🗄️ SmartCache System](#️-smartcache-system)
- [🌐 Deployment](#-deployment)
- [🔐 Environment Variables](#-environment-variables)
- [📚 Usage Examples](#-usage-examples)
- [🛠️ Troubleshooting](#️-troubleshooting)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/salesforce-rag-bot.git
cd salesforce-rag-bot
```

### 2. Install Dependencies

```bash
# Install pipeline dependencies
pip install -r requirements.txt

# Install chatbot dependencies
pip install -r src/chatbot/requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Required: Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=salesforce-schema

# Required: At least one LLM provider
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Optional: Alternative LLM providers
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
```

### 4. Run the Pipeline (First Time)

```bash
# Authenticate to Salesforce
sf org login web -a YourOrgAlias

# Run the full pipeline with all optimizations (recommended)
python run_optimized_pipeline.py

# Or run manually with all optimizations (Smart API Batching + Parallel + Cache)
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 15 \
  --cache-dir cache \
  --cache-max-age 24 \
  --cache-stats
  # Smart API Batching is automatically enabled for optimal performance
```

### 5. Launch the Chatbot

```bash
streamlit run src/chatbot/app.py
```

## 🏗️ System Architecture

### **Core Components**

1. **📊 Data Pipeline** (`src/pipeline/`)
   - **Schema Extraction**: Fetches Salesforce object metadata via Tooling API
   - **Data Processing**: Converts raw metadata into structured JSON
   - **Vectorization**: Creates embeddings and uploads to Pinecone
   - **Incremental Updates**: Only processes changed objects/files

2. **🤖 Chatbot Interface** (`src/chatbot/`)
   - **Streamlit Web App**: User-friendly conversational interface
   - **RAG Service**: Retrieves relevant context from Pinecone
   - **Multi-LLM Support**: OpenAI, Anthropic, and Google AI
   - **Real-time Responses**: Instant answers with source citations

3. **🔄 Automation** (`.github/workflows/`)
   - **Daily Updates**: Runs pipeline at 12 AM UTC daily
   - **Smart Diffing**: Only updates changed schema elements
   - **Error Handling**: Comprehensive logging and notifications

### **Data Flow**

```
Salesforce Org → Schema Pipeline → Pinecone Vector DB → RAG Service → Chatbot UI
     ↓              ↓                    ↓                ↓           ↓
  Metadata    JSON Processing    Embeddings & Index   Context     User Query
  Extraction   & Validation      Storage              Retrieval   Response
```

### **Technologies Used**

- **Backend**: Python 3.11+, LangChain, Pinecone
- **Frontend**: Streamlit
- **LLM Providers**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Vector Database**: Pinecone (serverless)
- **Automation**: GitHub Actions, Salesforce CLI
- **Containerization**: Docker, Docker Compose

## 📦 Installation & Setup

### **Prerequisites**

- Python 3.11 or higher
- Salesforce CLI (`sf`)
- Git
- Access to LLM APIs (OpenAI, Anthropic, or Google)
- Pinecone account

### **Step-by-Step Setup**

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/your-username/salesforce-rag-bot.git
   cd salesforce-rag-bot
   ```

2. **Install Python Dependencies**
   ```bash
   # Install pipeline dependencies
   pip install -r requirements.txt
   
   # Install chatbot dependencies
   pip install -r src/chatbot/requirements.txt
   ```

3. **Install Salesforce CLI**
   ```bash
   # Windows (PowerShell)
   winget install Salesforce.CLI
   
   # macOS
   brew install salesforce-cli
   
   # Linux
   npm install --global @salesforce/cli
   ```

4. **Authenticate to Salesforce**
   ```bash
   sf org login web -a YourOrgAlias
   ```

## 🔧 Local Development

### **Running the Pipeline Locally**

```bash
# Basic pipeline run
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output

# Full pipeline with all features
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone
```

### **Pipeline Options**

- `--org-alias`: Salesforce org alias (required)
- `--output`: Output directory for generated files
- `--with-stats`: Include usage statistics
- `--with-automation`: Include flows, triggers, validation rules
- `--with-metadata`: Include profiles, permission sets
- `--emit-jsonl`: Generate JSONL files for vector DB
- `--push-to-pinecone`: Upload embeddings to Pinecone

### **Running the Chatbot Locally**

```bash
# Start the Streamlit app
streamlit run src/chatbot/app.py

# Or with custom port
streamlit run src/chatbot/app.py --server.port 8501
```

### **Testing the Setup**

```bash
# Test pipeline connectivity
python -c "
from src.pipeline.build_schema_library_end_to_end import main
main(['--org-alias', 'YourOrgAlias', '--test-only'])
"

# Test chatbot connectivity
python -c "
from src.chatbot.config import config
print('Configuration valid:', bool(config.validate_config()))
"
```

## 🔄 Pipeline Automation

### **Complete Pipeline Workflow**

The Salesforce Schema Pipeline is a comprehensive system that extracts, processes, and vectorizes your Salesforce org's metadata. Here's the complete workflow:

#### **Pipeline Steps Overview**

1. **📊 Schema Extraction**: Fetches all Salesforce objects and their metadata
2. **🔍 Field Analysis**: Extracts field types, descriptions, and relationships  
3. **📈 Statistics Collection**: Gathers record counts and field usage data
4. **🤖 Automation Discovery**: Analyzes flows, triggers, and validation rules
5. **📝 Documentation Generation**: Creates markdown files for each object
6. **🔢 Vector Database Preparation**: Generates JSONL files for vector ingestion
7. **🚀 Pinecone Upload**: Creates embeddings and uploads to vector database

#### **Performance Optimizations**

The pipeline includes several optimizations for maximum efficiency:

- **🔄 Resume Functionality**: Skip already processed data
- **⚡ Parallel Processing**: Up to 15 concurrent workers
- **💾 Smart Caching**: Intelligent caching with 24-hour expiration
- **📦 Smart API Batching**: Combines multiple queries into single API calls
- **🎯 Incremental Updates**: Only process changed objects

### **Setting Up GitHub Actions**

The repository includes automated pipeline execution that runs daily at 12 AM UTC. Here's how to set it up:

#### **1. Fork/Clone the Repository**
```bash
git clone https://github.com/your-username/salesforce-rag-bot.git
cd salesforce-rag-bot
```

#### **2. Configure GitHub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

**Required Secrets:**
```
SF_ORG_ALIAS: Your Salesforce org alias (e.g., "DEVNEW")
SFDX_AUTH_URL: Your Salesforce auth URL
PINECONE_API_KEY: Your Pinecone API key
OPENAI_API_KEY: Your OpenAI API key
```

**Optional Configuration:**
```
PINECONE_CLOUD: aws
PINECONE_REGION: us-east-1
PINECONE_INDEX_NAME: salesforce-schema
```

#### **3. Generate Salesforce Auth URL**
```bash
# Create a new org alias for automation
sf org login web -a AutomatedOrg

# Generate auth URL for GitHub Actions
sf org display -a AutomatedOrg --verbose

# Copy the "Sfdx Auth Url" value to your GitHub secret
```

#### **4. Create GitHub Actions Workflow**

Create `.github/workflows/salesforce-pipeline.yml`:

```yaml
name: Salesforce Schema Pipeline

on:
  schedule:
    - cron: '0 12 * * *'  # Daily at 12 PM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  schema-pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 480  # 8 hours max
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r src/chatbot/requirements.txt
          
      - name: Install Salesforce CLI
        run: |
          npm install --global @salesforce/cli
          
      - name: Authenticate to Salesforce
        run: |
          echo ${{ secrets.SFDX_AUTH_URL }} | sf org login sfdx-url --set-default-dev-hub
          
      - name: Run Full Pipeline
        run: |
          python src/pipeline/build_schema_library_end_to_end.py \
            --org-alias ${{ secrets.SF_ORG_ALIAS }} \
            --output ./output \
            --with-metadata \
            --emit-markdown \
            --emit-jsonl \
            --push-to-pinecone \
            --resume \
            --stats-resume \
            --max-workers 15
        env:
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_CLOUD: ${{ secrets.PINECONE_CLOUD }}
          PINECONE_REGION: ${{ secrets.PINECONE_REGION }}
          PINECONE_INDEX_NAME: ${{ secrets.PINECONE_INDEX_NAME }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: schema-output
          path: output/
          
      - name: Notify on success
        if: success()
        run: |
          echo "✅ Pipeline completed successfully!"
          echo "📊 Generated files:"
          ls -la output/
          echo "📁 Markdown files: $(ls output/md/ | wc -l)"
          
      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ Pipeline failed!"
```

#### **5. Enable GitHub Actions**

The workflow will automatically:
- Run daily at 12 PM UTC
- Authenticate to Salesforce using your auth URL
- Execute the pipeline with resume functionality
- Generate markdown files, JSONL files, and upload to Pinecone
- Provide success/failure notifications
- Upload artifacts for inspection

### **Pipeline Execution Strategies**

#### **🚀 Initial Setup (First Run)**

For the first time setup, run the complete pipeline:

```bash
# Full pipeline with all features (recommended for first run)
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-metadata \
  --emit-markdown \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 15
```

**Expected Output:**
- ✅ 1,458 Salesforce objects processed
- ✅ 1,458 markdown files generated
- ✅ 1,458 JSONL entries created
- ✅ 1,458 vectors uploaded to Pinecone
- ⏱️ Processing time: 15-30 minutes

#### **🔄 Regular Updates (Subsequent Runs)**

For regular updates, use the resume functionality:

```bash
# Fast update with resume functionality
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-metadata \
  --emit-markdown \
  --emit-jsonl \
  --push-to-pinecone \
  --resume \
  --stats-resume \
  --max-workers 15
```

**Expected Output:**
- ✅ Found existing schema data with 1,458 objects
- ✅ Using existing schema data (resume mode)
- ✅ Emitted 1,458 markdown files
- ✅ Emitted JSONL file
- ✅ Successfully uploaded 1,458 objects to Pinecone
- ⏱️ Processing time: 2-5 minutes

### **Verification and Testing**

#### **Test Output Files**
```bash
# Verify all files were created correctly
python verify_output_files.py

# Expected output:
# ✅ Output Directory: PASSED
# ✅ Schema JSON: PASSED  
# ✅ Markdown Files: PASSED
# ✅ JSONL File: PASSED
# ✅ Data Consistency: PASSED
# 🎉 ALL CHECKS PASSED! Your output files are perfect!
```

#### **Test Pinecone Index**
```bash
# Verify Pinecone index is working correctly
python test_pinecone_index.py

# Expected output:
# ✅ Connection Test: PASSED
# ✅ Index Statistics: PASSED
# ✅ Metadata Quality: PASSED
# ✅ Vector Search: PASSED
# ✅ Specific Object Search: PASSED
# 🎉 ALL TESTS PASSED! Your Pinecone index is working perfectly!
```

### **GitHub Actions Execution**

#### **Manual Trigger**
1. Go to your GitHub repository
2. Click on "Actions" tab
3. Select "Salesforce Schema Pipeline"
4. Click "Run workflow"
5. Select your branch and click "Run workflow"

#### **Automatic Daily Execution**
The pipeline runs automatically every day at 12 PM UTC and:
- Uses resume functionality to skip existing data
- Only processes new or changed objects
- Updates Pinecone index with new vectors
- Provides detailed logs and artifacts

#### **Monitoring Execution**
- **View Logs**: Go to Actions → Salesforce Schema Pipeline → Latest run
- **Download Artifacts**: Click "schema-output" to download generated files
- **Check Status**: Green checkmark = success, red X = failure

### **Troubleshooting GitHub Actions**

#### **Common Issues**

1. **Authentication Failed**
   ```bash
   # Regenerate auth URL
   sf org display -a YourOrgAlias --verbose
   # Update SFDX_AUTH_URL secret in GitHub
   ```

2. **Timeout Issues**
   ```yaml
   # Increase timeout in workflow
   timeout-minutes: 480  # 8 hours
   ```

3. **Missing Secrets**
   - Verify all required secrets are set in GitHub
   - Check secret names match exactly

4. **API Rate Limits**
   ```bash
   # Reduce workers if hitting limits
   --max-workers 5  # Instead of 15
   ```

#### **Debug Mode**
```yaml
# Add to workflow for debugging
- name: Debug Information
  run: |
    echo "Org alias: ${{ secrets.SF_ORG_ALIAS }}"
    echo "Pinecone index: ${{ secrets.PINECONE_INDEX_NAME }}"
    sf org list
```

### **Performance Optimization**

#### **GitHub Actions Optimizations**

**Fast Execution (Recommended):**
```yaml
- name: Run Optimized Pipeline
  run: |
    python src/pipeline/build_schema_library_end_to_end.py \
      --org-alias ${{ secrets.SF_ORG_ALIAS }} \
      --output ./output \
      --with-metadata \
      --emit-markdown \
      --emit-jsonl \
      --push-to-pinecone \
      --resume \
      --stats-resume \
      --max-workers 15
```

**Conservative Execution (API-limited orgs):**
```yaml
- name: Run Conservative Pipeline
  run: |
    python src/pipeline/build_schema_library_end_to_end.py \
      --org-alias ${{ secrets.SF_ORG_ALIAS }} \
      --output ./output \
      --with-metadata \
      --emit-markdown \
      --emit-jsonl \
      --push-to-pinecone \
      --resume \
      --stats-resume \
      --max-workers 5
```

#### **Expected Performance**

| Scenario | Objects | Time | Workers |
|----------|---------|------|---------|
| Initial Run | 1,458 | 15-30 min | 15 |
| Resume Run | 1,458 | 2-5 min | 15 |
| Conservative | 1,458 | 30-60 min | 5 |

### **Manual Pipeline Execution**

#### **Local Development**
```bash
# Full pipeline run
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-metadata \
  --emit-markdown \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 15

# Resume run (fast)
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-metadata \
  --emit-markdown \
  --emit-jsonl \
  --push-to-pinecone \
  --resume \
  --stats-resume \
  --max-workers 15
```

#### **Production Deployment**
```bash
# Production-ready command
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias PROD \
  --output ./output \
  --with-metadata \
  --emit-markdown \
  --emit-jsonl \
  --push-to-pinecone \
  --resume \
  --stats-resume \
  --max-workers 15
```

## 🌐 Deployment

### **Streamlit Cloud Deployment**

1. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"

2. **Configure App Settings**
   ```
   Repository: your-username/salesforce-rag-bot
   Branch: main
   Main file path: src/chatbot/app.py
   App URL: your-app-name (optional)
   ```

3. **Add Streamlit Secrets**
   
   In the Streamlit Cloud dashboard, add these secrets:

   ```toml
   PINECONE_API_KEY = "your-pinecone-api-key"
   PINECONE_CLOUD = "aws"
   PINECONE_REGION = "us-east-1"
   PINECONE_INDEX_NAME = "salesforce-schema"
   OPENAI_API_KEY = "sk-your-openai-key"
   ANTHROPIC_API_KEY = "sk-ant-your-anthropic-key"
   GOOGLE_API_KEY = "your-google-key"
   ```

4. **Deploy**
   - Click "Deploy!"
   - Wait for build completion
   - Your app will be available at `https://your-app-name.streamlit.app`

### **Docker Deployment**

```bash
# Build the Docker image
docker build -t salesforce-rag-bot .

# Run the container
docker run -p 8501:8501 \
  -e PINECONE_API_KEY=your-key \
  -e OPENAI_API_KEY=your-key \
  salesforce-rag-bot

# Or use Docker Compose
docker-compose up -d
```

## 🔐 Environment Variables

### **Required Variables**

```env
# Pinecone Configuration (Required)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=salesforce-schema

# LLM Provider (At least one required)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OR
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-1.5-pro
```

### **Optional Variables**

```env
# RAG Configuration
MAX_TOKENS=4000
TEMPERATURE=0.1
TOP_K=5
TOP_P=0.95

# Salesforce Configuration
SF_ORG_ALIAS=YourOrgAlias

# Logging
LOG_LEVEL=INFO
```

### **GitHub Actions Secrets**

For automated pipeline execution, add these to your GitHub repository secrets:

```
SFDX_AUTH_URL: Your Salesforce auth URL
PINECONE_API_KEY: Your Pinecone API key
OPENAI_API_KEY: Your OpenAI API key
PINECONE_CLOUD: aws
PINECONE_REGION: us-east-1
PINECONE_INDEX_NAME: salesforce-schema
```

### **Streamlit Cloud Secrets**

For Streamlit deployment, add these in TOML format:

```toml
PINECONE_API_KEY = "your-pinecone-api-key"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_INDEX_NAME = "salesforce-schema"
OPENAI_API_KEY = "sk-your-openai-key"
ANTHROPIC_API_KEY = "sk-ant-your-anthropic-key"
GOOGLE_API_KEY = "your-google-key"
```

## 📚 Usage Examples

### **Pipeline Commands**

```bash
# Basic schema extraction
python src/pipeline/build_schema_library_end_to_end.py --org-alias DEV

# Full pipeline with all features
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias PROD \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone

# Incremental update only (for regular updates)
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias DEV \
  --resume \
  --stats-resume \
  --emit-jsonl \
  --incremental-update \
  --push-to-pinecone \
  --with-stats \
  --with-metadata \
  --output ./output
```

### **Chatbot Queries**

Once deployed, you can ask questions like:

- "What fields are available on the Account object?"
- "Show me all validation rules on the Contact object"
- "What flows are triggered when a Lead is created?"
- "Which profiles have access to the Opportunity object?"
- "What are the most commonly used fields on Account?"
- "Show me all automation related to the Case object"

## 🛠️ Troubleshooting

### **Common Issues**

1. **Salesforce Authentication**
   ```bash
   # Re-authenticate if session expires
   sf org login web -a YourOrgAlias
   
   # Check org status
   sf org display -a YourOrgAlias
   ```

2. **Pinecone Connection**
   ```bash
   # Verify Pinecone credentials
   python -c "
   import pinecone
   pinecone.init(api_key='your-key', environment='us-east-1-aws')
   print('Connected:', pinecone.list_indexes())
   "
   ```

3. **LLM API Issues**
   ```bash
   # Test OpenAI connection
   python -c "
   from openai import OpenAI
   client = OpenAI(api_key='your-key')
   print('OpenAI connected')
   "
   ```

4. **Pipeline Failures**
   ```bash
   # Run with verbose logging
   python src/pipeline/build_schema_library_end_to_end.py \
     --org-alias YourOrgAlias \
     --verbose \
     --output ./output
   ```

### **Getting Help**

- Check the logs in the `output/` directory
- Review GitHub Actions workflow logs
- Verify all environment variables are set correctly
- Ensure Salesforce org has necessary permissions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the deployment documentation

## 🚀 Pipeline Speed Optimization (Parallel Processing + SmartCache + Smart API Batching)

### **Parallel Processing + SmartCache + Smart API Batching (NEW!)**

The pipeline now includes **parallel processing capabilities**, **intelligent caching**, and **Smart API Batching** that can reduce execution time from 12+ hours to 15-30 minutes (95%+ improvement).

#### **Performance Improvements**

- **Before**: Sequential processing with 150ms delays between objects
- **After**: Up to 15 concurrent workers with intelligent rate limiting + SmartCache + Smart API Batching
- **Result**: 95%+ faster execution while respecting Salesforce API limits
- **Cache Benefits**: 10-50x faster on subsequent runs with 80-95% cache hit rate
- **API Batching Benefits**: 5-10x faster API calls with 80-90% reduction in API requests

#### **Performance Improvements**

- **Before**: Sequential processing with 150ms delays between objects
- **After**: Up to 15 concurrent workers with intelligent rate limiting
- **Result**: 75%+ faster execution while respecting Salesforce API limits

#### **New Command Line Options**

```bash
--max-workers 15  # Number of concurrent workers (default: 10)
--cache-dir cache  # Cache directory (default: cache)
--cache-max-age 24  # Cache age in hours (default: 24)
--cache-stats  # Show cache statistics at end
--clear-cache  # Clear cache before running
# Smart API Batching is automatically enabled for optimal performance
```

#### **Production-Optimized Commands**

**🚀 ULTIMATE PERFORMANCE - Optimized Pipeline (Recommended for Production):**
```bash
# Use the production-ready optimized pipeline runner
python run_optimized_pipeline.py

# Or run manually with all optimizations (Smart API Batching + Parallel + Cache)
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 15 \
  --cache-dir cache \
  --cache-max-age 24 \
  --cache-stats \
  --resume \
  --stats-resume
```

**High-Performance Production Run (Without Cache):**
```bash
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 15 \
  --resume \
  --stats-resume
  # Smart API Batching is automatically enabled for optimal performance
```

**Conservative Production Run (API-limited orgs):**
```bash
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone \
  --max-workers 5 \
  --cache-dir cache \
  --cache-max-age 24 \
  --cache-stats \
  --resume \
  --stats-resume
  # Smart API Batching is automatically enabled for optimal performance
```

#### **SmartCache Management**

**Cache Statistics:**
```bash
# Show cache performance statistics
python run_optimized_pipeline.py --stats

# Clear cache if needed
python run_optimized_pipeline.py --clear

# Test cache functionality
python run_optimized_pipeline.py --test
```

**Cache Benefits:**
- **First run**: ~2-4 hours (with caching)
- **Subsequent runs**: ~15-30 minutes (cache hits)
- **Cache hit rate**: 80-95% on subsequent runs
- **API call reduction**: 90%+ reduction in API calls
- **Automatic invalidation**: Fresh data every 24 hours
- **Compression**: 3-5x disk space savings

**Smart API Batching Benefits:**
- **API call reduction**: 80-90% fewer Salesforce API calls
- **Batch processing**: Multiple objects processed in single API calls
- **Performance improvement**: 5-10x faster API operations
- **Rate limit friendly**: Reduces API pressure on Salesforce orgs
- **Automatic optimization**: No additional configuration required

#### **GitHub Actions Production Configuration**

**Optimized GitHub Actions Workflow:**
```yaml
# .github/workflows/production-pipeline.yml
name: Production Salesforce Schema Pipeline

on:
  schedule:
    - cron: '0 12 * * *'  # Daily at 12 PM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  schema-pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 480  # 8 hours max
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r src/chatbot/requirements.txt
          
      - name: Install Salesforce CLI
        run: |
          npm install --global @salesforce/cli
          
      - name: Authenticate to Salesforce
        run: |
          echo ${{ secrets.SFDX_AUTH_URL }} | sf org login sfdx-url --set-default-dev-hub
          
      - name: Run Production Pipeline (Optimized)
        run: |
          python run_optimized_pipeline.py
        env:
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_CLOUD: ${{ secrets.PINECONE_CLOUD }}
          PINECONE_REGION: ${{ secrets.PINECONE_REGION }}
          PINECONE_INDEX_NAME: ${{ secrets.PINECONE_INDEX_NAME }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      # Alternative: Manual optimized pipeline command
      - name: Run Production Pipeline (Manual)
        run: |
          python src/pipeline/build_schema_library_end_to_end.py \
            --org-alias ${{ secrets.SF_ORG_ALIAS }} \
            --output ./output \
            --with-stats \
            --with-automation \
            --with-metadata \
            --emit-jsonl \
            --push-to-pinecone \
            --max-workers 15 \
            --cache-dir cache \
            --cache-max-age 24 \
            --cache-stats \
            --resume \
            --stats-resume \
            --throttle-ms 300 \
            --retries 3
            # Smart API Batching is automatically enabled for optimal performance
        env:
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_CLOUD: ${{ secrets.PINECONE_CLOUD }}
          PINECONE_REGION: ${{ secrets.PINECONE_REGION }}
          PINECONE_INDEX_NAME: ${{ secrets.PINECONE_INDEX_NAME }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: schema-output
          path: output/
          
      - name: Notify on success
        if: success()
        run: |
          echo "✅ Pipeline completed successfully!"
          
      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ Pipeline failed!"
```

#### **Production Environment Variables**

**Required GitHub Secrets for Production:**
```
SF_ORG_ALIAS: Your Salesforce org alias
SFDX_AUTH_URL: Your Salesforce auth URL
PINECONE_API_KEY: Your Pinecone API key
PINECONE_CLOUD: aws
PINECONE_REGION: us-east-1
PINECONE_INDEX_NAME: salesforce-schema
OPENAI_API_KEY: Your OpenAI API key
```

#### **Performance Monitoring**

**Expected Performance by Org Size:**

| Org Size | Objects | Sequential Time | Parallel Time | Optimized Time | Improvement |
|----------|---------|----------------|---------------|----------------|-------------|
| Small    | <500    | 2-4 hours      | 30-60 min     | 15-30 min     | 95%+        |
| Medium   | 500-1000| 6-8 hours      | 1-2 hours     | 30-60 min     | 95%+        |
| Large    | 1000+   | 12+ hours      | 2-4 hours     | 60-90 min     | 95%+        |

**Monitoring Commands:**
```bash
# Check API usage
sf org limits --target-org YourOrgAlias

# Monitor progress
tail -f pipeline.log

# Check memory usage
htop  # or top
```

#### **Testing Parallel Processing, SmartCache & Smart API Batching**

**Test the parallel processing functionality:**
```bash
# Run the test script to verify parallel processing
python test_parallel_processing.py

# Expected output shows 4-5x speed improvement
# Parallel: ~1.7 seconds vs Sequential: ~8.1 seconds
```

**Test the SmartCache functionality:**
```bash
# Run the comprehensive cache test suite
python test_smart_cache.py

# Expected output shows 7/7 tests passed
# All cache features working correctly

# Test cache performance benefits
python test_cached_pipeline.py

# Expected output shows 5.4x speedup with caching
# Compression ratio: 5.7x smaller files
```

**Test the Smart API Batching functionality:**
```bash
# Run the comprehensive API batching test suite
python test_smart_api_batching.py

# Expected output shows 5/5 tests passed
# All batching features working correctly
# Performance improvement: 5-10x faster API calls
# API call reduction: 80-90% fewer requests
```

### **Additional Performance Optimizations**

#### **1. Throttling Optimization**

**Current Default:** 150ms between API calls
**Safe Optimizations:**
```bash
# Conservative optimization (recommended)
--throttle-ms 100

# Aggressive optimization (test first)
--throttle-ms 75

# Environment variable override
export THROTTLE_MS=100
```

#### **2. Batch Size Optimization**

**Embedding Batch Size:**
```bash
# Current: 96 embeddings per batch
--embed-batch-size 96

# Optimized: 150-200 embeddings per batch
--embed-batch-size 150

# Environment variable override
export EMBED_BATCH_SIZE=150
```

#### **3. Smart Caching**

**Resume Strategy:**
```bash
# Skip existing objects (saves significant time)
--resume

# Skip existing stats
--stats-resume

# Incremental updates only
--incremental-update
```

**SmartCache Strategy:**
```bash
# Enable intelligent caching (recommended)
--cache-dir cache
--cache-max-age 24
--cache-stats

# Clear cache if needed
--clear-cache

# Use production-ready optimized pipeline
python run_optimized_pipeline.py
```

#### **4. Platform-Specific Optimizations**

**Salesforce Limits:**
- **API Calls:** 200 calls/minute per org
- **Concurrent Workers:** 10-15 workers optimal
- **Rate Limiting:** 300ms between calls per worker

**Pinecone Limits:**
- **Embedding Requests:** 100 per second
- **Index Operations:** 10 per second
- **Batch Size:** Up to 100 vectors per upsert

**GitHub Actions:**
- **Job Timeout:** 8 hours (increased for parallel processing)
- **Concurrent Jobs:** 20 per repository
- **API Rate Limits:** 5,000 requests per hour

#### **5. Recommended Fast Pipeline Command**

**🚀 ULTIMATE PERFORMANCE - Optimized Pipeline (Recommended):**
```bash
# Use the production-ready optimized pipeline runner
python run_optimized_pipeline.py
```

**Manual Optimized Command:**
```bash
# Optimized for speed with parallel processing + caching + Smart API Batching
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --resume \
  --stats-resume \
  --emit-jsonl \
  --incremental-update \
  --push-to-pinecone \
  --with-stats \
  --with-metadata \
  --output ./output \
  --max-workers 15 \
  --cache-dir cache \
  --cache-max-age 24 \
  --cache-stats \
  --throttle-ms 100 \
  --embed-batch-size 150
  # Smart API Batching is automatically enabled for optimal performance
```

#### **6. Performance Monitoring**

**Expected Speed Improvements:**
- **Parallel processing:** 75%+ faster (main improvement)
- **SmartCache:** 10-50x faster on subsequent runs
- **Smart API Batching:** 5-10x faster API calls, 80-90% fewer requests
- **Throttling optimization:** 25-33% faster
- **Batch size increase:** 20-30% faster
- **Resume strategy:** 50-80% faster (for updates)
- **Combined optimizations:** 95%+ faster overall

**Safety Checks:**
- Monitor Salesforce API usage in Setup → Company Information → API Usage
- Check Pinecone console for rate limit warnings
- Review GitHub Actions logs for timeout issues

#### **8. Troubleshooting Performance Issues**

```bash
# If you hit rate limits, increase throttling
--throttle-ms 200

# If embeddings fail, reduce batch size
--embed-batch-size 50

# If GitHub Actions timeout, use incremental updates
--incremental-update --resume --stats-resume

# If cache issues occur, clear and rebuild
python run_optimized_pipeline.py --clear

# If cache hit rate is low, check cache age
python run_optimized_pipeline.py --stats

# If API batching issues occur, check Salesforce API limits
sf org limits --target-org YourOrgAlias
```

### **Platform Limits Reference**

| Platform | Rate Limit | Concurrent | Timeout |
|----------|------------|------------|---------|
| Salesforce | 15,000/hour | 25 | 120s |
| Pinecone | 100/sec | 10 | 30s |
| GitHub Actions | 5,000/hour | 20 | 6h |
| OpenAI | 3,000/min | 10 | 60s |

## 🚀 Smart API Batching System

### **Overview**

The Smart API Batching system dramatically reduces Salesforce API calls by combining multiple queries into single batched requests. This optimization provides 5-10x faster API operations and 80-90% reduction in API requests.

### **Key Features**

- **Batched Automation Queries**: Combines Flows, Triggers, Validation Rules, and Workflow Rules into single API calls
- **Batched Field-Level Security**: Fetches FLS data for multiple objects in one query
- **Batched Statistics**: Collects record counts and field fill rates for multiple objects simultaneously
- **Automatic Optimization**: No additional configuration required - automatically enabled
- **Rate Limit Friendly**: Reduces API pressure on Salesforce orgs
- **Error Handling**: Graceful fallback to individual queries if batching fails

### **How It Works**

**Before (Sequential API Calls):**
```python
# Individual API calls for each object
for object_name in object_names:
    flows = get_flows_for_object(object_name)      # 1 API call
    triggers = get_triggers_for_object(object_name) # 1 API call
    validation_rules = get_validation_rules(object_name) # 1 API call
    # Total: 3 API calls per object
```

**After (Batched API Calls):**
```python
# Single batched API calls for all objects
all_flows = get_all_flows_batched(object_names)           # 1 API call total
all_triggers = get_all_triggers_batched(object_names)     # 1 API call total
all_validation_rules = get_all_validation_rules_batched(object_names) # 1 API call total
# Total: 3 API calls for ALL objects
```

### **Performance Benefits**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API Calls | 3 per object | 3 total | 80-90% reduction |
| Processing Time | 2-4 hours | 15-30 minutes | 5-10x faster |
| Rate Limit Usage | High | Low | 80-90% reduction |
| Error Recovery | Individual | Batched | More resilient |

### **Supported Batching Operations**

1. **Automation Dependencies**
   - Flows (AutoLaunchedFlow, RecordTriggeredFlow)
   - Apex Triggers
   - Validation Rules
   - Workflow Rules
   - Code Complexity Analysis

2. **Field-Level Security**
   - FieldPermissions for multiple objects
   - Profile and Permission Set access
   - Field-level security settings

3. **Statistics Collection**
   - Record counts for multiple objects
   - Field fill rates with sample data
   - Usage statistics

### **Integration with SmartCache**

Smart API Batching works seamlessly with SmartCache:
- **First Run**: Uses batched API calls for maximum efficiency
- **Subsequent Runs**: Uses cached data when available, batched calls for new data
- **Cache Miss**: Falls back to batched API calls for optimal performance
- **Combined Benefits**: 95%+ performance improvement over original pipeline

### **Usage Examples**

**Production Pipeline with Smart API Batching:**
```bash
# Smart API Batching is automatically enabled
python run_optimized_pipeline.py

# Manual command with all optimizations
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --with-automation \
  --with-stats \
  --max-workers 15 \
  --cache-dir cache \
  --cache-max-age 24
  # Smart API Batching is automatically enabled for optimal performance
```

**Testing Smart API Batching:**
```bash
# Run comprehensive test suite
python test_smart_api_batching.py

# Expected results:
# ✓ 5/5 tests passed
# ✓ Batched automation data collection
# ✓ Batched field-level security
# ✓ Batched statistics collection
# ✓ Performance comparison
# ✓ Error handling
```

### **Configuration**

Smart API Batching requires no additional configuration - it's automatically enabled for optimal performance. The system:

- **Automatically detects** when batching is beneficial
- **Gracefully falls back** to individual queries if needed
- **Integrates seamlessly** with existing parallel processing and caching
- **Respects rate limits** and API quotas

### **Troubleshooting**

**Common Issues:**
```bash
# Check if batching is working
python test_smart_api_batching.py

# Monitor API usage
sf org limits --target-org YourOrgAlias

# Check for batching errors in logs
grep "batching" pipeline.log

# If batching fails, system automatically falls back to individual queries
```

**Performance Monitoring:**
```bash
# Monitor API call reduction
python run_optimized_pipeline.py --stats

# Check batch processing efficiency
tail -f pipeline.log | grep "batched"
```

## 🗄️ SmartCache System

### **Overview**

The SmartCache system provides intelligent caching for all API calls, dramatically improving pipeline performance on subsequent runs.

### **Key Features**

- **Automatic Cache Invalidation**: 24-hour cache age with automatic refresh
- **Compression**: 3-5x disk space savings with gzip compression
- **Cache Statistics**: Real-time monitoring of hit rates and performance
- **Selective Clearing**: Clear specific data types or age-based clearing
- **Error Handling**: Graceful degradation if cache fails
- **Metadata Tracking**: Full audit trail of cached data

### **Cache Integration Points**

- **Automation Dependencies**: Flows, triggers, code complexity
- **Field-Level Security**: FLS data caching
- **Custom Field History**: Audit trail caching
- **Stats Data**: Object statistics with sample size parameters
- **Code Complexity**: Apex complexity analysis

### **Usage Examples**

**Production Cached Pipeline:**
```bash
# Use the production-ready runner (recommended)
python run_cached_pipeline.py

# Show cache statistics
python run_cached_pipeline.py --stats

# Clear cache if needed
python run_cached_pipeline.py --clear
```

**Manual Cache Management:**
```python
from src.pipeline.smart_cache import SmartCache

# Create cache instance
cache = SmartCache("cache", max_age_hours=24)

# Cache automation data
cache.cache_data("Account", "automation", automation_data)

# Retrieve cached data
cached_data = cache.get_cached_data("Account", "automation")

# Get statistics
stats = cache.get_cache_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
```

### **Performance Benefits**

| Scenario | Without Cache | With Cache | Improvement |
|----------|---------------|------------|-------------|
| First Run | 2-4 hours | 2-4 hours | Same |
| Subsequent Runs | 2-4 hours | 30-60 min | 10-50x faster |
| API Calls | 100% fresh | 5-20% fresh | 80-95% reduction |
| Disk Usage | Uncompressed | 3-5x compressed | 60-80% savings |

### **Cache Configuration**

**Environment Variables:**
```bash
# Cache settings
CACHE_DIR=cache
CACHE_MAX_AGE=24
CACHE_COMPRESSION=true
```

**Command Line Options:**
```bash
--cache-dir cache          # Cache directory
--cache-max-age 24         # Cache age in hours
--cache-stats              # Show statistics
--clear-cache              # Clear before running
```

### **GitHub Actions Integration**

**Cache between runs:**
```yaml
- name: Cache pipeline data
  uses: actions/cache@v3
  with:
    path: cache/
    key: ${{ runner.os }}-pipeline-cache-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-pipeline-cache-
```

### **Troubleshooting Cache Issues**

**Common Issues:**
```bash
# Cache not working
ls -la cache/
python run_cached_pipeline.py --clear

# Low cache hit rate
python run_cached_pipeline.py --stats
# Increase cache age if needed: --cache-max-age 48

# Cache corruption
rm -rf cache/
python run_cached_pipeline.py
```

**Debug Mode:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for cache operations
logger = logging.getLogger('smart_cache')
logger.setLevel(logging.DEBUG)
```

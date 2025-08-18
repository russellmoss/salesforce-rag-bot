# 🚀 Setup Guide for Salesforce RAG Bot

This guide will help you set up and run the Salesforce RAG Bot with your own API keys and Salesforce data.

## 📋 Prerequisites

Before you begin, ensure you have:

- Python 3.11+ installed
- A Salesforce org with API access
- API keys for at least one LLM provider (OpenAI, Anthropic, or Google)
- A Pinecone account and API key

## 🔧 Environment Configuration

### 1. Create Environment File

Create a `.env` file in the root directory (`salesforce-rag-bot/.env`) with the following variables:

```env
# Required: Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=salesforce-schema

# Required: At least one LLM provider (OpenAI, Anthropic, or Google)
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Anthropic Configuration (Alternative to OpenAI)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Google Configuration (Alternative to OpenAI)
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-1.5-pro

# Optional: RAG Configuration
MAX_TOKENS=4000
TEMPERATURE=0.1
TOP_K=5
TOP_P=0.95
```

### 2. Get Your API Keys

#### Pinecone
1. Sign up at [pinecone.io](https://pinecone.io)
2. Create a new index (dimension: 1536, metric: cosine)
3. Copy your API key from the dashboard

#### OpenAI
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Create an API key in your account settings
3. Ensure you have credits for GPT-4o

#### Anthropic (Alternative)
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Ensure you have access to Claude 3.5 Sonnet

#### Google (Alternative)
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create an API key
3. Enable the Gemini API

## 🏗️ Installation

### 1. Install Dependencies

```bash
# Install pipeline dependencies
pip install -r requirements.txt

# Install chatbot dependencies
pip install -r src/chatbot/requirements.txt
```

### 2. Run the Data Pipeline

First, you need to extract your Salesforce schema and upload it to Pinecone:

```bash
# Authenticate to Salesforce
sf org login web -a YourOrgAlias

# Run the pipeline
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --output ./output \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone
```

### 3. Launch the Chatbot

```bash
streamlit run src/chatbot/app.py
```

The application will be available at `http://localhost:8501`

## 🔍 Verification

### Check System Status

When you launch the app, check the sidebar for:

- ✅ **Pinecone Connected** - Your vector database is accessible
- 🤖 **LLM Provider** - Shows which AI model you're using
- 📊 **Index Name** - Confirms the correct Pinecone index

### Test the Chat

Try asking questions like:
- "What fields are available on the Account object?"
- "Show me all automation related to Contact creation"
- "What permission sets exist in my org?"

## 🛠️ Troubleshooting

### Common Issues

1. **"Pinecone Not Connected"**
   - Check your `PINECONE_API_KEY` is correct
   - Verify the index exists in your Pinecone dashboard
   - Ensure the region matches your index location

2. **"No LLM Provider"**
   - Make sure at least one API key is set (OpenAI, Anthropic, or Google)
   - Check the API key format is correct
   - Verify you have credits/access to the chosen model

3. **"No relevant context found"**
   - Run the data pipeline first to populate Pinecone
   - Check that your Salesforce org has data
   - Verify the index name matches between pipeline and chatbot

4. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version (3.11+ required)
   - Try reinstalling requirements: `pip install -r src/chatbot/requirements.txt --force-reinstall`

### Debug Mode

To see detailed logs, set the logging level:

```python
# In app.py, change:
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Use environment variables in production deployments
- Regularly rotate your API keys
- Monitor your API usage to avoid unexpected charges

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Verify your API keys and permissions
4. Ensure your Salesforce org is accessible

For additional help, refer to the main README.md file.

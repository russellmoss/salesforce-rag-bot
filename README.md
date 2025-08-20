# 🤖 Salesforce Schema AI Assistant

Transform your Salesforce org into an intelligent knowledge base! This AI-powered assistant lets you chat with your Salesforce schema, understanding your objects, fields, automation, and security model instantly.

## 🏆 Why This Tool is Essential for RevOps & Salesforce Admins

**Finally, an AI assistant that actually understands YOUR Salesforce org** - not generic documentation, not customer service scripts, but your actual schema, automation, and security model.

### 🎯 Built Specifically for RevOps & Admin Teams

While other tools focus on customer service or generic documentation, this is the **ONLY** AI-powered solution designed specifically for the people who build and maintain Salesforce orgs.

### 📊 How We Compare to Everything Else

| Feature | **Salesforce Schema AI Assistant** | Einstein Copilot | Agentforce | Traditional Tools |
|---------|-----------------------------------|------------------|------------|-------------------|
| **Understands YOUR Schema** | ✅ Complete org analysis | ❌ Generic only | ❌ Process focused | ✅ Limited |
| **Natural Language Chat** | ✅ Ask anything | ✅ Limited scope | ✅ Customer service | ❌ Click-based |
| **Automation Analysis** | ✅ Flows, triggers, rules | ❌ No | ❌ No | ⚠️ Manual |
| **Security & FLS Insights** | ✅ Complete coverage | ❌ No | ❌ No | ⚠️ Basic |
| **Cost** | ✅ Free (your API keys) | 💰 Enterprise pricing | 💰 Premium add-on | 💰 Varies |
| **Setup Time** | ✅ 30 minutes | ❌ Weeks | ❌ Months | ⚠️ Hours |
| **Privacy** | ✅ Your data, your control | ⚠️ Salesforce hosted | ⚠️ Salesforce hosted | ✅ Local |

### 🚀 Game-Changing Benefits for Your Team

#### **For RevOps Teams:**
- **Instant Impact Analysis**: "What flows will break if I change this field?" - get answers in seconds
- **Cross-Object Intelligence**: "Show me all automation touching the Opportunity object" - complete visibility
- **Security Audits Made Easy**: "Which profiles can edit Amount fields?" - instant compliance checks

#### **For Salesforce Admins:**
- **No More Clicking Through Setup**: Ask questions naturally instead of navigating endless menus
- **Documentation That Updates Itself**: Daily syncs mean your knowledge base is always current
- **Onboard New Team Members Faster**: They can ask the AI instead of interrupting you

#### **For Occasional Developers:**
- **No Need to Remember Field APIs**: "What's the API name for the account billing address?"
- **Understand Complex Relationships**: "How are Opportunities related to Quotes?"
- **Debug Without Digging**: "What validation rules exist on Contact?"

### 💡 Real-World Use Cases That Save Hours

1. **🔍 Impact Analysis Before Changes**
   - *Traditional way*: Manually check every flow, trigger, and rule (2-3 hours)
   - *With this tool*: "What depends on Account.Custom_Field__c?" (30 seconds)

2. **📝 Documentation for Audits**
   - *Traditional way*: Screenshot and document everything manually (8+ hours)
   - *With this tool*: "Generate a report of all Lead automation" (instant)

3. **🔐 Security Reviews**
   - *Traditional way*: Click through every profile and permission set (4-5 hours)
   - *With this tool*: "Who can delete Opportunities?" (instant)

4. **🎯 Debugging Issues**
   - *Traditional way*: Check flows, triggers, validation rules one by one (1-2 hours)
   - *With this tool*: "What automation fires when a Case is created?" (instant)

### 🏅 The Bottom Line

This isn't just another Salesforce tool - it's your **AI-powered Salesforce expert** that:
- ✅ Knows YOUR specific org inside and out
- ✅ Answers complex questions in plain English
- ✅ Updates automatically every night
- ✅ Costs less than a single consulting hour to set up
- ✅ Saves dozens of hours every month

**Stop clicking through Setup. Start asking questions.**

## 📋 Table of Contents

- [🎯 What Does This Do?](#-what-does-this-do)
- [⚡ Before You Start](#-before-you-start-2-minute-setup)
- [🚀 Quick Start Guide](#-quick-start-guide)
- [📋 What to Expect During Setup](#-what-to-expect-during-setup)
- [✅ Success Checklist](#-success-checklist)
- [🌐 Deploy to the Cloud](#-deploy-your-chatbot-to-the-cloud-free-hosting)
- [🔄 Automated Daily Updates](#-automated-daily-updates-github-actions)
- [🐳 Docker Installation](#-docker-installation-alternative)
- [📁 What Gets Created?](#-what-gets-created-local-deployment)
- [🛠️ Customization](#️-customization)
- [❓ FAQ](#-faq)
- [🆘 Troubleshooting](#️-troubleshooting)

## 🎯 What Does This Do?

This tool:
- **Extracts** your entire Salesforce schema (objects, fields, relationships, automation)
- **Stores** it in a searchable vector database (Pinecone)
- **Provides** an AI chatbot that can answer questions about your org instantly

Ask questions like:
- "What fields are on the Account object?"
- "Show me all validation rules for Contacts"
- "Which workflows trigger when a Lead is created?"
- "What permissions does the Sales team have?"

## ⚡ Before You Start (2-minute setup)

**What you'll need:**
- ✅ A computer (Windows, Mac, or Linux)
- ✅ Internet connection  
- ✅ A Salesforce account (any type)
- ⏱️ About 30 minutes of your time

**What this will give you:**
- 🤖 An AI assistant that knows your Salesforce inside and out
- 📊 Instant answers about your org structure
- 🔄 Automatic daily updates

**Time commitment:**
- Setup: 30 minutes (one-time)
- Daily updates: Automatic (no work needed)
- Using the tool: As needed (instant answers)

## 🚀 Quick Start Guide

### Prerequisites

You'll need:
1. A computer with Python 3.11+ installed
2. **Salesforce CLI** installed and authenticated
3. A Salesforce account (any type - Production, Sandbox, or Developer)
4. API keys from:
   - [Pinecone](https://pinecone.io) (free tier available)
   - [OpenAI](https://platform.openai.com) (or Anthropic/Google as alternatives)

#### Install Salesforce CLI

**Windows:**
```bash
# Download and install from https://developer.salesforce.com/tools/sfdxcli
# Or use winget:
winget install Salesforce.SalesforceCLI
```

**macOS:**
```bash
# Using Homebrew
brew install salesforce-cli

# Or using npm
npm install --global @salesforce/cli
```

**Linux:**
```bash
# Using npm
npm install --global @salesforce/cli

# Or download from https://developer.salesforce.com/tools/sfdxcli
```

**Verify installation:**
```bash
sf --version
```

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/salesforce-rag-bot.git
cd salesforce-rag-bot
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
pip install -r src/chatbot/requirements.txt
```

### Step 3: Set Up Your API Keys

Create a `.env` file in the root directory and add your keys:

```env
# Required - Get from pinecone.io
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=salesforce-schema

# Required - At least one AI provider
OPENAI_API_KEY=sk-your-openai-key

# Optional - Alternative AI providers
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_API_KEY=your-google-key
```

### Step 4: Connect to YOUR Salesforce Org

```bash
# This will open a browser to log into YOUR Salesforce org
sf org login web -a MyOrg
```

**If you get an error about Salesforce CLI not being found:**
1. Make sure you installed Salesforce CLI (see Prerequisites above)
2. Restart your terminal/command prompt
3. Try the command again

> **Note**: Replace `MyOrg` with a name for your org (e.g., `ProductionOrg`, `MyCompany`, etc.)
> 
> **💡 How to find your org name:** 
> - Log into your Salesforce org in a browser
> - Look at the URL: `https://yourcompany.my.salesforce.com` → use `yourcompany`
> - Or check the org name in Setup → Company Information → Organization Name
> - Examples: If your URL is `acme.my.salesforce.com`, use `acme` or `AcmeCorp`

### Step 5: Extract Your Salesforce Schema

```bash
# Run the optimized pipeline (takes 15-30 minutes)
python run_optimized_pipeline.py --org-alias MyOrg --with-stats --with-automation --emit-markdown --emit-jsonl --push-to-pinecone
```

This will:
- Connect to YOUR Salesforce org
- Download all objects, fields, and metadata
- Create embeddings and upload to Pinecone
- Generate documentation files

### Step 6: Start the AI Assistant

```bash
streamlit run src/chatbot/app.py
```

Open your browser to `http://localhost:8501` and start chatting with your Salesforce schema!

### 🧪 Quick Test

To verify everything is working, try asking:
- "What objects do I have?"
- "Show me the Account object fields"
- "What validation rules exist?"

## 📋 What to Expect During Setup

### During Step 4 (Salesforce Login):
- A browser window will open
- Log into your Salesforce org normally
- You'll be redirected back to the terminal
- You'll see "Successfully authorized" message

### During Step 5 (Schema Extraction):
- Progress bars will show what's happening
- You'll see messages like "Processing Account object..."
- This takes 15-30 minutes for most orgs
- You can safely leave it running

### During Step 6 (Starting the Assistant):
- A browser window will open automatically
- You'll see a chat interface
- Type "What objects do I have?" to test it

## ✅ Success Checklist

After completing all steps, you should have:

- [ ] A `.env` file with your API keys
- [ ] Successfully logged into Salesforce (`sf org display` works)
- [ ] An `output/` folder with files in it
- [ ] A browser window with the chat interface open
- [ ] The ability to ask "What objects do I have?" and get an answer

If any of these are missing, check the troubleshooting section below.

> **🎉 Success!** You now have a working AI assistant for your Salesforce org!
> 
> **Next steps:**
> - Deploy to the cloud for 24/7 access (see [Deploy to the Cloud](#-deploy-your-chatbot-to-the-cloud-free-hosting) section)
> - Set up automatic daily updates (see [Automated Daily Updates](#-automated-daily-updates-github-actions) section)

## 🌐 Deploy Your Chatbot to the Cloud (Free Hosting!)

Want your AI assistant available 24/7 from anywhere? Deploy it to Streamlit Cloud for free!

### 📋 Prerequisites

Before deploying, make sure you've:
- ✅ Completed the local setup and tested the chatbot works
- ✅ Pushed your code to GitHub (your own fork)
- ✅ Have your API keys ready (Pinecone, OpenAI/Anthropic)

### 🚀 Step-by-Step Streamlit Cloud Deployment

#### Step 1: Prepare Your GitHub Repository

First, make sure your code is on GitHub:

```bash
# If you haven't already, create a GitHub account and fork this repo
# Then clone YOUR fork:
git clone https://github.com/YOUR-USERNAME/salesforce-rag-bot.git
cd salesforce-rag-bot

# Make sure you're on the main branch
git checkout main

# Push any local changes
git add .
git commit -m "Ready for Streamlit deployment"
git push origin main
```

#### Step 2: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" and choose "Continue with GitHub"
3. Authorize Streamlit to access your GitHub

#### Step 3: Create Your App

Once logged in:
1. Click "New app"
2. Fill in the deployment settings:
   - **Repository**: `YOUR-USERNAME/salesforce-rag-bot`
   - **Branch**: `main`
   - **Main file path**: `src/chatbot/app.py`
   - **App URL** (optional): Choose a custom URL like `your-company-salesforce-bot`
3. **Click "Advanced settings" before deploying!**

#### Step 4: Add Your Secret API Keys

⚠️ **CRITICAL**: Add your secrets BEFORE clicking deploy!

In the "Secrets" section, paste this EXACTLY (with your real keys):

```toml
# Pinecone Configuration
PINECONE_API_KEY = "your-actual-pinecone-api-key"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_INDEX_NAME = "salesforce-schema"

# AI Provider (at least one required)
OPENAI_API_KEY = "sk-your-actual-openai-key"

# Optional AI Providers
ANTHROPIC_API_KEY = "sk-ant-your-actual-anthropic-key"
GOOGLE_API_KEY = "your-actual-google-key"

# RAG Configuration
MAX_TOKENS = "16000"
TEMPERATURE = "0.1"
TOP_K = "10"
```

⚠️ **Important**: Use your ACTUAL API keys here, not placeholder text!

#### Step 5: Deploy Your App

1. After adding secrets, click "Deploy!"
2. Streamlit will build your app (takes 3-5 minutes)
3. You'll see logs showing the deployment progress
4. Once complete, your app will be live at your URL!

### 🔧 Connecting to Your Salesforce Data

**Important**: The chatbot on Streamlit Cloud will connect to the SAME Pinecone index you created during local setup. This means:

✅ Your Salesforce data is already available  
✅ No need to re-run the pipeline  
✅ Daily updates via GitHub Actions will keep it current  

### 📱 Using Your Deployed App

Your chatbot is now available at:
`https://your-app-name.streamlit.app`

Share this URL with your team! They can now:
- Ask questions about your Salesforce schema
- Get instant answers about fields, objects, and automation
- Access it from any device with internet

### 🔄 Updating Your Deployed App

Whenever you make changes:

```bash
# Make your changes locally
git add .
git commit -m "Update chatbot feature"
git push origin main
```

Streamlit automatically redeploys when you push to GitHub!

### 🔍 Troubleshooting Deployment Issues

#### "App is not loading"
- Check the logs in Streamlit Cloud dashboard
- Verify all secrets are added correctly
- Ensure requirements.txt files are present

#### "ModuleNotFoundError"
- Check both requirements.txt files exist:
  - `/requirements.txt`
  - `/src/chatbot/requirements.txt`

#### "Connection to Pinecone failed"
- Verify your Pinecone API key in secrets
- Check the index name matches exactly
- Ensure Pinecone region is correct

#### "No data found"
- Make sure you ran the pipeline locally first
- Verify the Pinecone index has data (check Pinecone dashboard)
- Confirm the index name in secrets matches your local `.env`

### 🎯 Best Practices for Production

- **Limit Access**: Make your app private in Streamlit settings if needed
- **Monitor Usage**: Check your API usage on OpenAI/Pinecone dashboards
- **Set Limits**: Configure spending limits on your API accounts
- **Regular Updates**: Use GitHub Actions to keep schema current

### 🔒 Security Notes

- Secrets are encrypted and never visible in logs
- Only you can see/edit the secrets
- API keys are not exposed to app users
- Consider using read-only API keys where possible

## 🔄 Automated Daily Updates (GitHub Actions)

If you prefer Docker:

```bash
# Build the image
docker build -t salesforce-rag-bot .

# Run the pipeline
docker run -v $(pwd)/output:/app/output \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  salesforce-rag-bot \
  --org-alias MyOrg

# Run the chatbot
docker run -p 8501:8501 \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  salesforce-rag-bot-chatbot
```

## 🔄 Automated Daily Updates (GitHub Actions)

Keep your schema up-to-date automatically!

### Step 1: Fork This Repository

Click the "Fork" button on GitHub to create your own copy.

### Step 2: Get Your Salesforce Auth URL

```bash
# Display your org's auth URL
sf org display -a MyOrg --verbose

# Copy the "Sfdx Auth Url" value
```

### Step 3: Add GitHub Secrets

In your forked repo, go to Settings → Secrets → Actions and add:

| Secret Name | Value |
|-------------|-------|
| `SFDX_AUTH_URL` | The auth URL from step 2 |
| `PINECONE_API_KEY` | Your Pinecone API key |
| `OPENAI_API_KEY` | Your OpenAI API key |

### Step 4: Enable GitHub Actions

The pipeline will now run automatically every day at midnight UTC, keeping your schema synchronized!

To run manually:
1. Go to Actions tab
2. Click "Salesforce Schema Pipeline"
3. Click "Run workflow"

## 🐳 Docker Installation (Alternative)

If you prefer Docker for local deployment:

```bash
# Build the image
docker build -t salesforce-rag-bot .

# Run the pipeline
docker run -v $(pwd)/output:/app/output \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  salesforce-rag-bot \
  --org-alias MyOrg

# Run the chatbot
docker run -p 8501:8501 \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  salesforce-rag-bot-chatbot
```

## 📁 What Gets Created? (Local Deployment)

After running the pipeline locally, you'll have:

```
output/
├── schema.json          # Complete schema data
├── md/                  # Markdown docs for each object
│   ├── Account.md
│   ├── Contact.md
│   └── ...
└── corpus.jsonl         # Vector database input
```

## 🛠️ Customization

### Use Different Salesforce Orgs

```bash
# Production org
sf org login web -a Production
python run_optimized_pipeline.py --org-alias Production

# Sandbox
sf org login web -a Sandbox --instance-url https://test.salesforce.com
python run_optimized_pipeline.py --org-alias Sandbox

# Multiple orgs
sf org login web -a ClientA
sf org login web -a ClientB
# Run pipeline for each as needed
```

### Adjust Performance

```bash
# Faster (more resources)
python run_optimized_pipeline.py --max-workers 20

# Slower (limited resources)
python run_optimized_pipeline.py --max-workers 5

# Skip certain features for speed
python run_optimized_pipeline.py --skip-stats --skip-automation
```

## ❓ FAQ

### "How do I connect to my production Salesforce?"
Just use `sf org login web` - it will open your browser to log into ANY Salesforce org (Production, Sandbox, or Developer).

### "How long does the pipeline take?"
- First run: 15-30 minutes for most orgs
- Daily updates: 2-5 minutes (only processes changes)

### "Can I use this with multiple orgs?"
Yes! Give each org a different alias when logging in, then run the pipeline for each.

### "Is my data secure?"
- Your data stays in YOUR Pinecone account
- API keys are never shared or uploaded
- All processing happens locally or in your GitHub Actions

### "What if I don't have OpenAI?"
You can use Anthropic (Claude) or Google (Gemini) instead. Just add their API keys to `.env`.

## 🆘 Troubleshooting

### Can't connect to Salesforce?
```bash
# Check your connection
sf org display -a MyOrg

# Re-authenticate
sf org login web -a MyOrg --set-default
```

### Salesforce CLI not found?
1. **Install Salesforce CLI** (see Prerequisites section above)
2. **Restart your terminal** after installation
3. **Verify installation**: `sf --version`
4. **Try the login command again**

### Pipeline fails?
```bash
# Run with more details
python run_optimized_pipeline.py --org-alias MyOrg --verbose

# Check API limits
sf org limits -a MyOrg

# Check if Salesforce CLI is working
sf org display -a MyOrg
```

### Chatbot not finding data?
1. Ensure pipeline completed successfully
2. Check Pinecone dashboard for your index
3. Verify API keys in `.env` file

## 📝 License

MIT License - Use freely!

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a PR with clear description

## 💡 Support

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Updates**: Watch this repo for new features

---

Built with ❤️ to make Salesforce development easier!
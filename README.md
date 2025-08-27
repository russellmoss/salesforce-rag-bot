# 🤖 Salesforce Schema AI Assistant

Transform your Salesforce org into an intelligent knowledge base! This AI-powered assistant extracts your **complete** Salesforce schema including objects, fields, relationships, automation, **AND comprehensive security data** - then stores it all in a searchable vector database for instant AI-powered insights.

## 🏆 Why This Tool is Essential for RevOps & Salesforce Admins

**Finally, an AI assistant that actually understands YOUR Salesforce org** - not generic documentation, not customer service scripts, but your actual schema, automation, security model, and permission structure.

### 🎯 Built Specifically for RevOps & Admin Teams

While other tools focus on customer service or generic documentation, this is the **ONLY** AI-powered solution designed specifically for the people who build and maintain Salesforce orgs, with **complete security and permission awareness**.

### 📊 How We Compare to Everything Else

| Feature | **Salesforce Schema AI Assistant** | Einstein Copilot | Agentforce | Traditional Tools |
|---------|-----------------------------------|------------------|------------|-------------------|
| **Understands YOUR Schema** | ✅ Complete org analysis | ❌ Generic only | ❌ Process focused | ✅ Limited |
| **Natural Language Chat** | ✅ Ask anything | ✅ Limited scope | ✅ Customer service | ❌ Click-based |
| **Automation Analysis** | ✅ Flows, triggers, rules | ❌ No | ❌ No | ⚠️ Manual |
| **Security & FLS Insights** | ✅ **Complete coverage** | ❌ No | ❌ No | ⚠️ Basic |
| **Profile & Permission Sets** | ✅ **Full analysis** | ❌ No | ❌ No | ❌ No |
| **Object Permissions** | ✅ **CRUD permissions** | ❌ No | ❌ No | ❌ No |
| **Field-Level Security** | ✅ **Complete FLS data** | ❌ No | ❌ No | ⚠️ Basic |
| **Performance Optimization** | ✅ **Advanced caching & search** | ❌ No | ❌ No | ❌ No |
| **Large Database Support** | ✅ **1000+ documents** | ❌ No | ❌ No | ⚠️ Limited |
| **Performance Monitoring** | ✅ **Built-in tools** | ❌ No | ❌ No | ❌ No |
| **Cost** | ✅ Free (your API keys) | 💰 Enterprise pricing | 💰 Premium add-on | 💰 Varies |
| **Setup Time** | ✅ 30 minutes | ❌ Weeks | ❌ Months | ⚠️ Hours |
| **Privacy** | ✅ Your data, your control | ⚠️ Salesforce hosted | ⚠️ Salesforce hosted | ✅ Local |

### 🚀 Game-Changing Benefits for Your Team

#### **For RevOps Teams:**
- **Instant Impact Analysis**: "What flows will break if I change this field?" - get answers in seconds
- **Cross-Object Intelligence**: "Show me all automation touching the Opportunity object" - complete visibility
- **Security Audits Made Easy**: "Which profiles can edit Amount fields?" - instant compliance checks
- **Permission Analysis**: "Who has delete access to Opportunities?" - complete security visibility
- **⚡ Lightning Fast Searches**: Advanced caching makes repeated queries 50-80% faster

#### **For Salesforce Admins:**
- **No More Clicking Through Setup**: Ask questions naturally instead of navigating endless menus
- **Documentation That Updates Itself**: Daily syncs mean your knowledge base is always current
- **Onboard New Team Members Faster**: They can ask the AI instead of interrupting you
- **Security Reviews**: "Show me all profiles with Account edit permissions" - instant security insights
- **🎯 Smart Object Detection**: Finds exact objects even in large databases with 1000+ documents

#### **For Occasional Developers:**
- **No Need to Remember Field APIs**: "What's the API name for the account billing address?"
- **Understand Complex Relationships**: "How are Opportunities related to Quotes?"
- **Debug Without Digging**: "What validation rules exist on Contact?"
- **Security Context**: "Which permission sets grant access to custom fields?"
- **📊 Performance Monitoring**: Built-in tools to optimize and monitor search performance

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

5. **🔒 Compliance Audits**
   - *Traditional way*: Review every profile and permission set manually (6+ hours)
   - *With this tool*: "Show me all profiles with access to sensitive fields" (instant)

6. **⚡ Performance Optimization**
   - *Traditional way*: Manually test and optimize search performance (2-3 hours)
   - *With this tool*: Run performance monitor and get optimization recommendations (5 minutes)

### 🏅 The Bottom Line

This isn't just another Salesforce tool - it's your **AI-powered Salesforce expert** that:
- ✅ Knows YOUR specific org inside and out
- ✅ **Understands your complete security model**
- ✅ Answers complex questions in plain English
- ✅ Updates automatically every night
- ✅ Costs less than a single consulting hour to set up
- ✅ Saves dozens of hours every month
- ✅ **⚡ Optimized for large databases** with advanced caching and search strategies
- ✅ **🎯 Smart object detection** for precise, accurate results

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
- [🚀 Performance Optimizations](#-performance-optimizations-for-large-databases)
- [❓ FAQ](#-faq)
- [🆘 Troubleshooting](#️-troubleshooting)

## 🎯 What Does This Do?

This tool **comprehensively extracts** your entire Salesforce org and creates an AI assistant that knows everything about it:

### 📊 **Complete Data Extraction:**
- **Objects & Fields**: All SObjects, custom fields, relationships, data types
- **Automation**: Flows, triggers, validation rules, workflow rules
- **Statistics**: Record counts, field fill rates, usage patterns
- **Security**: **Complete security model including:**
  - **Profiles**: All profile permissions and settings
  - **Permission Sets**: All permission sets and their assignments
  - **Object Permissions**: CRUD permissions for every object
  - **Field-Level Security**: FLS settings for every field
  - **Metadata**: Profile and permission set metadata

### 🤖 **AI-Powered Intelligence:**
- **Vector Database**: Stores everything in Pinecone for semantic search
- **Natural Language**: Ask questions in plain English
- **Context Awareness**: Understands relationships between objects
- **Security Insights**: Knows who can access what
- **⚡ Performance Optimized**: Advanced caching and search strategies for large databases
- **🎯 Smart Object Detection**: Finds exact object matches with enhanced pattern matching
- **📊 Performance Monitoring**: Built-in tools to optimize and monitor performance

### 🔄 **Progressive Collection Strategy:**
- **Phase 1**: Immediate setup with schema and automation (bot works today!)
- **Phase 2**: Progressive security data collection over 4-7 days
- **Phase 3**: Complete security knowledge in vector database
- **Ongoing**: Daily incremental updates

Ask questions like:
- "What fields are on the Account object?"
- "Show me all validation rules for Contacts"
- "Which workflows trigger when a Lead is created?"
- "**Which profiles can delete Contacts?**"
- "**What fields can the Admin profile edit on Account?**"
- "**Which permission sets grant access to Opportunity fields?**"
- "**Who has read access to sensitive fields?**"

## ⚡ Before You Start (2-minute setup)

**What you'll need:**
- ✅ A computer (Windows, Mac, or Linux)
- ✅ Internet connection  
- ✅ A Salesforce account (any type)
- ⏱️ About 30 minutes of your time

**What this will give you:**
- 🤖 An AI assistant that knows your Salesforce inside and out
- 📊 Instant answers about your org structure
- 🔒 **Complete security and permission insights**
- 🔄 Automatic daily updates

**Time commitment:**
- Setup: 30 minutes (one-time)
- **Progressive collection**: 4-7 days (automated, no work needed)
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

### Step 5: Extract Your Salesforce Schema (Automated Multi-Phase Setup)

**🎉 NEW: Fully Automated Progressive Setup!** 

We've created a GitHub Action that automatically handles the entire multi-phase setup process. The system uses a **progressive collection strategy** to work within Salesforce API limits while building complete knowledge.

#### Option A: Automated Setup (Recommended)

1. **Add GitHub Secrets** (see [Automated Daily Updates](#-automated-daily-updates-github-actions) section)
2. **Run the automated workflow**:
   - Go to Actions tab in your GitHub repo
   - Click "Initial Setup with Progressive Security Collection"
   - Click "Run workflow"
   - Enter your org alias (e.g., "MyOrg")
   - Click "Run workflow"

**That's it!** The workflow will:
- ✅ **Day 1**: Complete initial setup and push to Pinecone (bot works immediately!)
- ✅ **Days 2-6**: Automatically collect security data in chunks (200 objects/day)
- ✅ **Day 7**: Automatically push complete security data to Pinecone
- ✅ **Completion**: Creates a GitHub issue when everything is done

**You'll get:**
- 🚀 **Working bot on Day 1** with schema knowledge
- 📈 **Progressive security knowledge** building over days
- 🔔 **Automatic notifications** when complete
- 📊 **Progress tracking** in GitHub Actions

#### Option B: Manual Setup (Original Method)

If you prefer to run it manually, here's the original multi-phase approach:

#### Phase 1: Initial Setup (Get Your Bot Working Today)

```bash
# Get everything EXCEPT security data and push to Pinecone immediately
python src/pipeline/build_schema_library_end_to_end.py --org-alias MyOrg --output ./output_new --max-workers 3 --cache-dir cache_new --cache-max-age 24 --with-stats --with-automation --emit-jsonl --push-to-pinecone --resume
```

This will:
- ✅ Connect to YOUR Salesforce org
- ✅ Download all objects, fields, and metadata
- ✅ Get usage statistics and automation data
- ✅ Create embeddings and upload to Pinecone
- ✅ **Your bot is now working!** 🎉

**What your bot can answer immediately:**
- "What fields are on the Account object?"
- "Show me all validation rules for Contacts"
- "What automation exists on Opportunity?"
- "How many records are in each object?"

#### Phase 2: Security Data Collection (Next 4-7 Days)

```bash
# Collect security data over multiple days (runs until it hits API limits)
python src/pipeline/build_schema_library_end_to_end.py --org-alias MyOrg --output ./output_new --max-workers 3 --cache-dir cache_new --cache-max-age 24 --with-security --resume
```

**Run this same command each day until it completes:**
- **Day 1**: Processes ~200 objects, hits limits, saves progress
- **Day 2**: Resumes from where it left off, processes next ~200 objects
- **Day 3**: Continues with next batch
- **Day 4-7**: Completes remaining objects

**The pipeline automatically:**
- ✅ Saves partial progress each day
- ✅ Resumes exactly where it left off
- ✅ Skips already-processed objects
- ✅ Shows clear progress indicators

**What gets collected during this phase:**
- **Profiles**: All profile information and settings
- **Permission Sets**: All permission sets and their metadata
- **Object Permissions**: CRUD permissions for every object
- **Field-Level Security**: FLS settings for every field
- **Metadata**: Complete profile and permission set metadata

#### Phase 3: Final Security Push (When Complete)

```bash
# Push complete security data to Pinecone (run when Phase 2 finishes)
python src/pipeline/build_schema_library_end_to_end.py --org-alias MyOrg --output ./output_new --max-workers 3 --cache-dir cache_new --cache-max-age 24 --with-security --emit-jsonl --push-to-pinecone --resume
```

**What your bot can now answer:**
- "**Which profiles can delete Contacts?**"
- "**What fields can the Admin profile edit on Account?**"
- "**Which permission sets grant access to Opportunity fields?**"
- "**Who has read access to sensitive fields?**"
- "**Show me all profiles with Account edit permissions**"
- "**Which permission sets allow Opportunity deletion?**"

#### Phase 4: Daily Updates (Ongoing)

Once everything is complete, daily updates are much faster:

```bash
# Future daily updates - only processes changed objects, no API limits
python src/pipeline/build_schema_library_end_to_end.py --org-alias MyOrg --output ./output_new --max-workers 3 --cache-dir cache_new --cache-max-age 24 --with-security --with-stats --emit-jsonl --push-to-pinecone --resume
```

**Why this progressive approach works:**
- 🚀 **Immediate value** - Your bot works today with rich schema knowledge
- 📈 **Progressive enhancement** - Security knowledge builds over days
- ⚡ **Future efficiency** - Daily updates only process changes, not everything
- 🔄 **No data loss** - Each day builds on previous progress
- 🔒 **Complete security model** - Full understanding of permissions and access

**Timeline:**
- **Today**: Complete setup + Pinecone push (bot works!)
- **Days 2-7**: Security data collection (200 objects/day)
- **Day 8**: Final security push (complete knowledge)
- **Ongoing**: Daily incremental updates (fast, no limits)

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
- "**Which profiles can edit Account records?**" (after security collection)

## 📋 What to Expect During Setup

### During Step 4 (Salesforce Login):
- A browser window will open
- Log into your Salesforce org normally
- You'll be redirected back to the terminal
- You'll see "Successfully authorized" message

### During Step 5 (Schema Extraction):
- **Phase 1**: Progress bars will show what's happening
- You'll see messages like "Processing Account object..."
- This takes 15-30 minutes for most orgs
- You can safely leave it running
- **Phase 2**: Daily runs showing security data collection progress
- You'll see messages like "Found 16 profiles to analyze"
- Each day processes ~200 objects until complete
- **Phase 3**: Final push of complete security data to vector database

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
- [ ] **Complete security knowledge** (after progressive collection)
- [ ] **Ability to ask security questions** like "Who can delete Contacts?"

If any of these are missing, check the troubleshooting section below.

> **🎉 Success!** You now have a working AI assistant for your Salesforce org with **complete security knowledge**!
> 
> **Next steps:**
> - Deploy to the cloud for 24/7 access (see [Deploy to the Cloud](#-deploy-your-chatbot-to-the-cloud-free-hosting) section)
> - Set up automatic daily updates (see [Automated Daily Updates](#-automated-daily-updates-github-actions) section)

## 🌐 Deploy Your Chatbot to the Cloud (Free Hosting!)

Want your AI assistant available 24/7 from anywhere? Deploy it to Streamlit Cloud for free!

### 📋 Prerequisites

Before deploying, make sure you've:
- ✅ Completed the local setup and tested the chatbot works
- ✅ **Completed the progressive security collection** (4-7 days)
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
✅ **Your complete security knowledge is available**  
✅ No need to re-run the pipeline  
✅ Daily updates via GitHub Actions will keep it current  

### 📱 Using Your Deployed App

Your chatbot is now available at:
`https://your-app-name.streamlit.app`

Share this URL with your team! They can now:
- Ask questions about your Salesforce schema
- Get instant answers about fields, objects, and automation
- **Get complete security insights** about permissions and access
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
- **Ensure progressive security collection is complete**
- Verify the Pinecone index has data (check Pinecone dashboard)
- Confirm the index name in secrets matches your local `.env`

### 🎯 Best Practices for Production

- **Limit Access**: Make your app private in Streamlit settings if needed
- **Monitor Usage**: Check your API usage on OpenAI/Pinecone dashboards
- **Set Limits**: Configure spending limits on your API accounts
- **Regular Updates**: Use GitHub Actions to keep schema current
- **Security Awareness**: Your bot now has complete security knowledge

### 🔒 Security Notes

- Secrets are encrypted and never visible in logs
- Only you can see/edit the secrets
- API keys are not exposed to app users
- Consider using read-only API keys where possible
- **Your bot has complete security knowledge** - ensure appropriate access controls

## 🔄 Automated Daily Updates (GitHub Actions)

Keep your schema up-to-date automatically! **Note**: This is for ongoing daily updates after your initial setup is complete.

### Initial Setup vs Daily Updates

**Initial Setup (First Time):**
- Use the automated workflow: "Initial Setup with Progressive Security Collection"
- Takes 4-7 days to complete due to API limits
- Builds complete security knowledge progressively
- **Fully automated** - runs daily until complete

**Daily Updates (Ongoing):**
- Much faster - only processes changed objects
- No API limit issues - only incremental changes
- Can be automated with GitHub Actions

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
| `SF_ORG_ALIAS` | Your org alias (e.g., "MyOrg") |

### Step 4: Enable GitHub Actions

The pipeline will now run automatically every day at midnight UTC, keeping your schema synchronized!

To run manually:
1. Go to Actions tab
2. Click "Salesforce Schema Pipeline"
3. Click "Run workflow"

## 📧 Email Alerts & Monitoring

Get notified automatically when your daily schema updates succeed, fail, or have issues!

### 🚀 Quick Setup (Choose One Option)

#### Option A: GitHub Built-in Notifications (Easiest - 2 minutes)
1. **Go to GitHub Settings** → Notifications
2. **Enable email notifications** for Actions (workflow runs)
3. **Set frequency** to "Immediate"
4. **Done!** You'll get emails for all workflow events

#### Option B: Custom Email Alerts (Advanced)
Set up detailed email notifications with custom SMTP:

1. **Add these GitHub Secrets**:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM=your-email@gmail.com
   NOTIFICATION_EMAIL=admin@yourcompany.com
   ```

2. **For Gmail users**: Use App Password (not regular password)
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

3. **Test**: Run workflow manually and check for email

### 📧 What You'll Receive

#### ✅ Success Email
```
🎉 Salesforce Schema Update Completed Successfully!
📊 Objects Processed: 247
✅ Your AI assistant is now updated!
```

#### ⚠️ Warning Email
```
⚠️ Salesforce Schema Update Completed with Warnings
📊 Objects Processed: 245
⚠️ Some warnings detected - review logs for details
```

#### ❌ Failure Email
```
❌ Salesforce Schema Update Failed!
🚨 Exit Code: 1, Objects Processed: 23
🔍 Check GitHub Actions logs for details
```

### 🔔 Alternative Notification Methods

- **📱 GitHub Mobile App**: Push notifications on your phone
- **🌐 Browser Notifications**: Real-time alerts when at computer
- **💬 Slack Integration**: Team channel notifications
- **📊 Status Badge**: Visual indicator in README

### 📋 Status Badge (Visual Monitoring)

Add this to your README.md for at-a-glance status:
```markdown
![Pipeline Status](https://github.com/YOUR-USERNAME/salesforce-rag-bot/workflows/Daily%20Salesforce%20Schema%20Update/badge.svg)
```

**Badge Colors:**
- 🟢 Green = Success
- 🔴 Red = Failed  
- 🟡 Yellow = Running

### 🛠️ Troubleshooting Alerts

**"No emails received":**
- Check spam/junk folder
- Verify notification settings
- Test with manual workflow run

**"SMTP authentication failed":**
- Use App Password for Gmail (not regular password)
- Check SMTP server and port settings
- Verify credentials are correct

**For detailed setup instructions**, see:
- [`EMAIL_ALERTS_SETUP.md`](EMAIL_ALERTS_SETUP.md) - Complete email configuration guide
- [`SIMPLE_ALERTS_SETUP.md`](SIMPLE_ALERTS_SETUP.md) - 8 simple notification options

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
├── security.json        # **Complete security data**
├── automation.json      # Automation data
├── stats.json          # Usage statistics
├── md/                  # Markdown docs for each object
│   ├── Account.md
│   ├── Contact.md
│   └── ...
├── corpus.jsonl         # Vector database input
└── security_progress.json # Progress tracking for security collection
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

## 🚀 Performance Optimizations for Large Databases

### ⚡ Enhanced Search & Caching System

The RAG bot now includes **advanced performance optimizations** for handling large Pinecone databases with 1000+ documents:

#### **🔍 Smart Search Strategies**
- **Object-Specific Targeting**: Finds exact object matches (e.g., "Contact") before partial matches
- **Enhanced Pattern Matching**: Uses regex patterns to detect object names in queries
- **Security Query Detection**: Automatically detects security-related questions for optimized search
- **Batch Processing**: Configurable batch sizes for efficient database queries

#### **💾 Intelligent Caching**
- **In-Memory Cache**: Caches search results to avoid repeated queries
- **Configurable TTL**: Set cache expiration time (default: 5 minutes)
- **Cache Statistics**: Monitor cache hit rates and performance
- **Automatic Cache Management**: Clears expired entries automatically

#### **⚙️ Performance Configuration**

Add these environment variables to optimize for your database size:

```bash
# For large databases (>1000 documents)
SEARCH_BATCH_SIZE=200
MAX_SEARCH_RESULTS=2000
ENABLE_SEARCH_CACHING=true
CACHE_TTL_SECONDS=300

# For very large databases (>5000 documents)
SEARCH_BATCH_SIZE=500
MAX_SEARCH_RESULTS=5000
ENABLE_SEARCH_CACHING=true
CACHE_TTL_SECONDS=600
```

#### **📊 Performance Monitoring**

Run the built-in performance monitor to optimize your setup:

```bash
# Test performance with various queries
python performance_monitor.py

# This will:
# - Test 10 different query types
# - Measure search times and cache efficiency
# - Provide optimization recommendations
# - Save detailed performance reports
```

#### **🎯 Optimized for Large Scale**

**Database Size** | **Recommended Settings** | **Expected Performance**
---|---|---
< 500 documents | Default settings | < 0.5s search time
500-1000 documents | `SEARCH_BATCH_SIZE=100` | < 1s search time
1000-5000 documents | `SEARCH_BATCH_SIZE=200` | < 2s search time
5000+ documents | `SEARCH_BATCH_SIZE=500` | < 3s search time

#### **🔧 Advanced Features**

- **Progressive Search**: Searches exact matches first, then expands to related objects
- **Query Optimization**: Automatically optimizes search queries based on content type
- **Memory Management**: Efficient memory usage for large result sets
- **Error Recovery**: Graceful handling of API limits and timeouts

#### **📈 Performance Benefits**

- **⚡ 50-80% faster searches** for repeated queries (cache hits)
- **🎯 More accurate results** with object-specific targeting
- **📊 Better scalability** for large databases
- **🛠️ Easy optimization** with performance monitoring tools

### 🧪 Performance Testing

Test your setup with the included performance monitor:

```bash
# Quick performance test
python performance_monitor.py

# Detailed test with custom queries
python performance_monitor.py --iterations 5 --custom-queries
```

The performance monitor will:
- ✅ Test search speed and accuracy
- ✅ Measure cache effectiveness
- ✅ Provide optimization recommendations
- ✅ Generate detailed performance reports
- ✅ Suggest configuration improvements

## ❓ FAQ

### "How do I connect to my production Salesforce?"
Just use `sf org login web` - it will open your browser to log into ANY Salesforce org (Production, Sandbox, or Developer).

### "How long does the pipeline take?"
- **Initial setup**: 4-7 days (multi-phase approach due to API limits)
  - Phase 1: 30 minutes (bot works immediately)
  - Phase 2: 4-7 days (security data collection)
  - Phase 3: 30 minutes (final security push)
- **Daily updates**: 2-5 minutes (only processes changes, no API limits)

### "Can I use this with multiple orgs?"
Yes! Give each org a different alias when logging in, then run the pipeline for each.

### "Is my data secure?"
- Your data stays in YOUR Pinecone account
- API keys are never shared or uploaded
- All processing happens locally or in your GitHub Actions
- **Your bot has complete security knowledge** - ensure appropriate access controls

### "What if I don't have OpenAI?"
You can use Anthropic (Claude) or Google (Gemini) instead. Just add their API keys to `.env`.

### "What security data gets collected?"
The system collects **complete security information**:
- **Profiles**: All profile settings and permissions
- **Permission Sets**: All permission sets and their metadata
- **Object Permissions**: CRUD permissions for every object
- **Field-Level Security**: FLS settings for every field
- **Metadata**: Complete profile and permission set metadata

### "Why does security collection take 4-7 days?"
Salesforce has API limits that prevent collecting all security data at once. The progressive approach:
- Respects API limits
- Saves progress daily
- Resumes automatically
- Ensures complete data collection

### "How does the performance optimization work?"
The RAG bot includes advanced optimizations for large databases:
- **Smart Caching**: Caches search results to avoid repeated queries
- **Object-Specific Search**: Finds exact object matches before partial matches
- **Batch Processing**: Configurable batch sizes for efficient database queries
- **Performance Monitoring**: Built-in tools to test and optimize performance

### "What database sizes does this support?"
The bot is optimized for various database sizes:
- **< 500 documents**: Default settings work perfectly
- **500-1000 documents**: Enable caching for better performance
- **1000-5000 documents**: Use recommended performance settings
- **5000+ documents**: Advanced optimization settings available

### "How do I optimize performance for my database?"
1. **Run the performance monitor**: `python performance_monitor.py`
2. **Follow the recommendations** provided by the monitor
3. **Adjust environment variables** based on your database size
4. **Enable caching** for repeated queries
5. **Monitor cache hit rates** to ensure optimal performance

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
2. **Ensure progressive security collection is complete**
3. Check Pinecone dashboard for your index
4. Verify API keys in `.env` file

### Security collection stuck?
- Check GitHub Actions logs for progress
- The system automatically resumes from where it left off
- Each day processes ~200 objects until complete
- Look for "Found progress tracking" messages in logs

### Performance issues?
```bash
# Run performance test
python performance_monitor.py

# Check cache statistics
# The bot logs cache hit/miss rates automatically

# Optimize for large databases
export SEARCH_BATCH_SIZE=200
export MAX_SEARCH_RESULTS=2000
export ENABLE_SEARCH_CACHING=true

# Clear cache if needed
# Restart the bot to clear the cache
```

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
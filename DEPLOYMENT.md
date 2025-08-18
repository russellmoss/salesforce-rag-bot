# 🚀 Deployment Guide

This guide will help you deploy your Salesforce RAG Bot to GitHub and Streamlit Cloud.

## 📋 **Pre-Deployment Checklist**

Before pushing to GitHub, ensure you have:

- ✅ [ ] All code is working locally
- ✅ [ ] API keys are ready (but not committed)
- ✅ [ ] `.gitignore` is properly configured
- ✅ [ ] README.md is updated
- ✅ [ ] No sensitive data in the repository

## 🔧 **GitHub Repository Setup**

### **1. Create GitHub Repository**

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `salesforce-rag-bot`
3. Make it **public** (required for Streamlit Cloud)
4. **Don't** initialize with README (we already have one)

### **2. Push Your Code**

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit your changes
git commit -m "Initial commit: Salesforce RAG Bot with pipeline and chatbot"

# Add your GitHub repository as remote
git remote add origin https://github.com/your-username/salesforce-rag-bot.git

# Push to GitHub
git push -u origin main
```

### **3. Verify Repository Structure**

Your GitHub repository should look like this:

```
salesforce-rag-bot/
├── src/
│   ├── pipeline/
│   │   └── build_schema_library_end_to_end.py
│   └── chatbot/
│       ├── app.py
│       ├── config.py
│       └── requirements.txt
├── .github/
│   └── workflows/
│       └── run_pipeline.yml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── DEPLOYMENT.md
└── .gitignore
```

## 🌐 **Streamlit Cloud Deployment**

### **1. Connect to Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**

### **2. Configure App Settings**

- **Repository**: `your-username/salesforce-rag-bot`
- **Branch**: `main`
- **Main file path**: `src/chatbot/app.py`
- **App URL**: `your-app-name` (optional custom URL)

### **3. Add Secrets**

In the Streamlit Cloud dashboard, add these secrets:

```toml
OPENAI_API_KEY = "sk-your-openai-key"
PINECONE_API_KEY = "your-pinecone-key"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_INDEX_NAME = "salesforce-schema"
ANTHROPIC_API_KEY = "sk-ant-your-anthropic-key"
GOOGLE_API_KEY = "your-google-key"
```

### **4. Deploy**

Click **"Deploy!"** and wait for the build to complete.

## 🔄 **GitHub Actions Setup**

### **1. Configure GitHub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these repository secrets:

| Secret Name | Description |
|-------------|-------------|
| `SFDX_AUTH_URL` | Salesforce auth URL |
| `PINECONE_API_KEY` | Pinecone API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `PINECONE_CLOUD` | Pinecone cloud provider |
| `PINECONE_REGION` | Pinecone region |
| `PINECONE_INDEX_NAME` | Pinecone index name |

### **2. Test GitHub Actions**

1. Go to **Actions** tab in your repository
2. Select **"Daily Salesforce Schema Update"**
3. Click **"Run workflow"**
4. Monitor the execution

## 📊 **Post-Deployment Verification**

### **1. Test Streamlit App**

1. Visit your Streamlit Cloud URL
2. Verify the app loads without errors
3. Test the chat interface
4. Check connection status in sidebar

### **2. Test GitHub Actions**

1. Monitor the first automated run
2. Check Pinecone for new vectors
3. Verify pipeline artifacts are uploaded

### **3. Monitor Performance**

- **Streamlit app** response times
- **Pinecone** usage and costs
- **GitHub Actions** execution time
- **Error logs** and debugging

## 🔧 **Troubleshooting**

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Streamlit app fails to load | Check secrets configuration |
| Pinecone connection errors | Verify API key and region |
| GitHub Actions fails | Check SFDX_AUTH_URL format |
| Import errors | Verify requirements.txt |

### **Debugging Steps**

1. **Check Streamlit logs** in the cloud dashboard
2. **Monitor GitHub Actions** execution logs
3. **Verify API keys** are correctly formatted
4. **Test locally** before pushing changes

## 🔄 **Continuous Deployment**

### **Automatic Updates**

- **Code changes**: Push to `main` branch triggers Streamlit redeploy
- **Pipeline updates**: GitHub Actions runs daily at 1 AM UTC
- **Dependency updates**: Update requirements.txt and push

### **Manual Triggers**

- **GitHub Actions**: Use "Run workflow" button
- **Streamlit**: Automatic on code push
- **Pipeline**: Manual execution via GitHub Actions

## 📈 **Monitoring & Maintenance**

### **Regular Tasks**

- [ ] Monitor Pinecone usage and costs
- [ ] Check GitHub Actions execution logs
- [ ] Update API keys as needed
- [ ] Review Streamlit app performance
- [ ] Update dependencies periodically

### **Performance Optimization**

- [ ] Optimize retrieval parameters
- [ ] Monitor response times
- [ ] Adjust caching strategies
- [ ] Review error rates

## 🎯 **Next Steps**

After successful deployment:

1. **Test the full workflow** end-to-end
2. **Configure monitoring** and alerts
3. **Set up backup strategies**
4. **Document any customizations**
5. **Share with your team**

---

**Your Salesforce RAG Bot is now live and ready to use! 🚀**

# 🚀 Optimized Pipeline Examples

This document provides practical examples of how to run the pipeline with different optimization strategies.

## 📊 Performance Comparison

| Strategy | Time Savings | Risk Level | Use Case |
|----------|-------------|------------|----------|
| Default | Baseline | Low | First-time setup |
| Conservative | 25-33% | Low | Production updates |
| Aggressive | 40-60% | Medium | Development/testing |
| Incremental | 50-80% | Low | Regular updates |

## 🎯 Optimization Scenarios

### **1. Conservative Optimization (Recommended)**

**Best for:** Production environments, large orgs
**Risk:** Low
**Speed improvement:** 25-33%

```bash
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
  --throttle-ms 100 \
  --embed-batch-size 120
```

### **2. Aggressive Optimization**

**Best for:** Development, testing, smaller orgs
**Risk:** Medium (monitor for rate limits)
**Speed improvement:** 40-60%

```bash
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
  --throttle-ms 75 \
  --embed-batch-size 150
```

### **3. Maximum Speed (Use with Caution)**

**Best for:** Small orgs, testing environments
**Risk:** High (may hit rate limits)
**Speed improvement:** 50-70%

```bash
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
  --throttle-ms 50 \
  --embed-batch-size 200
```

### **4. Safe Initial Setup**

**Best for:** First-time pipeline runs
**Risk:** Low
**Speed:** Baseline (but includes all optimizations)

```bash
python src/pipeline/build_schema_library_end_to_end.py \
  --org-alias YourOrgAlias \
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone \
  --output ./output \
  --throttle-ms 100 \
  --embed-batch-size 120
```

## 🔧 Environment Variable Setup

Create a `.env` file with optimized settings:

```env
# Pipeline Optimization
THROTTLE_MS=100
EMBED_BATCH_SIZE=120

# Standard Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=salesforce-schema
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o
```

## 📈 Monitoring Performance

### **Salesforce API Usage Check**

```bash
# Check current API usage
sf org display -a YourOrgAlias --verbose

# Monitor in Salesforce Setup
# Setup → Company Information → API Usage
```

### **Pinecone Rate Limit Monitoring**

```bash
# Check Pinecone console for warnings
# Look for "Rate limit exceeded" messages
```

### **GitHub Actions Optimization**

```yaml
# .github/workflows/run_pipeline.yml
- name: Run Optimized Pipeline
  run: |
    python src/pipeline/build_schema_library_end_to_end.py \
      --org-alias ${{ secrets.SF_ORG_ALIAS }} \
      --resume \
      --stats-resume \
      --emit-jsonl \
      --incremental-update \
      --push-to-pinecone \
      --with-stats \
      --with-metadata \
      --output ./output \
      --throttle-ms 100 \
      --embed-batch-size 120
```

## 🚨 Troubleshooting

### **If You Hit Rate Limits**

```bash
# Increase throttling
--throttle-ms 200

# Reduce batch size
--embed-batch-size 50

# Use more conservative settings
--throttle-ms 150 --embed-batch-size 96
```

### **If GitHub Actions Times Out**

```bash
# Use incremental updates only
--incremental-update --resume --stats-resume

# Skip automation step
# (Don't use --with-automation for updates)
```

### **If Embeddings Fail**

```bash
# Reduce batch size
--embed-batch-size 50

# Check OpenAI rate limits
# Monitor OpenAI dashboard for usage
```

## 📊 Expected Performance

### **Small Org (< 100 objects)**
- **Default:** 2-4 hours
- **Optimized:** 1-2 hours
- **Aggressive:** 30-60 minutes

### **Medium Org (100-500 objects)**
- **Default:** 6-12 hours
- **Optimized:** 4-8 hours
- **Aggressive:** 2-4 hours

### **Large Org (> 500 objects)**
- **Default:** 12-24 hours
- **Optimized:** 8-16 hours
- **Aggressive:** 4-8 hours

## 🎯 Best Practices

1. **Start Conservative:** Begin with `--throttle-ms 100`
2. **Monitor Closely:** Watch for rate limit warnings
3. **Scale Gradually:** Increase optimization if stable
4. **Use Incremental:** Always use `--resume` for updates
5. **Test First:** Try optimizations on dev orgs first

## 🔄 Regular Update Command

For daily/weekly updates, use this optimized command:

```bash
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
  --throttle-ms 100 \
  --embed-batch-size 120
```

**Expected time:** 30 minutes - 2 hours (depending on changes)


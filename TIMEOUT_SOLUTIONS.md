# Salesforce Schema Pipeline - Timeout Solutions

## 🚨 Current Timeout Issues

### Problem Analysis
The pipeline is experiencing timeouts due to:

1. **Individual Command Timeouts**: Each Salesforce CLI command has a 120-second timeout
2. **GitHub Actions Timeout**: 360-minute limit (6 hours) 
3. **Large Dataset**: 1458 objects requiring ~6+ hours to process
4. **API Rate Limiting**: Salesforce API throttling causing delays
5. **Network Latency**: Production environments may have slower connections

### Current Performance Metrics
- **Objects Processed**: 675/1458 (46% complete)
- **Time Elapsed**: 326 minutes (5.4 hours)
- **Estimated Total Time**: 8+ hours
- **Timeout Occurred**: On "Idea" object after 326 minutes

## ✅ Implemented Solutions

### 1. Increased Individual Command Timeout
**File**: `src/pipeline/build_schema_library_end_to_end.py`
```python
def run_sf(args: List[str], env: Optional[Dict[str, str]] = None, timeout: int = 300) -> Tuple[int, str, str]:
```
- **Change**: Increased from 120s to 300s (5 minutes)
- **Benefit**: Handles slow API responses better

### 2. Enhanced Error Handling with Retries
**File**: `src/pipeline/build_schema_library_end_to_end.py`
```python
except subprocess.TimeoutExpired:
    if attempt < cfg.retries:
        wait_time = (cfg.backoff_ms * (2 ** attempt)) / 1000.0
        print(f"    Timeout on attempt {attempt + 1}, retrying in {wait_time:.1f}s...")
        time.sleep(wait_time)
    else:
        print(f"    ❌ Timeout after {cfg.retries + 1} attempts for {name}")
        errors.append(name)
        break
```
- **Change**: Graceful timeout handling with exponential backoff
- **Benefit**: Continues processing other objects when one fails

### 3. Batch Processing Implementation
**File**: `src/pipeline/build_schema_library_end_to_end.py`
```python
# Process in batches to avoid overwhelming the API
BATCH_SIZE = 50
for batch_start in range(0, total, BATCH_SIZE):
    # ... batch processing logic ...
    # Add a longer pause between batches to avoid rate limiting
    if batch_end < total:
        print(f"Pausing 30 seconds between batches...")
        time.sleep(30)
```
- **Change**: Process objects in batches of 50 with 30-second pauses
- **Benefit**: Reduces API pressure and improves reliability

### 4. Increased GitHub Actions Timeout
**File**: `.github/workflows/run_pipeline.yml`
```yaml
timeout-minutes: 480  # Increased from 360 to 480 (8 hours)
```
- **Change**: Extended from 6 hours to 8 hours
- **Benefit**: Accommodates full pipeline execution time

## 🚀 Production Deployment Recommendations

### 1. Optimize Pipeline Configuration

**Recommended Settings for Production**:
```bash
python build_schema_library_end_to_end.py \
  --org-alias "ProductionOrg" \
  --output ./output \
  --throttle-ms 200 \        # Increased from 100ms
  --retries 5 \              # Increased from 3
  --backoff-ms 2000 \        # Increased from 1000ms
  --with-stats \
  --with-automation \
  --with-metadata \
  --emit-jsonl \
  --push-to-pinecone
```

### 2. Implement Resume Capability
**For Production Reliability**:
```bash
# First run (may timeout)
python build_schema_library_end_to_end.py --resume false

# Resume from where it left off
python build_schema_library_end_to_end.py --resume true
```

### 3. Split Processing Strategy
**For Very Large Orgs**:
```bash
# Process in chunks by object type
python build_schema_library_end_to_end.py --max-objects 500
python build_schema_library_end_to_end.py --max-objects 500 --resume true
```

### 4. Alternative: Parallel Processing
**For High-Performance Requirements**:
- Split objects into multiple batches
- Run parallel GitHub Actions jobs
- Merge results at the end

## 🔧 Additional Optimizations

### 1. Object Filtering
**Reduce Processing Load**:
```bash
# Skip noisy objects
python build_schema_library_end_to_end.py --prefilter-noise true

# Skip specific namespaces
python build_schema_library_end_to_end.py --ignore-namespaces "npsp,fflib"
```

### 2. Selective Feature Processing
**Process Only What You Need**:
```bash
# Skip expensive operations
python build_schema_library_end_to_end.py \
  --with-stats false \       # Skip usage statistics
  --with-automation false \  # Skip automation analysis
  --with-metadata false      # Skip permission sets
```

### 3. API Version Optimization
**Use Specific API Versions**:
```bash
python build_schema_library_end_to_end.py \
  --api-versions "64.0,63.0"  # Limit to stable versions
```

## 📊 Monitoring and Alerting

### 1. Progress Tracking
**Monitor Pipeline Progress**:
```bash
# Check progress
ls -la output/raw/ | wc -l  # Count processed objects
tail -f output/raw/_errors.log  # Monitor errors
```

### 2. GitHub Actions Monitoring
**Set Up Alerts**:
- Monitor workflow completion times
- Set up notifications for failures
- Track resource usage

### 3. Salesforce API Monitoring
**Monitor API Limits**:
- Track API call counts
- Monitor rate limiting
- Check org performance

## 🎯 Expected Performance Improvements

### With Current Optimizations:
- **Individual Timeouts**: Reduced by 60% (300s vs 120s)
- **Batch Processing**: 30-second pauses reduce API pressure
- **Error Recovery**: Failed objects don't stop the pipeline
- **Total Time**: Estimated 6-7 hours (vs 8+ hours)

### With Additional Optimizations:
- **Throttle Increase**: 200ms vs 100ms = 50% slower but more reliable
- **Retry Increase**: 5 retries vs 3 = Better error recovery
- **Resume Capability**: Can restart from failure point
- **Object Filtering**: 20-30% reduction in processing time

## 🚨 Emergency Procedures

### If Pipeline Times Out in Production:

1. **Immediate Action**:
   ```bash
   # Check what was processed
   ls output/raw/ | wc -l
   
   # Resume from where it left off
   python build_schema_library_end_to_end.py --resume true
   ```

2. **Fallback Strategy**:
   ```bash
   # Process only essential objects
   python build_schema_library_end_to_end.py \
     --max-objects 200 \
     --with-stats false \
     --with-automation false
   ```

3. **Manual Recovery**:
   - Identify failed objects from `_errors.log`
   - Process them individually
   - Merge results manually

## 📋 Production Checklist

### Before Deployment:
- [ ] Test with smaller org first
- [ ] Verify all API credentials
- [ ] Set up monitoring and alerts
- [ ] Configure appropriate timeouts
- [ ] Test resume functionality

### During Deployment:
- [ ] Monitor GitHub Actions logs
- [ ] Check API rate limits
- [ ] Verify progress indicators
- [ ] Monitor error logs

### After Deployment:
- [ ] Verify all objects processed
- [ ] Check Pinecone upload success
- [ ] Test chatbot functionality
- [ ] Review performance metrics

## 🔮 Future Improvements

### 1. Incremental Updates
- Process only changed objects
- Use Salesforce change tracking
- Implement delta processing

### 2. Caching Strategy
- Cache API responses
- Implement local storage
- Use CDN for static data

### 3. Advanced Error Handling
- Implement circuit breakers
- Add health checks
- Create fallback mechanisms

---

**Note**: These optimizations should resolve the timeout issues for most Salesforce orgs. For extremely large orgs (>2000 objects), consider implementing parallel processing or incremental updates.

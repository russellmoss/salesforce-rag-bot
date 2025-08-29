# Improved RAG Architecture for Salesforce Schema Bot

## Current Problems
- Complex fallback logic that's fragile
- 1000+ documents in single vector search creates noise
- Fixing one search type breaks others
- Inconsistent retrieval strategies

## Proposed Solution: Multi-Index Architecture

### 1. **Separate Vector Indexes by Document Type**
```
Pinecone Indexes:
├── salesforce-objects (Object metadata)
├── salesforce-security (Security permissions) 
├── salesforce-fields (Field definitions)
└── salesforce-relationships (Object relationships)
```

### 2. **Query Router with Intent Classification**
```python
class QueryRouter:
    def route_query(self, query: str) -> List[str]:
        # Classify query intent
        intents = self.classify_intent(query)
        
        # Route to appropriate indexes
        indexes = []
        if "security" in intents or "permission" in intents:
            indexes.append("salesforce-security")
        if "field" in intents or "metadata" in intents:
            indexes.append("salesforce-fields") 
        if "object" in intents:
            indexes.append("salesforce-objects")
            
        return indexes
```

### 3. **Hybrid Retrieval Strategy**
```python
class HybridRetriever:
    def retrieve(self, query: str) -> List[Document]:
        # 1. Direct ID lookup (fastest, most accurate)
        direct_docs = self.direct_lookup(query)
        
        # 2. Vector search in relevant indexes
        vector_docs = self.vector_search(query, indexes)
        
        # 3. Keyword search fallback
        keyword_docs = self.keyword_search(query)
        
        # 4. Combine and rank results
        return self.rank_and_deduplicate(direct_docs, vector_docs, keyword_docs)
```

### 4. **Smart Document Organization**
```python
# Object documents: salesforce_object_Account
# Security documents: security_Account_SystemAdministrator  
# Field documents: field_Account_Name
# Relationship documents: relationship_Account_Contact
```

### 5. **Intent-Aware Response Generation**
```python
class IntentAwareGenerator:
    def generate_response(self, query: str, docs: List[Document]) -> str:
        intent = self.classify_intent(query)
        
        if intent == "field_list":
            return self.generate_field_list_response(docs)
        elif intent == "security_permissions":
            return self.generate_security_response(docs)
        elif intent == "object_metadata":
            return self.generate_metadata_response(docs)
```

## Benefits
1. **Faster**: Direct lookups instead of complex similarity search
2. **More Accurate**: Targeted searches in relevant document types
3. **Scalable**: Can handle 10,000+ documents easily
4. **Maintainable**: Clear separation of concerns
5. **Robust**: Multiple fallback strategies that don't interfere

## Implementation Plan
1. **Phase 1**: Create separate Pinecone indexes
2. **Phase 2**: Implement query router and intent classification
3. **Phase 3**: Build hybrid retriever with direct lookup
4. **Phase 4**: Add intent-aware response generation
5. **Phase 5**: Migrate existing data to new structure

## Cost Considerations
- Multiple indexes: ~$50-100/month additional
- More API calls: ~2-3x current cost
- Better accuracy: Worth the cost for internal tool
- Faster responses: Better user experience

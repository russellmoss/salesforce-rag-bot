#!/usr/bin/env python3
"""
Enhanced Document Organizer for Better Vector DB Structure
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentCategory(Enum):
    """Document categories for better organization"""
    OBJECT_SCHEMA = "object_schema"
    FIELD_METADATA = "field_metadata"
    SECURITY_PERMISSIONS = "security_permissions"
    AUTOMATION = "automation"
    RELATIONSHIPS = "relationships"
    CUSTOM_FIELDS = "custom_fields"
    STANDARD_FIELDS = "standard_fields"
    VALIDATION_RULES = "validation_rules"
    WORKFLOW_RULES = "workflow_rules"
    FLOWS = "flows"
    TRIGGERS = "triggers"

@dataclass
class DocumentMetadata:
    """Enhanced metadata structure for documents"""
    id: str
    category: DocumentCategory
    object_name: str
    field_name: Optional[str] = None
    document_type: str = "salesforce_metadata"
    priority: int = 1  # 1=high, 2=medium, 3=low
    search_keywords: List[str] = None
    related_objects: List[str] = None
    field_count: int = 0
    record_count: int = 0
    is_custom: bool = False
    is_standard: bool = True
    has_automation: bool = False
    has_security: bool = False

class EnhancedDocumentOrganizer:
    """
    Organizes documents for better vector DB structure and searchability
    """
    
    def __init__(self):
        self.standard_objects = {
            'Account', 'Contact', 'Lead', 'Opportunity', 'Case', 'User', 'Profile', 'Role',
            'PermissionSet', 'Group', 'Queue', 'Campaign', 'Product2', 'Pricebook2',
            'PricebookEntry', 'Quote', 'Order', 'OrderItem', 'Contract', 'Asset',
            'Task', 'Event', 'Note', 'Attachment', 'Document', 'Folder', 'Report',
            'Dashboard', 'List', 'ListView', 'CustomObject', 'CustomField', 'ValidationRule',
            'WorkflowRule', 'Flow', 'ProcessBuilder', 'Trigger', 'ApexClass', 'ApexTrigger'
        }
        
        self.search_keywords_map = {
            'Contact': ['contact', 'person', 'individual', 'email', 'phone', 'address', 'account'],
            'Account': ['account', 'company', 'organization', 'business', 'customer', 'client'],
            'Lead': ['lead', 'prospect', 'potential', 'conversion', 'qualification'],
            'Opportunity': ['opportunity', 'deal', 'sales', 'revenue', 'pipeline', 'forecast'],
            'Case': ['case', 'support', 'ticket', 'issue', 'problem', 'resolution'],
            'User': ['user', 'login', 'profile', 'role', 'permission', 'access'],
            'Profile': ['profile', 'permission', 'access', 'security', 'crud'],
            'Role': ['role', 'hierarchy', 'sharing', 'access', 'permission']
        }
    
    def create_enhanced_documents(self, schema_data: Dict[str, Any], 
                                automation_data: Optional[Dict[str, Any]] = None,
                                security_data: Optional[Dict[str, Any]] = None,
                                stats_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Create enhanced documents with better organization and metadata
        """
        documents = []
        
        # Process each object
        for object_name, object_data in schema_data.items():
            logger.info(f"Processing object: {object_name}")
            
            # 1. Main object document
            main_doc = self._create_object_document(object_name, object_data, stats_data)
            documents.append(main_doc)
            
            # 2. Field-specific documents (for better field-level search)
            field_docs = self._create_field_documents(object_name, object_data)
            documents.extend(field_docs)
            
            # 3. Security documents
            if security_data and object_name in security_data:
                security_docs = self._create_security_documents(object_name, security_data[object_name])
                documents.extend(security_docs)
            
            # 4. Automation documents
            if automation_data and object_name in automation_data:
                automation_docs = self._create_automation_documents(object_name, automation_data[object_name])
                documents.extend(automation_docs)
            
            # 5. Relationship documents
            relationship_docs = self._create_relationship_documents(object_name, object_data)
            documents.extend(relationship_docs)
        
        logger.info(f"Created {len(documents)} enhanced documents")
        return documents
    
    def _create_object_document(self, object_name: str, object_data: Dict[str, Any], 
                              stats_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create main object document with enhanced metadata"""
        
        # Build comprehensive content
        content_parts = [f"Object: {object_name}"]
        
        if object_data.get('description'):
            content_parts.append(f"Description: {object_data['description']}")
        
        # Add fields information
        if 'fields' in object_data:
            content_parts.append("Fields:")
            for field_name, field_data in object_data['fields'].items():
                field_type = field_data.get('type', 'Unknown')
                field_label = field_data.get('label', field_name)
                content_parts.append(f"- {field_name}: {field_type} - {field_label}")
        
        # Add relationships
        if 'childRelationships' in object_data:
            content_parts.append("Child Relationships:")
            for rel in object_data['childRelationships']:
                content_parts.append(f"- {rel.get('childSObject', 'Unknown')}")
        
        content = "\n".join(content_parts)
        
        # Create enhanced metadata
        metadata = DocumentMetadata(
            id=f"salesforce_object_{object_name}",
            category=DocumentCategory.OBJECT_SCHEMA,
            object_name=object_name,
            document_type="salesforce_object",
            priority=1,
            search_keywords=self._get_search_keywords(object_name),
            related_objects=self._get_related_objects(object_data),
            field_count=len(object_data.get('fields', {})),
            record_count=stats_data.get(object_name, {}).get('record_count', 0) if stats_data else 0,
            is_custom=object_name not in self.standard_objects,
            is_standard=object_name in self.standard_objects,
            has_automation=bool(automation_data and object_name in automation_data) if 'automation_data' in locals() else False,
            has_security=bool(security_data and object_name in security_data) if 'security_data' in locals() else False
        )
        
        return {
            "id": metadata.id,
            "text": content,
            "metadata": {
                "id": metadata.id,
                "object_name": metadata.object_name,
                "type": metadata.document_type,
                "category": metadata.category.value,
                "priority": metadata.priority,
                "search_keywords": metadata.search_keywords,
                "related_objects": metadata.related_objects,
                "fields_count": metadata.field_count,
                "record_count": metadata.record_count,
                "is_custom": metadata.is_custom,
                "is_standard": metadata.is_standard,
                "has_automation": metadata.has_automation,
                "has_security": metadata.has_security,
                "content": content[:1000] + "..." if len(content) > 1000 else content
            }
        }
    
    def _create_field_documents(self, object_name: str, object_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create individual field documents for better field-level search"""
        documents = []
        
        if 'fields' not in object_data:
            return documents
        
        for field_name, field_data in object_data['fields'].items():
            # Skip system fields for now (can be configured)
            if field_name in ['Id', 'CreatedDate', 'LastModifiedDate', 'SystemModstamp']:
                continue
            
            # Build field-specific content
            content_parts = [f"Field: {field_name}"]
            content_parts.append(f"Object: {object_name}")
            content_parts.append(f"Type: {field_data.get('type', 'Unknown')}")
            content_parts.append(f"Label: {field_data.get('label', field_name)}")
            
            if field_data.get('description'):
                content_parts.append(f"Description: {field_data['description']}")
            
            if field_data.get('required'):
                content_parts.append("Required: Yes")
            
            if field_data.get('unique'):
                content_parts.append("Unique: Yes")
            
            if field_data.get('referenceTo'):
                content_parts.append(f"References: {', '.join(field_data['referenceTo'])}")
            
            content = "\n".join(content_parts)
            
            # Determine field category
            category = DocumentCategory.CUSTOM_FIELDS if field_name.endswith('__c') else DocumentCategory.STANDARD_FIELDS
            
            metadata = DocumentMetadata(
                id=f"field_{object_name}_{field_name}",
                category=category,
                object_name=object_name,
                field_name=field_name,
                document_type="field_metadata",
                priority=2,
                search_keywords=[field_name.lower(), field_data.get('label', '').lower()],
                is_custom=field_name.endswith('__c'),
                is_standard=not field_name.endswith('__c')
            )
            
            documents.append({
                "id": metadata.id,
                "text": content,
                "metadata": {
                    "id": metadata.id,
                    "object_name": metadata.object_name,
                    "field_name": metadata.field_name,
                    "type": metadata.document_type,
                    "category": metadata.category.value,
                    "priority": metadata.priority,
                    "search_keywords": metadata.search_keywords,
                    "is_custom": metadata.is_custom,
                    "is_standard": metadata.is_standard,
                    "content": content
                }
            })
        
        return documents
    
    def _create_security_documents(self, object_name: str, security_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create security-specific documents"""
        documents = []
        
        # Object-level security
        if 'object_permissions' in security_data:
            content = f"Object: {object_name}\nSecurity Permissions:\n"
            for perm, value in security_data['object_permissions'].items():
                content += f"- {perm}: {value}\n"
            
            documents.append({
                "id": f"security_object_{object_name}",
                "text": content,
                "metadata": {
                    "id": f"security_object_{object_name}",
                    "object_name": object_name,
                    "type": "security_permissions",
                    "category": DocumentCategory.SECURITY_PERMISSIONS.value,
                    "security_type": "object_permissions",
                    "priority": 1,
                    "content": content
                }
            })
        
        # Field-level security
        if 'field_permissions' in security_data:
            for field_name, field_perms in security_data['field_permissions'].items():
                content = f"Object: {object_name}\nField: {field_name}\nField Security:\n"
                for perm, value in field_perms.items():
                    content += f"- {perm}: {value}\n"
                
                documents.append({
                    "id": f"security_field_{object_name}_{field_name}",
                    "text": content,
                    "metadata": {
                        "id": f"security_field_{object_name}_{field_name}",
                        "object_name": object_name,
                        "field_name": field_name,
                        "type": "security_permissions",
                        "category": DocumentCategory.SECURITY_PERMISSIONS.value,
                        "security_type": "field_permissions",
                        "priority": 2,
                        "content": content
                    }
                })
        
        return documents
    
    def _create_automation_documents(self, object_name: str, automation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create automation-specific documents"""
        documents = []
        
        # Validation rules
        if 'validation_rules' in automation_data:
            for rule_name, rule_data in automation_data['validation_rules'].items():
                content = f"Object: {object_name}\nValidation Rule: {rule_name}\n"
                content += f"Description: {rule_data.get('description', 'No description')}\n"
                content += f"Error Message: {rule_data.get('errorMessage', 'No error message')}\n"
                
                documents.append({
                    "id": f"validation_{object_name}_{rule_name}",
                    "text": content,
                    "metadata": {
                        "id": f"validation_{object_name}_{rule_name}",
                        "object_name": object_name,
                        "type": "automation",
                        "category": DocumentCategory.VALIDATION_RULES.value,
                        "automation_type": "validation_rule",
                        "priority": 2,
                        "content": content
                    }
                })
        
        # Workflow rules
        if 'workflow_rules' in automation_data:
            for rule_name, rule_data in automation_data['workflow_rules'].items():
                content = f"Object: {object_name}\nWorkflow Rule: {rule_name}\n"
                content += f"Description: {rule_data.get('description', 'No description')}\n"
                
                documents.append({
                    "id": f"workflow_{object_name}_{rule_name}",
                    "text": content,
                    "metadata": {
                        "id": f"workflow_{object_name}_{rule_name}",
                        "object_name": object_name,
                        "type": "automation",
                        "category": DocumentCategory.WORKFLOW_RULES.value,
                        "automation_type": "workflow_rule",
                        "priority": 2,
                        "content": content
                    }
                })
        
        return documents
    
    def _create_relationship_documents(self, object_name: str, object_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create relationship-specific documents"""
        documents = []
        
        if 'childRelationships' in object_data:
            for rel in object_data['childRelationships']:
                child_object = rel.get('childSObject', 'Unknown')
                relationship_name = rel.get('relationshipName', 'Unknown')
                
                content = f"Object: {object_name}\nChild Relationship: {relationship_name}\n"
                content += f"Child Object: {child_object}\n"
                content += f"Relationship Type: {rel.get('relationshipType', 'Unknown')}\n"
                
                documents.append({
                    "id": f"relationship_{object_name}_{relationship_name}",
                    "text": content,
                    "metadata": {
                        "id": f"relationship_{object_name}_{relationship_name}",
                        "object_name": object_name,
                        "related_object": child_object,
                        "type": "relationship",
                        "category": DocumentCategory.RELATIONSHIPS.value,
                        "relationship_type": rel.get('relationshipType', 'Unknown'),
                        "priority": 3,
                        "content": content
                    }
                })
        
        return documents
    
    def _get_search_keywords(self, object_name: str) -> List[str]:
        """Get search keywords for an object"""
        keywords = [object_name.lower()]
        
        if object_name in self.search_keywords_map:
            keywords.extend(self.search_keywords_map[object_name])
        
        return keywords
    
    def _get_related_objects(self, object_data: Dict[str, Any]) -> List[str]:
        """Get related objects from object data"""
        related = []
        
        # From child relationships
        if 'childRelationships' in object_data:
            for rel in object_data['childRelationships']:
                child_object = rel.get('childSObject')
                if child_object:
                    related.append(child_object)
        
        # From field references
        if 'fields' in object_data:
            for field_name, field_data in object_data['fields'].items():
                if 'referenceTo' in field_data:
                    related.extend(field_data['referenceTo'])
        
        return list(set(related))  # Remove duplicates
    
    def save_enhanced_corpus(self, documents: List[Dict[str, Any]], output_dir: Path):
        """Save enhanced corpus to JSONL file"""
        corpus_file = output_dir / "enhanced_corpus.jsonl"
        
        with open(corpus_file, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc) + "\n")
        
        logger.info(f"Saved enhanced corpus with {len(documents)} documents to {corpus_file}")
        
        # Also save a summary
        summary_file = output_dir / "corpus_summary.json"
        summary = {
            "total_documents": len(documents),
            "categories": {},
            "objects": {},
            "document_types": {}
        }
        
        for doc in documents:
            metadata = doc['metadata']
            category = metadata.get('category', 'unknown')
            object_name = metadata.get('object_name', 'unknown')
            doc_type = metadata.get('type', 'unknown')
            
            summary['categories'][category] = summary['categories'].get(category, 0) + 1
            summary['objects'][object_name] = summary['objects'].get(object_name, 0) + 1
            summary['document_types'][doc_type] = summary['document_types'].get(doc_type, 0) + 1
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved corpus summary to {summary_file}")

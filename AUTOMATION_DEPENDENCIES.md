# Automation Dependencies, Field-Level Security, Audit History, and Qualitative Analysis Feature

This document describes the automation dependencies, field-level security, audit history, and qualitative analysis functionality added to the Salesforce schema builder.

## Overview

The automation dependencies, field-level security, audit history, and qualitative analysis feature allows you to discover and document:
- **Automation**: Flows and Apex triggers that are associated with each Salesforce object
- **Field-Level Security**: Permission sets that can edit or read each field
- **Audit History**: Creation and modification history for custom fields
- **Code Complexity**: Lines of code and comment analysis for triggers and classes
- **Data Quality**: Picklist value distributions and data freshness metrics
- **User Adoption**: Top owning profiles and usage patterns

This information is useful for understanding the automation landscape, security model, audit trail, code quality, data health, user adoption, and dependencies in your Salesforce org.

## How It Works

When the `--with-automation` flag is provided, the script will:

1. Query the Tooling API for each Salesforce object to find:
   - **Flows**: Auto-launched flows that are triggered by the object
   - **Apex Triggers**: Triggers that are associated with the object
   - **Field-Level Security**: Permission sets that can edit or read each field
   - **Audit History**: Creation and modification history for custom fields
   - **Code Complexity**: Lines of code and comment analysis for triggers and classes

2. Query the Data API for operational metrics:
   - **Data Quality**: Picklist value distributions and data freshness analysis
   - **User Adoption**: Top owning profiles and usage patterns

3. Store automation information in the object's `_relationshipMetadata.automationSummary` field

4. Store FLS information in each field's `_flsSummary` field

5. Store audit history information in each custom field's `_auditHistory` field

6. Store data quality and user adoption metrics in the object's `_relationshipMetadata.usageSummary` field

7. Include all information in the generated Markdown documentation

## Usage

To enable automation dependencies fetching, add the `--with-automation` flag to your command:

```bash
python build_schema_library_end_to_end.py --org-alias TP --with-automation --emit-markdown
```

## API Queries

The feature uses multiple Tooling API and Data API queries:

### Tooling API Queries

#### Flows Query
```sql
SELECT Name, Description 
FROM Flow 
WHERE ProcessType = 'AutoLaunchedFlow' 
AND TriggerObjectOrEvent.QualifiedApiName = '{sobject_name}'
```

#### Apex Triggers Query
```sql
SELECT Name, Body 
FROM ApexTrigger 
WHERE TableEnumOrId = '{sobject_name}'
```

#### Apex Classes Query
```sql
SELECT Name, Body 
FROM ApexClass 
WHERE Body LIKE '%{sobject_name}%'
```

#### Field-Level Security Query
```sql
SELECT Field, PermissionSet.Label, PermissionsEdit, PermissionsRead 
FROM FieldPermissions 
WHERE SobjectType = '{sobject_name}'
```

**Note**: The `Field` column returns values in the format `ObjectName.FieldName` (e.g., `Account.Amount__c`). The script extracts just the field name for storage.

#### Audit History Query
```sql
SELECT DeveloperName, CreatedBy.Name, CreatedDate, LastModifiedBy.Name, LastModifiedDate 
FROM CustomField 
WHERE TableEnumOrId = '{sobject_name}'
```

**Note**: This query only returns data for custom fields (fields with `custom = true`).

### Data API Queries

#### Picklist Distribution Query
```sql
SELECT {field_name}, COUNT(Id) 
FROM {sobject_name} 
GROUP BY {field_name}
```

#### Data Freshness Query
```sql
SELECT COUNT(Id) 
FROM {sobject_name} 
WHERE LastModifiedDate < {two_years_ago_date}
```

#### User Adoption Query
```sql
SELECT Owner.Profile.Name, COUNT(Id) 
FROM {sobject_name} 
GROUP BY Owner.Profile.Name 
ORDER BY COUNT(Id) DESC 
LIMIT 5
```

## Output Format

### Automation Dependencies
The automation dependencies are stored in the following format:

```json
{
  "automationSummary": {
    "flows": ["FlowName1", "FlowName2"],
    "triggers": ["TriggerName1", "TriggerName2"]
  }
}
```

### Field-Level Security
The FLS data is stored in each field's `_flsSummary` field:

```json
{
  "fields": [
    {
      "name": "Amount",
      "type": "currency",
      "_flsSummary": {
        "editable_by": ["Sales Ops", "Admin"],
        "readonly_by": ["Sales Team"]
      }
    }
  ]
}
```

### Audit History
The audit history data is stored in each custom field's `_auditHistory` field:

```json
{
  "fields": [
    {
      "name": "Amount__c",
      "type": "currency",
      "custom": true,
      "_auditHistory": {
        "created_by": "Jane Doe",
        "created_date": "2018-05-20T10:30:00.000+0000",
        "last_modified_by": "Integration User",
        "last_modified_date": "2024-07-18T14:45:00.000+0000"
      }
    }
  ]
}
```

### Code Complexity
The code complexity data is stored in the automation summary:

```json
{
  "automationSummary": {
    "flows": ["FlowName1"],
    "triggers": ["TriggerName1"],
    "code_complexity": {
      "triggers": [
        {
          "name": "AccountTrigger",
          "total_lines": 50,
          "comment_lines": 10,
          "code_lines": 40
        }
      ],
      "classes": [
        {
          "name": "AccountHelper",
          "total_lines": 100,
          "comment_lines": 20,
          "code_lines": 80
        }
      ]
    }
  }
}
```

### Data Quality and User Adoption
The data quality and user adoption metrics are stored in the usage summary:

```json
{
  "usageSummary": {
    "data_quality": {
      "picklist_distributions": {
        "Status__c": [
          {"value": "Active", "count": 100},
          {"value": "Inactive", "count": 50}
        ]
      },
      "data_freshness": {
        "old_records_count": 30,
        "total_records": 200,
        "percentage_old": 15.0
      }
    },
    "user_adoption": {
      "top_owning_profiles": [
        {"profile": "System Administrator", "record_count": 150},
        {"profile": "Sales User", "record_count": 75}
      ]
    }
  }
}
```

## Markdown Output

### Automation Section
When automation dependencies are found, the generated Markdown will include an "Automation" section:

```markdown
## Automation

### Flows
- `AccountFlow1`
- `AccountFlow2`

### Apex Triggers
- `AccountTrigger1`
- `AccountTrigger2`
```

### Field-Level Security and Audit History in Fields Table
When FLS or audit history data is available, the fields table will include this information:

```markdown
| Field | Type | Req | Unique | ExtId | Len | Prec | Scale | Formula |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `Amount__c` | `currency` |  |  |  |  |  |  |  |
| *FLS: Editable by Sales Ops, Admin; Read-only by Sales Team* |  |  |  |  |  |  |  |  |
| *History: Created by Jane Doe on 2018-05-20; Last modified by Integration User on 2024-07-18* |  |  |  |  |  |  |  |  |
```

### Code Complexity in Automation Section
When code complexity data is available, the automation section will include:

```markdown
## Automation

### Flows
- `AccountFlow1`

### Apex Triggers
- `AccountTrigger1`

### Code Complexity

#### Triggers
- `AccountTrigger`: 50 total lines (40 code, 10 comments)

#### Related Apex Classes
- `AccountHelper`: 100 total lines (80 code, 20 comments)
```

### Data Quality and User Adoption Analysis
When data quality and user adoption data is available, the usage section will include:

```markdown
## Data Quality Analysis

### Picklist Value Distributions

#### Status__c

| Value | Count |
|---|---:|
| Active | 100 |
| Inactive | 50 |

### Data Freshness
- **Records older than 2 years**: 30 out of 200 (15.0%)

## User Adoption Analysis

### Top Owning Profiles

| Profile | Record Count |
|---|---:|
| System Administrator | 150 |
| Sales User | 75 |
```

## Performance Considerations

- Each object requires 6 additional Tooling API calls (2 for automation + 1 for FLS + 1 for audit history + 2 for code complexity)
- Each object requires additional Data API calls for data quality and user adoption metrics
- The script respects the `--throttle-ms` setting to avoid overwhelming the API
- Progress is reported every 25 objects processed
- Errors are logged but don't stop the process

## Requirements

- Salesforce CLI (sf) must be installed and authenticated
- The authenticated user must have access to the Tooling API and Data API
- Appropriate permissions to query Flow, ApexTrigger, ApexClass, FieldPermissions, and CustomField metadata
- Appropriate permissions to query object data for picklist distributions and user adoption analysis

## Error Handling

If automation dependencies, FLS data, audit history, code complexity, data quality, or user adoption data cannot be fetched for an object:
- An error message is printed to the console
- The object's `automationSummary` is set to empty arrays with empty code complexity
- Fields without FLS data will not have the `_flsSummary` field
- Custom fields without audit history will not have the `_auditHistory` field
- Data quality and user adoption metrics will be set to empty structures
- The process continues with the next object

## Testing

The functionality has been tested with mock data to verify:
- Tooling API query functionality for flows, triggers, classes, field permissions, and custom field metadata
- Data API query functionality for picklist distributions, data freshness, and user adoption
- Automation dependencies parsing and storage
- Field-level security parsing and storage
- Audit history parsing and storage
- Code complexity analysis and storage
- Data quality metrics parsing and storage
- User adoption metrics parsing and storage
- Markdown generation with all qualitative analysis data
- Error handling for missing or invalid data

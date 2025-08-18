#!/usr/bin/env python3
"""
Simple test for Smart API Batching functionality.
"""

import json
from unittest.mock import patch
from src.pipeline.build_schema_library_end_to_end import get_all_automation_data_batched

def test_simple_batching():
    """Simple test for batched automation data."""
    print("🧪 Testing Simple Batched Automation Data...")
    
    # Test data
    test_objects = ["Account", "Contact"]
    
    # Mock Salesforce CLI responses
    mock_flows_response = {
        "result": {
            "records": [
                {
                    "Name": "Account_Flow",
                    "Description": "Test flow for Account",
                    "TriggerObjectOrEvent": {"QualifiedApiName": "Account"},
                    "ProcessType": "AutoLaunchedFlow",
                    "Status": "Active"
                }
            ]
        }
    }
    
    mock_triggers_response = {
        "result": {
            "records": [
                {
                    "Name": "AccountTrigger",
                    "TableEnumOrId": "Account",
                    "Body": "trigger AccountTrigger on Account (before insert) {\n    // Test trigger\n}",
                    "Status": "Active"
                }
            ]
        }
    }
    
    mock_validation_response = {"result": {"records": []}}
    mock_workflow_response = {"result": {"records": []}}
    
    # Mock the run_sf function
    with patch('src.pipeline.build_schema_library_end_to_end.run_sf') as mock_run_sf:
        def mock_run_sf_side_effect(args, org=""):
            print(f"Mock args: {args}")
            # Find the query in the args
            query = ""
            for i, arg in enumerate(args):
                if arg == "--query" and i + 1 < len(args):
                    query = args[i + 1]
                    break
            
            print(f"Mock query: {query}")
            if "Flow" in query:
                return json.dumps(mock_flows_response)
            elif "ApexTrigger" in query:
                return json.dumps(mock_triggers_response)
            elif "ValidationRule" in query:
                return json.dumps(mock_validation_response)
            elif "WorkflowRule" in query:
                return json.dumps(mock_workflow_response)
            else:
                return json.dumps({"result": {"records": []}})
        
        mock_run_sf.side_effect = mock_run_sf_side_effect
        
        # Test the function
        result = get_all_automation_data_batched("test_org", test_objects)
        
        print(f"Result keys: {list(result.keys())}")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Verify results
        if "Account" in result:
            print("✅ Account found in results")
            account_data = result["Account"]
            print(f"Account flows: {len(account_data['flows'])}")
            print(f"Account triggers: {len(account_data['triggers'])}")
        else:
            print("❌ Account not found in results")
        
        if "Contact" in result:
            print("✅ Contact found in results")
        else:
            print("❌ Contact not found in results")
        
        return len(result) > 0

if __name__ == "__main__":
    success = test_simple_batching()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")

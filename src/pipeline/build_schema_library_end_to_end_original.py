#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
End-to-end Salesforce schema → LLM corpus builder.

What it does (single command):
 1) Fetch: list SObjects and describe each (resume-friendly, retries, throttle)
 2) Combine describes → schema.json
 3) Split/annotate → objects/*.json (+ relationships-index.json, edges/nodes CSVs)
 4) (optional) Stats → per-object counts + sampled field fill-rates
 5) (optional) Automation → flows, triggers, field-level security, audit history, code complexity, data quality, and user adoption for each object (Tooling API)
 6) (optional) Emit Markdown and/or JSONL chunks for vector DB ingestion

Requires: Salesforce CLI (sf) installed and an authenticated alias (e.g., TP).
Works on Windows/macOS/Linux; supports running PowerShell shim (sf.ps1).

Environment Variables:
  SF_ORG_ALIAS: Set this environment variable to specify the Salesforce org alias.
                This can be set in your shell or in a .env file.
                
                PowerShell: $env:SF_ORG_ALIAS="DEVNEW"
                Bash/Zsh:   export SF_ORG_ALIAS=DEVNEW
                
                The script will use this value as the default if --org-alias is not provided.
                You can still override with --org-alias if needed.

Example usage:
  # Using environment variable (recommended)
  $env:SF_ORG_ALIAS="DEVNEW"  # PowerShell
  python build_schema_library_end_to_end.py --with-stats
  
  # Using command line argument (overrides env var)
  python build_schema_library_end_to_end.py --org-alias PROD --with-stats
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass  # .env loading is optional on servers that use real env vars

# Pinecone imports
from typing import Iterable
try:
    from openai import OpenAI
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: openai or pinecone-client not installed. Pinecone upload will be skipped.")

# Token counting imports
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not installed. Using character-based token estimation.")

# ----------------------------
# CLI resolution & helpers
# ----------------------------

SF_BIN: Optional[str] = None  # set in main()


def resolve_sf(sf_path_opt: str = "") -> str:
    """Resolve path to Salesforce CLI executable/shim."""
    if sf_path_opt:
        p = Path(sf_path_opt)
        if p.exists():
            return str(p)
        raise SystemExit(f"--sf-path '{sf_path_opt}' doesn't exist.")
    # Try common names via PATH (include PowerShell shims)
    for name in [
        "sf.cmd",
        "sf.exe",
        "sf.ps1",
        "sf",
        "sfdx.cmd",
        "sfdx.exe",
        "sfdx.ps1",
        "sfdx",
    ]:
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit(
        "Could not locate Salesforce CLI. Provide --sf-path, or ensure 'sf' is on PATH.\n"
        "PowerShell tip:  Get-Command sf | Select-Object -ExpandProperty Source"
    )


def run_sf(args: List[str], env: Optional[Dict[str, str]] = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Run an sf CLI command robustly on Windows/macOS/Linux."""
    if not SF_BIN:
        raise RuntimeError("SF_BIN not initialized")

    # On Windows, handle shim types explicitly
    if SF_BIN.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd", "/c", SF_BIN] + args
    elif SF_BIN.lower().endswith(".ps1"):
        # Prefer PowerShell 7 (pwsh) if available; fall back to Windows PowerShell
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if not pwsh:
            raise SystemExit("Cannot find PowerShell to run sf.ps1 (looked for 'pwsh' and 'powershell').")
        cmd = [pwsh, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", SF_BIN] + args
    else:
        # Native executable on *nix or Windows
        cmd = [SF_BIN] + args

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def safe_json_load(s: str) -> Optional[Any]:
    """Parse JSON safely; tolerate stray whitespace/BOM. Return None on error."""
    if s is None:
        return None
    try:
        return json.loads(s)
    except Exception:
        # try utf-8-sig removal
        try:
            return json.loads(s.encode("utf-8").decode("utf-8-sig"))
        except Exception:
            return None


# ----------------------------
# Namespaces & noise
# ----------------------------

DEFAULT_API_VERSIONS = ["64.0", "63.0", "62.0", "61.0"]

NOISE_SUFFIXES = ("ChangeEvent", "Feed", "History", "Share", "FieldHistory", "EventRelation")
NOISE_EXACT = {"ActivityHistory", "AggregateResult", "OpenActivity", "TaskRelation"}


def is_noise_object(name: str) -> bool:
    return name in NOISE_EXACT or any(name.endswith(s) for s in NOISE_SUFFIXES)


def namespace_of(api_name: str) -> str:
    """Return namespace from api name like 'ns__Object__c' else ''."""
    parts = api_name.split("__")
    # e.g., ['npsp','Something','c'] -> namespace 'npsp'
    if len(parts) >= 3:
        return parts[0]
    return ""


def is_ignored_namespace(api_name: str, ignore: Set[str]) -> bool:
    ns = namespace_of(api_name)
    return ns in ignore if ns else False


# ----------------------------
# Fetch phase
# ----------------------------


def list_sobjects(org: str) -> List[str]:
    """Get full SObject name list from org (modern, then legacy)."""
    code, out, _ = run_sf(["schema", "sobject", "list", "--target-org", org, "--json"])
    data = safe_json_load(out) if code == 0 else None
    if data and "result" in data:
        return list(data["result"])
    code, out, _ = run_sf(["force", "schema", "sobject", "list", "--target-org", org, "--sobject", "all", "--json"])
    data = safe_json_load(out) if code == 0 else None
    if not data or "result" not in data:
        raise SystemExit("Failed to list SObjects from org; try `sf org list` and re-auth.")
    return list(data["result"])


def describe_one(org: str, name: str, api_versions: List[str]) -> Optional[dict]:
    """Describe an SObject using several fallbacks; return inner describe dict or None."""
    attempts: List[List[str]] = [
        ["schema", "sobject", "describe", "--target-org", org, "--sobject", name, "--json"],
        ["force", "schema", "sobject", "describe", "--target-org", org, "--sobject", name, "--json"],
    ]
    for v in api_versions:
        attempts.append(["schema", "sobject", "describe", "--target-org", org, "--sobject", name, "--api-version", v, "--json"])
    for v in api_versions:
        attempts.append(["force", "schema", "sobject", "describe", "--target-org", org, "--sobject", name, "--api-version", v, "--json"])

    for cmd in attempts:
        code, out, _ = run_sf(cmd)
        if code != 0 or not out:
            continue
        j = safe_json_load(out)
        if not j:
            continue
        if isinstance(j, dict) and "result" in j and isinstance(j["result"], dict):
            return j["result"]
        if isinstance(j, dict) and j.get("name"):
            return j
    return None


@dataclass
class FetchConfig:
    org: str
    out_root: Path
    prefilter_noise: bool
    prefilter_namespaces: Set[str]
    throttle_ms: int
    retries: int
    backoff_ms: int
    max_objects: Optional[int]
    resume: bool
    mode: str  # 'all' | 'seeds'
    seeds: List[str]
    depth: int
    api_versions: List[str]


def fetch_describes(cfg: FetchConfig) -> Tuple[List[str], List[str]]:
    """Fetch describes into out_root/raw/*.json. Returns (all_names_considered, errors_list)."""
    raw_dir = cfg.out_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if cfg.mode == "all":
        full_list = list_sobjects(cfg.org)
        names = []
        for n in full_list:
            if cfg.prefilter_noise and is_noise_object(n):
                continue
            if cfg.prefilter_namespaces and is_ignored_namespace(n, cfg.prefilter_namespaces):
                continue
            names.append(n)
        if cfg.max_objects is not None:
            names = names[: cfg.max_objects]
    else:
        if not cfg.seeds:
            raise SystemExit("--seeds required when --fetch=seeds")
        full_list = list_sobjects(cfg.org)
        seed_set = [s for s in cfg.seeds if s in full_list]
        if not seed_set:
            raise SystemExit("None of the provided --seeds exist in org.")
        names_seen: Set[str] = set()
        q: deque = deque()
        for s in seed_set:
            q.append((s, 0))
            names_seen.add(s)

        def neighbors(desc: dict) -> Set[str]:
            out: Set[str] = set()
            for f in desc.get("fields", []):
                if f.get("type") == "reference":
                    out.update(f.get("referenceTo") or [])
            for cr in desc.get("childRelationships", []):
                child = cr.get("childSObject")
                if child:
                    out.add(child)
            return out

        print(f"Neighborhood crawl: seeds={seed_set}, depth={cfg.depth}")
        while q:
            name, d = q.popleft()
            if cfg.prefilter_namespaces and is_ignored_namespace(name, cfg.prefilter_namespaces):
                continue
            target_path = raw_dir / f"{name}.json"
            desc_obj = None
            if cfg.resume and target_path.exists():
                try:
                    desc_obj = json.loads(target_path.read_text(encoding="utf-8"))
                except Exception:
                    desc_obj = None
            if not desc_obj:
                attempt = 0
                while attempt <= cfg.retries:
                    desc_obj = describe_one(cfg.org, name, cfg.api_versions)
                    if desc_obj:
                        break
                    attempt += 1
                    time.sleep((cfg.backoff_ms * (2 ** (attempt - 1))) / 1000.0)
                if desc_obj:
                    target_path.write_text(json.dumps(desc_obj, ensure_ascii=False, indent=2), encoding="utf-8")
                    if cfg.throttle_ms > 0:
                        time.sleep(cfg.throttle_ms / 1000.0)
                else:
                    print(f"  !! Failed to describe {name}")
                    continue
            if d < cfg.depth:
                for n in neighbors(desc_obj):
                    if cfg.prefilter_noise and is_noise_object(n):
                        continue
                    if cfg.prefilter_namespaces and is_ignored_namespace(n, cfg.prefilter_namespaces):
                        continue
                    if n not in names_seen:
                        names_seen.add(n)
                        q.append((n, d + 1))
        names = sorted(names_seen)

    errors: List[str] = []
    total = len(names)
    print(f"Describing {total} objects (prefilter_noise={cfg.prefilter_noise}, resume={cfg.resume})...")
    
    # Process in batches to avoid overwhelming the API
    BATCH_SIZE = 50
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch_names = names[batch_start:batch_end]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch_names)} objects)...")
        
        for i, name in enumerate(batch_names, 1):
            out_path = raw_dir / f"{name}.json"
            if cfg.resume and out_path.exists():
                continue
            attempt = 0
            desc = None
            while attempt <= cfg.retries:
                try:
                    desc = describe_one(cfg.org, name, cfg.api_versions)
                    if desc:
                        break
                except subprocess.TimeoutExpired:
                    if attempt < cfg.retries:
                        wait_time = (cfg.backoff_ms * (2 ** attempt)) / 1000.0
                        print(f"    Timeout on attempt {attempt + 1}, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"    ❌ Timeout after {cfg.retries + 1} attempts for {name}")
                        errors.append(name)
                        break
                except Exception as e:
                    if attempt < cfg.retries:
                        wait_time = (cfg.backoff_ms * (2 ** attempt)) / 1000.0
                        print(f"    Error on attempt {attempt + 1}: {e}, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"    ❌ Failed after {cfg.retries + 1} attempts for {name}: {e}")
                        errors.append(name)
                        break
                attempt += 1
            if desc:
                out_path.write_text(json.dumps(desc, ensure_ascii=False, indent=2), encoding="utf-8")
                if cfg.throttle_ms > 0:
                    time.sleep(cfg.throttle_ms / 1000.0)
            if (batch_start + i) % 25 == 0:
                print(f"  … {batch_start + i}/{total} processed")
        
        # Add a longer pause between batches to avoid rate limiting
        if batch_end < total:
            print(f"Pausing 30 seconds between batches...")
            time.sleep(30)
    
    if errors:
        (raw_dir / "_errors.log").write_text("\n".join(errors), encoding="utf-8")
    (cfg.out_root / "sobject-list.json").write_text(
        json.dumps({"result": names}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return names, errors


# ----------------------------
# SOQL helpers (stats)
# ----------------------------


def soql_query(org: str, soql: str, timeout: int = 180) -> Tuple[int, Optional[dict]]:
    """Run a SOQL query via sf data query; return (exit_code, result_dict_or_None)."""
    code, out, _ = run_sf(["data", "query", "--target-org", org, "--json", "--query", soql], timeout=timeout)
    data = safe_json_load(out) if code == 0 else None
    if data and isinstance(data, dict) and "result" in data:
        return code, data["result"]
    return code, None


def tooling_query(org: str, soql: str, timeout: int = 180) -> Tuple[int, Optional[dict]]:
    """Run a SOQL query via sf data query with tooling API; return (exit_code, result_dict_or_None)."""
    code, out, _ = run_sf(["data", "query", "--target-org", org, "--json", "--query", soql, "--tooling-api"], timeout=timeout)
    data = safe_json_load(out) if code == 0 else None
    if data and isinstance(data, dict) and "result" in data:
        return code, data["result"]
    return code, None


def get_automation_dependencies(org: str, sobject_name: str) -> dict:
    """Get automation dependencies (flows and triggers) for a Salesforce object."""
    flows = []
    triggers = []
    
    # Query 1: Flows
    flow_query = f"SELECT Name, Description FROM Flow WHERE ProcessType = 'AutoLaunchedFlow' AND TriggerObjectOrEvent.QualifiedApiName = '{sobject_name}'"
    code, flow_result = tooling_query(org, flow_query)
    if code == 0 and flow_result and isinstance(flow_result.get("records"), list):
        flows = [record.get("Name") for record in flow_result["records"] if record.get("Name")]
    
    # Query 2: Apex Triggers
    trigger_query = f"SELECT Name FROM ApexTrigger WHERE TableEnumOrId = '{sobject_name}'"
    code, trigger_result = tooling_query(org, trigger_query)
    if code == 0 and trigger_result and isinstance(trigger_result.get("records"), list):
        triggers = [record.get("Name") for record in trigger_result["records"] if record.get("Name")]
    
    return {"flows": flows, "triggers": triggers}


def get_field_level_security(org: str, sobject_name: str) -> dict:
    """Get field-level security permissions for a Salesforce object."""
    fls_data = {}
    
    # Query FieldPermissions for the entire object
    fls_query = f"SELECT Field, PermissionSet.Label, PermissionsEdit, PermissionsRead FROM FieldPermissions WHERE SobjectType = '{sobject_name}'"
    code, fls_result = tooling_query(org, fls_query)
    
    if code == 0 and fls_result and isinstance(fls_result.get("records"), list):
        for record in fls_result["records"]:
            field_name = record.get("Field")
            permission_set_label = record.get("PermissionSet", {}).get("Label")
            can_edit = record.get("PermissionsEdit", False)
            can_read = record.get("PermissionsRead", False)
            
            if field_name and permission_set_label:
                # Extract just the field name (remove object prefix)
                # Field format is "ObjectName.FieldName" (e.g., "Account.Amount__c")
                if "." in field_name:
                    field_name = field_name.split(".", 1)[1]
                
                # Initialize field entry if it doesn't exist
                if field_name not in fls_data:
                    fls_data[field_name] = {"editable_by": [], "readonly_by": []}
                
                # Add permission set to appropriate list
                if can_edit:
                    fls_data[field_name]["editable_by"].append(permission_set_label)
                elif can_read:
                    fls_data[field_name]["readonly_by"].append(permission_set_label)
    
    return fls_data


def get_custom_field_history(org: str, sobject_name: str) -> dict:
    """Get audit history for custom fields on a Salesforce object."""
    history_data = {}
    
    # Query CustomField for the entire object
    history_query = f"SELECT DeveloperName, CreatedBy.Name, CreatedDate, LastModifiedBy.Name, LastModifiedDate FROM CustomField WHERE TableEnumOrId = '{sobject_name}'"
    code, history_result = tooling_query(org, history_query)
    
    if code == 0 and history_result and isinstance(history_result.get("records"), list):
        for record in history_result["records"]:
            field_name = record.get("DeveloperName")
            created_by = record.get("CreatedBy", {}).get("Name")
            created_date = record.get("CreatedDate")
            last_modified_by = record.get("LastModifiedBy", {}).get("Name")
            last_modified_date = record.get("LastModifiedDate")
            
            if field_name:
                history_data[field_name] = {
                    "created_by": created_by,
                    "created_date": created_date,
                    "last_modified_by": last_modified_by,
                    "last_modified_date": last_modified_date
                }
    
    return history_data


def get_code_complexity(org: str, sobject_name: str) -> dict:
    """Get code complexity metrics for automation related to an SObject."""
    complexity_data = {"triggers": [], "classes": []}
    
    # Query ApexTriggers for the object
    trigger_query = f"SELECT Name, Body FROM ApexTrigger WHERE TableEnumOrId = '{sobject_name}'"
    code, trigger_result = tooling_query(org, trigger_query)
    
    if code == 0 and trigger_result and isinstance(trigger_result.get("records"), list):
        for record in trigger_result["records"]:
            name = record.get("Name")
            body = record.get("Body", "")
            
            if name and body:
                # Calculate lines of code and comment lines
                lines = body.split('\n')
                total_lines = len(lines)
                comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*'))
                
                complexity_data["triggers"].append({
                    "name": name,
                    "total_lines": total_lines,
                    "comment_lines": comment_lines,
                    "code_lines": total_lines - comment_lines
                })
    
    # Query ApexClasses that might be related (this is a broader search)
    # Note: This is a simplified approach - in practice, you might want to analyze class relationships
    class_query = f"SELECT Name, Body FROM ApexClass WHERE Body LIKE '%{sobject_name}%'"
    code, class_result = tooling_query(org, class_query)
    
    if code == 0 and class_result and isinstance(class_result.get("records"), list):
        for record in class_result["records"]:
            name = record.get("Name")
            body = record.get("Body", "")
            
            if name and body:
                # Calculate lines of code and comment lines
                lines = body.split('\n')
                total_lines = len(lines)
                comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*'))
                
                complexity_data["classes"].append({
                    "name": name,
                    "total_lines": total_lines,
                    "comment_lines": comment_lines,
                    "code_lines": total_lines - comment_lines
                })
    
    return complexity_data


def get_data_quality_metrics(org: str, sobject_name: str, usage_summary: dict) -> dict:
    """Get data quality metrics for an object including picklist distributions and data freshness."""
    quality_data = {"picklist_distributions": {}, "data_freshness": None}
    
    # Get top 5 most-used picklist fields
    field_fill_rates = usage_summary.get("fieldFillRatesTop", [])
    picklist_fields = []
    
    for field_info in field_fill_rates:
        field_name = field_info.get("field")
        # This is a simplified approach - in practice, you'd need to check field type
        # For now, we'll assume fields ending with __c are likely picklists
        if field_name and field_name.endswith('__c'):
            picklist_fields.append(field_name)
            if len(picklist_fields) >= 5:
                break
    
    # Get picklist value distributions
    for field_name in picklist_fields:
        try:
            picklist_query = f"SELECT {field_name}, COUNT(Id) FROM {sobject_name} GROUP BY {field_name}"
            code, picklist_result = soql_query(org, picklist_query)
            
            if code == 0 and picklist_result and isinstance(picklist_result.get("records"), list):
                distribution = []
                for record in picklist_result["records"]:
                    value = record.get(field_name)
                    count = record.get("expr0")  # COUNT(Id) result
                    if value is not None and count is not None:
                        distribution.append({"value": value, "count": count})
                
                quality_data["picklist_distributions"][field_name] = distribution
        except Exception as e:
            # Skip fields that can't be queried
            continue
    
    # Calculate data freshness (percentage of records older than 2 years)
    try:
        from datetime import datetime, timedelta
        two_years_ago = datetime.now() - timedelta(days=2*365)
        two_years_ago_str = two_years_ago.strftime("%Y-%m-%d")
        
        freshness_query = f"SELECT COUNT(Id) FROM {sobject_name} WHERE LastModifiedDate < {two_years_ago_str}"
        code, freshness_result = soql_query(org, freshness_query)
        
        if code == 0 and freshness_result and isinstance(freshness_result.get("records"), list):
            old_records = freshness_result["records"][0].get("expr0", 0)
            total_records = usage_summary.get("objectCount", 0)
            
            if total_records > 0:
                quality_data["data_freshness"] = {
                    "old_records_count": old_records,
                    "total_records": total_records,
                    "percentage_old": (old_records / total_records) * 100
                }
    except Exception as e:
        # Skip if data freshness calculation fails
        pass
    
    return quality_data


def get_user_adoption_metrics(org: str, sobject_name: str) -> dict:
    """Get user adoption metrics by analyzing record ownership patterns."""
    adoption_data = {"top_owning_profiles": []}
    
    try:
        # Query for top owning profiles
        adoption_query = f"SELECT Owner.Profile.Name, COUNT(Id) FROM {sobject_name} GROUP BY Owner.Profile.Name ORDER BY COUNT(Id) DESC LIMIT 5"
        code, adoption_result = soql_query(org, adoption_query)
        
        if code == 0 and adoption_result and isinstance(adoption_result.get("records"), list):
            for record in adoption_result["records"]:
                profile_name = record.get("Owner", {}).get("Profile", {}).get("Name")
                count = record.get("expr0")  # COUNT(Id) result
                
                if profile_name and count is not None:
                    adoption_data["top_owning_profiles"].append({
                        "profile": profile_name,
                        "record_count": count
                    })
    except Exception as e:
        # Skip if user adoption query fails
        pass
    
    return adoption_data


def get_all_profiles(org: str) -> List[dict]:
    """Get all profiles in the org."""
    profiles = []
    try:
        # Query profiles using SOQL
        profile_query = "SELECT Id, Name, Description, UserType, UserLicenseId FROM Profile ORDER BY Name"
        code, result = soql_query(org, profile_query)
        if code == 0 and result and isinstance(result.get("records"), list):
            profiles = result["records"]
    except Exception as e:
        print(f"Failed to get profiles: {e}")
    return profiles


def get_all_permission_sets(org: str) -> List[dict]:
    """Get all permission sets in the org."""
    permission_sets = []
    try:
        ps_query = "SELECT Id, Name, Label, Description, IsOwnedByProfile FROM PermissionSet WHERE IsOwnedByProfile = false ORDER BY Name"
        code, result = soql_query(org, ps_query)
        if code == 0 and result and isinstance(result.get("records"), list):
            permission_sets = result["records"]
    except Exception as e:
        print(f"Failed to get permission sets: {e}")
    return permission_sets


def get_all_roles(org: str) -> List[dict]:
    """Get all roles in the org with hierarchy."""
    roles = []
    try:
        role_query = "SELECT Id, Name, DeveloperName, ParentRoleId, RollupDescription FROM UserRole ORDER BY Name"
        code, result = soql_query(org, role_query)
        if code == 0 and result and isinstance(result.get("records"), list):
            roles = result["records"]
    except Exception as e:
        print(f"Failed to get roles: {e}")
    return roles


def rest_api_query(org: str, endpoint: str, method: str = "GET", data: dict = None, timeout: int = 180) -> Tuple[int, Optional[dict]]:
    """
    Execute a REST API query via sf rest api command.
    
    Args:
        org: Salesforce org alias
        endpoint: REST API endpoint (e.g., "/services/data/v64.0/sobjects/Profile")
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Optional data for POST/PUT requests
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (exit_code, response_data_or_None)
    """
    try:
        cmd = ["rest", "api", "--target-org", org, "--json", "--method", method, "--endpoint", endpoint]
        
        if data and method in ["POST", "PUT", "PATCH"]:
            # Convert data to JSON string for the command
            import json
            data_str = json.dumps(data)
            cmd.extend(["--data", data_str])
        
        code, out, _ = run_sf(cmd, timeout=timeout)
        response_data = safe_json_load(out) if code == 0 else None
        
        return code, response_data
        
    except Exception as e:
        print(f"REST API query failed for {endpoint}: {e}")
        return 1, None


def get_metadata_via_rest(org: str, metadata_type: str, full_names: List[str] = None) -> List[dict]:
    """
    Get metadata using REST API for types not available via SOQL.
    
    Args:
        org: Salesforce org alias
        metadata_type: Type of metadata (e.g., "Profile", "PermissionSet", "CustomObject")
        full_names: Optional list of specific metadata names to retrieve
        
    Returns:
        List of metadata records
    """
    metadata_records = []
    
    try:
        # Build the endpoint
        endpoint = f"/services/data/v64.0/metadata/{metadata_type}"
        if full_names:
            # For specific metadata items
            endpoint += f"/{','.join(full_names)}"
        
        code, result = rest_api_query(org, endpoint)
        
        if code == 0 and result:
            # Handle different response formats
            if isinstance(result, list):
                metadata_records = result
            elif isinstance(result, dict) and "records" in result:
                metadata_records = result["records"]
            elif isinstance(result, dict):
                metadata_records = [result]
                
    except Exception as e:
        print(f"Failed to get {metadata_type} metadata via REST: {e}")
    
    return metadata_records


def get_object_permissions(org: str, profile_ids: List[str] = None, permission_set_ids: List[str] = None) -> List[dict]:
    """Get object-level permissions for profiles and permission sets."""
    # Note: ObjectPermissions table access is limited in many orgs
    # This function returns an empty list as a fallback
    print(f"    Note: ObjectPermissions access not available in this org")
    return []


def get_profile_field_permissions(org: str, sobject_name: str, profile_id: str) -> List[dict]:
    """Get field permissions for a specific profile and object."""
    field_permissions = []
    try:
        field_perm_query = f"""
        SELECT Id, Field, PermissionsRead, PermissionsEdit, PermissionsCreate, PermissionsDelete
        FROM FieldPermissions 
        WHERE SobjectType = '{sobject_name}' AND ParentId = '{profile_id}'
        ORDER BY Field
        """
        
        code, result = soql_query(org, field_perm_query)
        if code == 0 and result and isinstance(result.get("records"), list):
            field_permissions = result["records"]
    except Exception as e:
        print(f"Failed to get field permissions for {sobject_name} and profile {profile_id}: {e}")
    return field_permissions


def get_permission_set_field_permissions(org: str, sobject_name: str, permission_set_id: str) -> List[dict]:
    """Get field permissions for a specific permission set and object."""
    field_permissions = []
    try:
        field_perm_query = f"""
        SELECT Id, Field, PermissionsRead, PermissionsEdit, PermissionsCreate, PermissionsDelete
        FROM FieldPermissions 
        WHERE SobjectType = '{sobject_name}' AND ParentId = '{permission_set_id}'
        ORDER BY Field
        """
        
        code, result = soql_query(org, field_perm_query)
        if code == 0 and result and isinstance(result.get("records"), list):
            field_permissions = result["records"]
    except Exception as e:
        print(f"Failed to get field permissions for {sobject_name} and permission set {permission_set_id}: {e}")
    return field_permissions


def get_comprehensive_permissions(org: str, sobject_name: str, profile_ids: List[str] = None, permission_set_ids: List[str] = None) -> dict:
    """
    Get comprehensive permissions (object + field level) for profiles and permission sets.
    
    Returns a structured dictionary with object and field permissions.
    """
    permissions_data = {
        "object_permissions": [],
        "profile_field_permissions": {},
        "permission_set_field_permissions": {}
    }
    
    try:
        # Get object-level permissions
        obj_permissions = get_object_permissions(org, profile_ids, permission_set_ids)
        permissions_data["object_permissions"] = obj_permissions
        
        # Get field permissions for profiles
        if profile_ids:
            for profile_id in profile_ids:
                field_perms = get_profile_field_permissions(org, sobject_name, profile_id)
                permissions_data["profile_field_permissions"][profile_id] = field_perms
        
        # Get field permissions for permission sets
        if permission_set_ids:
            for ps_id in permission_set_ids:
                field_perms = get_permission_set_field_permissions(org, sobject_name, ps_id)
                permissions_data["permission_set_field_permissions"][ps_id] = field_perms
                
    except Exception as e:
        print(f"Failed to get comprehensive permissions for {sobject_name}: {e}")
    
    return permissions_data


def create_profile_markdown_summary(profiles: List[dict]) -> str:
    """Create a markdown summary of profiles."""
    if not profiles:
        return "# Profiles\n\nNo profiles found."
    
    markdown = "# Profiles\n\n"
    markdown += f"Total profiles: {len(profiles)}\n\n"
    
    # Group by user type
    user_types = {}
    for profile in profiles:
        user_type = profile.get('UserType', 'Unknown')
        if user_type not in user_types:
            user_types[user_type] = []
        user_types[user_type].append(profile)
    
    for user_type, type_profiles in user_types.items():
        markdown += f"## {user_type} Profiles ({len(type_profiles)})\n\n"
        
        for profile in sorted(type_profiles, key=lambda x: x.get('Name', '')):
            name = profile.get('Name', 'Unknown')
            description = profile.get('Description', '')
            
            markdown += f"### {name}\n\n"
            if description:
                markdown += f"{description}\n\n"
            
            # Add metadata
            metadata_items = []
            if profile.get('UserType'):
                metadata_items.append(f"**User Type:** {profile['UserType']}")
            if profile.get('UserLicenseId'):
                metadata_items.append(f"**License:** {profile['UserLicenseId']}")
            
            if metadata_items:
                markdown += "**Metadata:** " + " | ".join(metadata_items) + "\n\n"
        
        markdown += "---\n\n"
    
    return markdown


def create_permission_set_markdown_summary(permission_sets: List[dict]) -> str:
    """Create a markdown summary of permission sets."""
    if not permission_sets:
        return "# Permission Sets\n\nNo permission sets found."
    
    markdown = "# Permission Sets\n\n"
    markdown += f"Total permission sets: {len(permission_sets)}\n\n"
    
    # Group by ownership
    owned_by_profile = []
    custom_permission_sets = []
    
    for ps in permission_sets:
        if ps.get('IsOwnedByProfile', False):
            owned_by_profile.append(ps)
        else:
            custom_permission_sets.append(ps)
    
    if custom_permission_sets:
        markdown += f"## Custom Permission Sets ({len(custom_permission_sets)})\n\n"
        
        for ps in sorted(custom_permission_sets, key=lambda x: x.get('Name', '')):
            name = ps.get('Name', 'Unknown')
            label = ps.get('Label', name)
            description = ps.get('Description', '')
            
            markdown += f"### {label}\n\n"
            markdown += f"**API Name:** `{name}`\n\n"
            
            if description:
                markdown += f"{description}\n\n"
        
        markdown += "---\n\n"
    
    if owned_by_profile:
        markdown += f"## Profile-Owned Permission Sets ({len(owned_by_profile)})\n\n"
        markdown += "*These permission sets are automatically created and owned by profiles.*\n\n"
        
        for ps in sorted(owned_by_profile, key=lambda x: x.get('Name', '')):
            name = ps.get('Name', 'Unknown')
            label = ps.get('Label', name)
            
            markdown += f"- **{label}** (`{name}`)\n"
        
        markdown += "\n---\n\n"
    
    return markdown


def create_role_markdown_summary(roles: List[dict]) -> str:
    """Create a markdown summary of roles with hierarchy."""
    if not roles:
        return "# Roles\n\nNo roles found."
    
    markdown = "# Roles\n\n"
    markdown += f"Total roles: {len(roles)}\n\n"
    
    # Build hierarchy
    role_dict = {role.get('Id'): role for role in roles}
    parent_children = {}
    
    for role in roles:
        parent_id = role.get('ParentRoleId')
        if parent_id and parent_id in role_dict:
            if parent_id not in parent_children:
                parent_children[parent_id] = []
            parent_children[parent_id].append(role.get('Id'))
    
    # Find root roles (no parent)
    root_roles = [role for role in roles if not role.get('ParentRoleId') or role.get('ParentRoleId') not in role_dict]
    
    def print_role_hierarchy(role_id, level=0):
        role = role_dict.get(role_id)
        if not role:
            return ""
        
        indent = "  " * level
        name = role.get('Name', 'Unknown')
        dev_name = role.get('DeveloperName', '')
        rollup_desc = role.get('RollupDescription', '')
        
        result = f"{indent}- **{name}**"
        if dev_name and dev_name != name:
            result += f" (`{dev_name}`)"
        result += "\n"
        
        if rollup_desc:
            result += f"{indent}  *{rollup_desc}*\n"
        
        # Add children
        children = parent_children.get(role_id, [])
        for child_id in sorted(children, key=lambda x: role_dict.get(x, {}).get('Name', '')):
            result += print_role_hierarchy(child_id, level + 1)
        
        return result
    
    markdown += "## Role Hierarchy\n\n"
    
    for root_role in sorted(root_roles, key=lambda x: x.get('Name', '')):
        markdown += print_role_hierarchy(root_role.get('Id'))
    
    markdown += "\n---\n\n"
    
    # Add flat list for reference
    markdown += "## All Roles (Alphabetical)\n\n"
    
    for role in sorted(roles, key=lambda x: x.get('Name', '')):
        name = role.get('Name', 'Unknown')
        dev_name = role.get('DeveloperName', '')
        rollup_desc = role.get('RollupDescription', '')
        parent_id = role.get('ParentRoleId')
        
        markdown += f"### {name}\n\n"
        
        if dev_name and dev_name != name:
            markdown += f"**Developer Name:** `{dev_name}`\n\n"
        
        if rollup_desc:
            markdown += f"**Description:** {rollup_desc}\n\n"
        
        if parent_id and parent_id in role_dict:
            parent_name = role_dict[parent_id].get('Name', 'Unknown')
            markdown += f"**Parent Role:** {parent_name}\n\n"
    
    return markdown


def build_metadata_markdown(profiles: List[dict], permission_sets: List[dict], 
                          roles: List[dict], object_permissions: List[dict]) -> str:
    """Build comprehensive metadata documentation."""
    parts = []
    
    # Header
    parts.append("# Salesforce Org Metadata Overview")
    parts.append("")
    parts.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    parts.append("")
    
    # Profile summary
    parts.append("## Profiles")
    parts.append("")
    parts.append(f"Total profiles: {len(profiles)}")
    parts.append("")
    parts.append("| Profile Name | User Type | Description |")
    parts.append("|---|---|---|")
    for prof in profiles[:20]:  # Top 20
        parts.append(
            f"| {md_escape(prof.get('Name', ''))} | "
            f"{md_escape(prof.get('UserType', ''))} | "
            f"{md_escape(prof.get('Description', '') or 'N/A')} |"
        )
    parts.append("")
    
    # Permission sets summary
    parts.append("## Permission Sets")
    parts.append("")
    parts.append(f"Total permission sets: {len(permission_sets)}")
    parts.append("")
    parts.append("| Permission Set | Label | Description |")
    parts.append("|---|---|---|")
    for ps in permission_sets[:20]:  # Top 20
        parts.append(
            f"| {md_escape(ps.get('Name', ''))} | "
            f"{md_escape(ps.get('Label', ''))} | "
            f"{md_escape(ps.get('Description', '') or 'N/A')} |"
        )
    parts.append("")
    
    # Role hierarchy
    parts.append("## Role Hierarchy")
    parts.append("")
    parts.append(f"Total roles: {len(roles)}")
    parts.append("")
    
    # Build role tree
    role_map = {r.get('Id'): r for r in roles}
    root_roles = [r for r in roles if not r.get('ParentRoleId')]
    
    def build_role_tree(role, indent=0):
        tree_parts = []
        tree_parts.append("  " * indent + f"- {role.get('Name')}")
        # Find children
        children = [r for r in roles if r.get('ParentRoleId') == role.get('Id')]
        for child in children:
            tree_parts.extend(build_role_tree(child, indent + 1))
        return tree_parts
    
    for root in root_roles[:10]:  # Limit to avoid huge trees
        parts.extend(build_role_tree(root))
    parts.append("")
    
    # Permission matrix
    if object_permissions:
        parts.append("## Object Permission Matrix")
        parts.append("")
        parts.append("This matrix shows which profiles and permission sets have access to which objects.")
        parts.append("")
        
        # Group permissions by object
        obj_perms = {}
        for perm in object_permissions:
            obj_name = perm.get('SobjectType', 'Unknown')
            if obj_name not in obj_perms:
                obj_perms[obj_name] = []
            obj_perms[obj_name].append(perm)
        
        # Show top objects by permission count
        top_objects = sorted(obj_perms.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        
        for obj_name, perms in top_objects:
            parts.append(f"### {obj_name}")
            parts.append("")
            parts.append("| Profile/Permission Set | Create | Read | Edit | Delete | View All | Modify All |")
            parts.append("|---|---|---|---|---|---|---|")
            
            for perm in perms[:15]:  # Limit to avoid huge tables
                parent_id = perm.get('ParentId', '')
                # Try to find profile or permission set name
                profile_name = next((p.get('Name') for p in profiles if p.get('Id') == parent_id), 'Unknown')
                ps_name = next((ps.get('Name') for ps in permission_sets if ps.get('Id') == parent_id), '')
                
                name = profile_name if profile_name != 'Unknown' else ps_name
                if name:
                    parts.append(
                        f"| {md_escape(name)} | "
                        f"{'✓' if perm.get('PermissionsCreate') else '✗'} | "
                        f"{'✓' if perm.get('PermissionsRead') else '✗'} | "
                        f"{'✓' if perm.get('PermissionsEdit') else '✗'} | "
                        f"{'✓' if perm.get('PermissionsDelete') else '✗'} | "
                        f"{'✓' if perm.get('PermissionsViewAllRecords') else '✗'} | "
                        f"{'✓' if perm.get('PermissionsModifyAllRecords', False) else '✗'} |"
                    )
            parts.append("")
    
    return "\n".join(parts)


def emit_metadata_corpus(metadata_dir: Path, md_out_dir: Path, emit_jsonl: bool, org_alias: str = "DEVNEW") -> Tuple[int, int]:
    """Generate metadata corpus for vector DB."""
    md_count = 0
    chunks = []
    
    # Read metadata files
    profiles_path = metadata_dir / "profiles.json"
    ps_path = metadata_dir / "permission_sets.json"
    roles_path = metadata_dir / "roles.json"
    
    if not all(p.exists() for p in [profiles_path, ps_path, roles_path]):
        return 0, 0
    
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    permission_sets = json.loads(ps_path.read_text(encoding="utf-8"))
    roles = json.loads(roles_path.read_text(encoding="utf-8"))
    
    # Get object permissions for all profiles and permission sets
    profile_ids = [p.get('Id') for p in profiles if p.get('Id')]
    ps_ids = [ps.get('Id') for ps in permission_sets if ps.get('Id')]
    
    # Note: We'll implement batching here as there might be limits
    # For now, we'll get permissions in batches
    object_permissions = []
    
    # Note: ObjectPermissions access is limited in many orgs
    # We'll create cross-reference chunks based on available metadata instead
    print(f"  Note: Creating cross-reference chunks based on available metadata...")
    
    # Save object permissions for cross-reference chunks
    if object_permissions:
        (metadata_dir / "object_permissions.json").write_text(
            json.dumps(object_permissions, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✓ Saved {len(object_permissions)} object permissions")
    
    # Generate comprehensive markdown
    md_content = build_metadata_markdown(profiles, permission_sets, roles, object_permissions)
    md_path = md_out_dir / "org_metadata.md"
    md_path.write_text(md_content, encoding="utf-8")
    md_count = 1
    
    if emit_jsonl:
        # Create chunks for different sections
        base_meta = {
            "source": "metadata",
            "type": "org_configuration"
        }
        
        # Profile chunks
        for profile in profiles:
            chunks.append({
                "id": f"profile:{profile.get('Name')}",
                "object": "Profile",
                "section": "profile_details",
                "text": f"Profile: {profile.get('Name')}, Type: {profile.get('UserType')}, "
                       f"Description: {profile.get('Description', 'N/A')}",
                "metadata": {**base_meta, "profileName": profile.get('Name')}
            })
        
        # Permission set chunks
        for ps in permission_sets:
            chunks.append({
                "id": f"permission_set:{ps.get('Name')}",
                "object": "PermissionSet",
                "section": "permission_set_details",
                "text": f"Permission Set: {ps.get('Name')}, Label: {ps.get('Label')}, "
                       f"Description: {ps.get('Description', 'N/A')}",
                "metadata": {**base_meta, "permissionSetName": ps.get('Name')}
            })
        
        # Role chunks with hierarchy context
        for role in roles:
            parent_name = "None"
            if role.get('ParentRoleId'):
                parent = next((r for r in roles if r.get('Id') == role.get('ParentRoleId')), None)
                if parent:
                    parent_name = parent.get('Name')
            
            chunks.append({
                "id": f"role:{role.get('DeveloperName')}",
                "object": "UserRole",
                "section": "role_hierarchy",
                "text": f"Role: {role.get('Name')}, Parent: {parent_name}, "
                       f"Description: {role.get('RollupDescription', 'N/A')}",
                "metadata": {**base_meta, "roleName": role.get('Name'), "parentRole": parent_name}
            })
        
        # Object permission chunks
        for perm in object_permissions:
            obj_name = perm.get('SobjectType', 'Unknown')
            parent_id = perm.get('ParentId', '')
            
            # Find profile or permission set name
            profile_name = next((p.get('Name') for p in profiles if p.get('Id') == parent_id), '')
            ps_name = next((ps.get('Name') for ps in permission_sets if ps.get('Id') == parent_id), '')
            
            access_name = profile_name if profile_name else ps_name
            access_type = "Profile" if profile_name else "PermissionSet"
            
            if access_name:
                perm_text = f"{access_type}: {access_name} has access to {obj_name}. "
                perm_text += f"Create: {perm.get('PermissionsCreate', False)}, "
                perm_text += f"Read: {perm.get('PermissionsRead', False)}, "
                perm_text += f"Edit: {perm.get('PermissionsEdit', False)}, "
                perm_text += f"Delete: {perm.get('PermissionsDelete', False)}, "
                perm_text += f"View All: {perm.get('PermissionsViewAllRecords', False)}, "
                perm_text += f"Modify All: {perm.get('PermissionsModifyAllRecords', False)}"
                
                chunks.append({
                    "id": f"permission:{access_type}:{access_name}:{obj_name}",
                    "object": "ObjectPermission",
                    "section": "object_access",
                    "text": perm_text,
                    "metadata": {
                        **base_meta,
                        "accessType": access_type,
                        "accessName": access_name,
                        "objectName": obj_name,
                        "permissions": {
                            "create": perm.get('PermissionsCreate', False),
                            "read": perm.get('PermissionsRead', False),
                            "edit": perm.get('PermissionsEdit', False),
                            "delete": perm.get('PermissionsDelete', False),
                            "viewAll": perm.get('PermissionsViewAllRecords', False),
                            "modifyAll": perm.get('PermissionsModifyAllRecords', False)
                        }
                    }
                })
    
    # Write JSONL
    jsonl_written = 0
    if chunks and emit_jsonl:
        jsonl_path = md_out_dir / "metadata_chunks.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                jsonl_written += 1
    
    return md_count, jsonl_written


def count_records(org: str, sobject: str) -> Optional[int]:
    code, res = soql_query(org, f"SELECT COUNT() FROM {sobject}")
    if code == 0 and res and isinstance(res.get("totalSize"), int):
        return int(res["totalSize"])
    return None


def sample_records(org: str, sobject: str, limit_n: int, order_by: Optional[str]) -> List[dict]:
    """
    Try SELECT FIELDS(ALL) first; if that fails, returns [].
    (We may fallback later to a trimmed explicit field list.)
    """
    clauses = []
    if order_by:
        clauses.append(f"ORDER BY {order_by}")
    clauses.append(f"LIMIT {int(limit_n)}")
    suffix = " ".join(clauses)

    # Attempt FIELDS(ALL)
    code, res = soql_query(org, f"SELECT FIELDS(ALL) FROM {sobject} {suffix}")
    if code == 0 and res and isinstance(res.get("records"), list):
        return res["records"]

    return []


# ----------------------------
# Split/annotate phase
# ----------------------------


def summarize_object(obj: dict) -> dict:
    fields = obj.get("fields", [])
    name_field = next((f.get("name") for f in fields if f.get("name")), None)
    type_counts = Counter(f.get("type") for f in fields if f.get("type"))
    return {
        "label": obj.get("label"),
        "custom": obj.get("custom"),
        "createable": obj.get("createable"),
        "deletable": obj.get("deletable"),
        "queryable": obj.get("queryable"),
        "nameField": name_field,
        "fieldTypeCounts": dict(type_counts),
    }


def write_edges(rel_summaries: dict, out_root: Path, filename: str = "edges.csv") -> None:
    rows = []
    for src, rs in rel_summaries.items():
        for ob in rs.get("outbound", []):
            rows.append([
                src,
                ob.get("viaField"),
                ob.get("toObject"),
                ob.get("relationshipType"),
                "true" if ob.get("polymorphic") else "false",
                (ob.get("relationshipExtraInfo") or ""),
            ])
    rows.sort(key=lambda r: (r[0] or "", r[1] or "", r[2] or ""))
    with (out_root / filename).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "field", "target", "type", "polymorphic", "extraInfo"])
        w.writerows(rows)


def write_nodes(rel_summaries: dict, objects_by_name: dict, included: Set[str], out_root: Path, filename: str) -> None:
    rows = []
    for name, rs in rel_summaries.items():
        out_full = rs.get("outbound", [])
        in_full = rs.get("inbound", [])
        out_clean = [e for e in out_full if e.get("toObject") in included]
        in_clean = [e for e in in_full if e.get("fromObject") in included]
        poly_out = sum(1 for e in out_full if e.get("polymorphic"))
        summary = summarize_object(objects_by_name.get(name, {}))
        rows.append([
            name,
            summary.get("label"),
            "true" if summary.get("custom") else "false",
            summary.get("nameField") or "",
            json.dumps(summary.get("fieldTypeCounts", {}), ensure_ascii=False),
            len(out_full),
            len(in_full),
            poly_out,
            len(out_clean),
            len(in_clean),
            "true" if rs.get("isLikelyJunction") else "false",
        ])
    rows.sort(key=lambda r: r[0].lower())
    with (out_root / filename).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "object",
            "label",
            "custom",
            "nameField",
            "fieldTypeCounts",
            "outbound_count",
            "inbound_count",
            "outbound_polymorphic_count",
            "outbound_clean_count",
            "inbound_clean_count",
            "isLikelyJunction",
        ])
        w.writerows(rows)


def write_sobject_lists(all_input_names, included_names, out_root: Path):
    (out_root / "sobject-list.json").write_text(
        json.dumps({"result": sorted(all_input_names)}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_root / "sobject-list.clean.json").write_text(
        json.dumps({"result": sorted(included_names)}, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_indexes(objects: List[dict]) -> Tuple[Dict, Dict]:
    outbound_index: Dict[str, list] = {}
    inbound_index: Dict[str, list] = {}
    for obj in objects:
        name = obj.get("name")
        if not name:
            continue
        # inbound (childRelationships)
        for cr in obj.get("childRelationships", []):
            inbound_index.setdefault(name, []).append(
                {
                    "childSObject": cr.get("childSObject"),
                    "field": cr.get("field"),
                    "relationshipName": cr.get("relationshipName"),
                    "cascadeDelete": cr.get("cascadeDelete", False),
                    "junctionIdListNames": cr.get("junctionIdListNames") or [],
                }
            )
        # outbound (reference fields)
        for f in obj.get("fields", []):
            if f.get("type") == "reference":
                outbound_index.setdefault(name, []).append(
                    {
                        "field": f.get("name"),
                        "targets": f.get("referenceTo") or [],
                        "polymorphic": len(f.get("referenceTo") or []) > 1,
                        "extraTypeInfo": f.get("extraTypeInfo"),
                    }
                )
    return outbound_index, inbound_index


def infer_relationship_type_from_inbound(inbound_index: Dict, src_obj: str, field_name: str, target_obj: str) -> str:
    for rel in inbound_index.get(target_obj, []):
        if rel.get("childSObject") == src_obj and rel.get("field") == field_name:
            return "Master-Detail" if rel.get("cascadeDelete") else "Lookup"
    return "Lookup"


def is_likely_junction(obj_name: str, inbound_index: Dict) -> bool:
    parents = {
        parent
        for parent, rels in inbound_index.items()
        if any(r.get("childSObject") == obj_name and r.get("cascadeDelete") for r in rels)
    }
    return len(parents) >= 2


def build_relationships(objects: List[dict]) -> Dict[str, dict]:
    name_to_obj = {o["name"]: o for o in objects if isinstance(o, dict) and o.get("name")}
    outbound_index, inbound_index = build_indexes(objects)
    summaries: Dict[str, dict] = {}
    for obj_name in name_to_obj:
        outbound = []
        for entry in outbound_index.get(obj_name, []):
            field_name = entry["field"]
            for tgt in entry["targets"]:
                rtype = infer_relationship_type_from_inbound(inbound_index, obj_name, field_name, tgt)
                outbound.append(
                    {
                        "toObject": tgt,
                        "viaField": field_name,
                        "relationshipType": rtype,
                        "polymorphic": entry.get("polymorphic", False),
                        "relationshipExtraInfo": entry.get("extraTypeInfo"),
                        "sentence": f"This object ('{obj_name}') has a {rtype} relationship TO the '{tgt}' object via the '{field_name}' field.",
                    }
                )
        inbound = []
        for cr in inbound_index.get(obj_name, []):
            child = cr.get("childSObject")
            field_name = cr.get("field")
            rtype = "Master-Detail" if cr.get("cascadeDelete") else "Lookup"
            inbound.append(
                {
                    "fromObject": child,
                    "viaField": field_name,
                    "relationshipType": rtype,
                    "isJunctionSide": bool(cr.get("junctionIdListNames")),
                    "sentence": f"This object ('{obj_name}') has an inbound {rtype} relationship FROM the '{child}' object via the '{field_name}' field.",
                }
            )
        summaries[obj_name] = {
            "outbound": outbound,
            "inbound": inbound,
            "isLikelyJunction": is_likely_junction(obj_name, inbound_index),
        }
    return summaries


def write_per_object_files(
    objects: List[dict],
    rel_summaries: Dict[str, dict],
    out_root: Path,
    included: Set[str],
    usage_summaries: Optional[Dict[str, dict]] = None,
    ignored_namespaces: Optional[Set[str]] = None,
) -> None:
    out_objects = out_root / "objects"
    out_objects.mkdir(parents=True, exist_ok=True)
    for obj in objects:
        name = obj["name"]
        annotated = dict(obj)
        if isinstance(annotated.get("fields"), list):
            annotated["fields"] = sorted(annotated["fields"], key=lambda f: f.get("name", ""))
        if isinstance(annotated.get("childRelationships"), list):
            annotated["childRelationships"] = sorted(
                annotated["childRelationships"], key=lambda r: (r.get("childSObject", ""), r.get("field", ""))
            )
        full_out = rel_summaries.get(name, {}).get("outbound", [])
        full_in = rel_summaries.get(name, {}).get("inbound", [])
        outbound_clean = [e for e in full_out if e.get("toObject") in included]
        inbound_clean = [e for e in full_in if e.get("fromObject") in included]

        meta = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "outbound": full_out,
            "inbound": full_in,
            "outbound_clean": outbound_clean,
            "inbound_clean": inbound_clean,
            "isLikelyJunction": rel_summaries.get(name, {}).get("isLikelyJunction", False),
            "objectSummary": summarize_object(obj),
            "namespace": namespace_of(name) or "",
        }
        if usage_summaries and name in usage_summaries:
            meta["usageSummary"] = usage_summaries[name]
        if ignored_namespaces:
            meta["namespaceIgnored"] = is_ignored_namespace(name, ignored_namespaces)

        annotated["_relationshipMetadata"] = meta
        (out_objects / f"{name}.json").write_text(json.dumps(annotated, indent=2, ensure_ascii=False), encoding="utf-8")

    index = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "objectCount": len(objects),
        "objects": sorted([o["name"] for o in objects]),
    }
    (out_root / "relationships-index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def combine_raw_to_schema(raw_dir: Path, out_schema: Path) -> int:
    """Combine raw/*.json → schema.json (objects[]). Returns count."""
    objs = []
    for p in raw_dir.glob("*.json"):
        if p.name.startswith("_"):
            continue
        try:
            objs.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    schema = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "objects": objs,
    }
    out_schema.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(objs)


# ----------------------------
# Stats (counts + fill-rates)
# ----------------------------


def compute_fill_rates_from_records(fields: List[dict], records: List[dict]) -> Dict[str, dict]:
    """Compute per-field non-null counts/percent from a list of raw record dicts."""
    field_names = [f.get("name") for f in fields if isinstance(f, dict) and f.get("name")]
    totals = {fn: 0 for fn in field_names}
    n = len(records)
    for rec in records:
        if not isinstance(rec, dict):
            continue
        # Remove attributes key if present
        rec = {k: v for k, v in rec.items() if k != "attributes"}
        for fn in field_names:
            val = rec.get(fn, None)
            if val not in (None, ""):
                totals[fn] += 1
    out = {}
    for fn in field_names:
        non_null = totals.get(fn, 0)
        pct = (non_null / n) if n else 0.0
        out[fn] = {"nonNull": non_null, "sampleSize": n, "nonNullPct": pct}
    return out


def compute_stats_for_object(
    org: str,
    obj: dict,
    sample_n: int,
    order_by: Optional[str],
    retries: int,
    throttle_ms: int,
    stats_dir: Path,
    resume: bool,
) -> Optional[dict]:
    """Return usageSummary for one object and persist to stats_dir/name.usage.json."""
    name = obj.get("name")
    if not name:
        return None
    stats_path = stats_dir / f"{name}.usage.json"
    if resume and stats_path.exists():
        try:
            return json.loads(stats_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if not obj.get("queryable", True):
        summary = {
            "queryable": False,
            "objectCount": None,
            "sampled": 0,
            "fieldFillRatesTop": [],
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
        stats_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return summary

    # COUNT()
    obj_count = None
    attempt = 0
    while attempt <= retries:
        obj_count = count_records(org, name)
        if obj_count is not None:
            break
        attempt += 1
        time.sleep((100 * (2 ** (attempt - 1))) / 1000.0)  # small backoff for count

    # SAMPLE
    records = []
    attempt = 0
    while attempt <= retries and not records:
        records = sample_records(org, name, sample_n, order_by)
        if records:
            break
        attempt += 1
        time.sleep((100 * (2 ** (attempt - 1))) / 1000.0)

    # If FIELDS(ALL) failed, try explicit first 100 fields
    if not records:
        fields = [f.get("name") for f in obj.get("fields", []) if isinstance(f, dict) and f.get("name")]
        if fields:
            subset = fields[:100]
            field_list = ", ".join(subset)
            clauses = []
            if order_by:
                clauses.append(f"ORDER BY {order_by}")
            clauses.append(f"LIMIT {int(sample_n)}")
            suffix = " ".join(clauses)
            code, res = soql_query(org, f"SELECT {field_list} FROM {name} {suffix}")
            if code == 0 and res and isinstance(res.get("records"), list):
                records = res["records"]

    # Compute fill rates
    fill = compute_fill_rates_from_records(obj.get("fields", []), records)
    # Top 25 fields by nonNullPct, then by nonNull count
    top = sorted(
        [{"field": k, **v} for k, v in fill.items()],
        key=lambda x: (x["nonNullPct"], x["nonNull"]),
        reverse=True,
    )[:25]

    summary = {
        "queryable": obj.get("queryable", True),
        "objectCount": obj_count,
        "sampled": len(records),
        "fieldFillRatesTop": top,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    stats_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if throttle_ms > 0:
        time.sleep(throttle_ms / 1000.0)
    return summary


def compute_stats_for_all(
    org: str,
    objects: List[dict],
    out_root: Path,
    sample_n: int,
    order_by: Optional[str],
    retries: int,
    throttle_ms: int,
    resume: bool,
) -> Dict[str, dict]:
    stats_dir = out_root / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    usage: Dict[str, dict] = {}
    for i, obj in enumerate(objects, 1):
        name = obj.get("name")
        if not name:
            continue
        summary = compute_stats_for_object(
            org, obj, sample_n, order_by, retries, throttle_ms, stats_dir, resume
        )
        if summary:
            usage[name] = summary
        if i % 25 == 0:
            print(f"  … stats {i}/{len(objects)} objects processed")
    # Export rollups
    counts_rows = []
    fills_rows = []
    for n, s in usage.items():
        counts_rows.append([n, s.get("objectCount"), s.get("sampled"), s.get("queryable")])
        for row in s.get("fieldFillRatesTop", []):
            fills_rows.append([
                n,
                row.get("field"),
                row.get("nonNullPct"),
                row.get("sampleSize"),
                row.get("nonNull"),
            ])
    # counts
    with (out_root / "object_counts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["object", "count", "sampled", "queryable"])
        counts_rows.sort(key=lambda r: (r[0].lower()))
        w.writerows(counts_rows)
    # fill rates (top only)
    with (out_root / "field_fill_rates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["object", "field", "non_null_pct", "sample_size", "non_null_count"])
        fills_rows.sort(key=lambda r: (r[0].lower(), -float(r[2] or 0)))
        w.writerows(fills_rows)
    return usage


# ----------------------------
# Markdown / JSONL emission (corpus)
# ----------------------------


def md_escape(s: str) -> str:
    return str(s).replace("|", "\\|")


def pct_fmt(x: Optional[float]) -> str:
    try:
        return f"{100.0 * float(x):.1f}%"
    except Exception:
        return ""


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def build_overview_block(obj: dict) -> str:
    name = obj.get("name", "")
    label = obj.get("label", "")
    meta = obj.get("_relationshipMetadata", {}) or {}
    usage = meta.get("usageSummary", {}) or {}
    summary = meta.get("objectSummary", {}) or {}
    automation = meta.get("automationSummary", {}) or {}
    ns = meta.get("namespace", "") or ""
    junction = bool(meta.get("isLikelyJunction", False))
    field_type_counts = summary.get("fieldTypeCounts", {}) or {}
    name_field = summary.get("nameField", "") or ""
    queryable = obj.get("queryable", True)

    parts = []
    parts.append(f"# {label or name} ({name})")
    parts.append("")
    parts.append(
        "> "
        + " | ".join(
            [
                f"label: **{md_escape(label or name)}**",
                f"API name: **{md_escape(name)}**",
                f"custom: **{str(bool(obj.get('custom')))}**",
                f"namespace: **{md_escape(ns)}**" if ns else "namespace: *(none)*",
                f"junction?: **{str(junction)}**",
            ]
        )
    )
    parts.append("")
    parts.append("## Overview")
    bullets = [
        f"- **Queryable**: `{queryable}`",
        f"- **Name field**: `{md_escape(name_field)}`" if name_field else "- **Name field**: *(not flagged)*",
        f"- **Record count**: `{usage.get('objectCount')}`" if "objectCount" in usage else "- **Record count**: *(not computed)*",
        f"- **Sampled for fill-rates**: `{usage.get('sampled', 0)}`",
        f"- **Field types**: `{json.dumps(field_type_counts, ensure_ascii=False)}`",
    ]
    parts.extend(bullets)
    parts.append("")
    
    # Add Automation section if there are flows or triggers
    flows = automation.get("flows", [])
    triggers = automation.get("triggers", [])
    code_complexity = automation.get("code_complexity", {})
    
    if flows or triggers or code_complexity:
        parts.append("## Automation")
        parts.append("")
        if flows:
            parts.append("### Flows")
            for flow in flows:
                parts.append(f"- `{md_escape(flow)}`")
            parts.append("")
        if triggers:
            parts.append("### Apex Triggers")
            for trigger in triggers:
                parts.append(f"- `{md_escape(trigger)}`")
            parts.append("")
        
        # Add Code Complexity section
        if code_complexity:
            parts.append("### Code Complexity")
            parts.append("")
            
            # Trigger complexity
            trigger_complexity = code_complexity.get("triggers", [])
            if trigger_complexity:
                parts.append("#### Triggers")
                for trigger in trigger_complexity:
                    name = trigger.get("name", "")
                    total_lines = trigger.get("total_lines", 0)
                    comment_lines = trigger.get("comment_lines", 0)
                    code_lines = trigger.get("code_lines", 0)
                    parts.append(f"- `{md_escape(name)}`: {total_lines} total lines ({code_lines} code, {comment_lines} comments)")
                parts.append("")
            
            # Class complexity
            class_complexity = code_complexity.get("classes", [])
            if class_complexity:
                parts.append("#### Related Apex Classes")
                for cls in class_complexity:
                    name = cls.get("name", "")
                    total_lines = cls.get("total_lines", 0)
                    comment_lines = cls.get("comment_lines", 0)
                    code_lines = cls.get("code_lines", 0)
                    parts.append(f"- `{md_escape(name)}`: {total_lines} total lines ({code_lines} code, {comment_lines} comments)")
                parts.append("")
    
    return "\n".join(parts)


def build_relationships_block(obj: dict) -> str:
    meta = obj.get("_relationshipMetadata", {}) or {}
    out_clean = meta.get("outbound_clean", []) or []
    in_clean = meta.get("inbound_clean", []) or []
    parts = []
    parts.append("## Relationships")
    parts.append("")
    parts.append("### Outbound (this object points **to**)\n")
    if out_clean:
        for e in out_clean:
            parts.append(f"- {md_escape(e.get('sentence', ''))}")
    else:
        parts.append("- *(none)*")
    parts.append("")
    parts.append("### Inbound (other objects point **to** this)\n")
    if in_clean:
        for e in in_clean:
            parts.append(f"- {md_escape(e.get('sentence', ''))}")
    else:
        parts.append("- *(none)*")
    parts.append("")
    return "\n".join(parts)


def build_usage_block(obj: dict, top_n: int) -> str:
    meta = obj.get("_relationshipMetadata", {}) or {}
    usage = meta.get("usageSummary", {}) or {}
    top = usage.get("fieldFillRatesTop") or []
    
    parts = []
    
    # Top fields by fill-rate
    if top:
        parts.append("## Top fields by fill-rate (sampled)")
        parts.append("")
        parts.append("| Field | Non-Null % | Non-Null | Sample |")
        parts.append("|---|---:|---:|---:|")
        for row in top[:top_n]:
            parts.append(
                f"| `{md_escape(row.get('field', ''))}` | {pct_fmt(row.get('nonNullPct'))} | {row.get('nonNull', '')} | {row.get('sampleSize', '')} |"
            )
        parts.append("")
    
    # Data Quality section
    data_quality = usage.get("data_quality", {})
    if data_quality:
        parts.append("## Data Quality Analysis")
        parts.append("")
        
        # Picklist distributions
        picklist_distributions = data_quality.get("picklist_distributions", {})
        if picklist_distributions:
            parts.append("### Picklist Value Distributions")
            parts.append("")
            for field_name, distribution in picklist_distributions.items():
                if distribution:
                    parts.append(f"#### {md_escape(field_name)}")
                    parts.append("")
                    parts.append("| Value | Count |")
                    parts.append("|---|---:|")
                    for item in distribution:
                        value = item.get("value", "")
                        count = item.get("count", 0)
                        parts.append(f"| {md_escape(str(value))} | {count} |")
                    parts.append("")
        
        # Data freshness
        data_freshness = data_quality.get("data_freshness")
        if data_freshness:
            parts.append("### Data Freshness")
            parts.append("")
            old_count = data_freshness.get("old_records_count", 0)
            total_count = data_freshness.get("total_records", 0)
            percentage = data_freshness.get("percentage_old", 0)
            parts.append(f"- **Records older than 2 years**: {old_count:,} out of {total_count:,} ({percentage:.1f}%)")
            parts.append("")
    
    # User Adoption section
    user_adoption = usage.get("user_adoption", {})
    if user_adoption:
        parts.append("## User Adoption Analysis")
        parts.append("")
        
        top_profiles = user_adoption.get("top_owning_profiles", [])
        if top_profiles:
            parts.append("### Top Owning Profiles")
            parts.append("")
            parts.append("| Profile | Record Count |")
            parts.append("|---|---:|")
            for profile in top_profiles:
                profile_name = profile.get("profile", "")
                count = profile.get("record_count", 0)
                parts.append(f"| {md_escape(profile_name)} | {count:,} |")
            parts.append("")
    
    return "\n".join(parts)


def build_fields_table(obj: dict, max_rows: int) -> str:
    fields = obj.get("fields", []) or []
    # sort by name for stable diffs
    fields = sorted([f for f in fields if isinstance(f, dict)], key=lambda f: f.get("name", ""))
    rows = []
    
    for f in fields[:max_rows]:
        name = f.get("name", "")
        ftype = f.get("type", "")
        req = "Y" if f.get("nillable") is False else ""
        uniq = "Y" if f.get("unique") else ""
        ext = "Y" if f.get("externalId") else ""
        length = f.get("length", "")
        prec = f.get("precision", "")
        scale = f.get("scale", "")
        formula = "Y" if f.get("calculated") else ""
        
        # Add FLS information if available
        fls_info = ""
        fls_summary = f.get("_flsSummary")
        if fls_summary:
            editable = fls_summary.get("editable_by", [])
            readonly = fls_summary.get("readonly_by", [])
            fls_parts = []
            if editable:
                fls_parts.append(f"Editable by {', '.join(editable)}")
            if readonly:
                fls_parts.append(f"Read-only by {', '.join(readonly)}")
            if fls_parts:
                fls_info = f"FLS: {'; '.join(fls_parts)}"
        
        # Add audit history information if available
        audit_info = ""
        audit_history = f.get("_auditHistory")
        if audit_history:
            created_by = audit_history.get("created_by", "Unknown")
            created_date = audit_history.get("created_date", "")
            last_modified_by = audit_history.get("last_modified_by", "Unknown")
            last_modified_date = audit_history.get("last_modified_date", "")
            
            # Format dates if available
            if created_date:
                try:
                    # Parse ISO date format and format as YYYY-MM-DD
                    created_date = created_date.split("T")[0]
                except:
                    pass
            
            if last_modified_date:
                try:
                    # Parse ISO date format and format as YYYY-MM-DD
                    last_modified_date = last_modified_date.split("T")[0]
                except:
                    pass
            
            audit_parts = []
            if created_by and created_date:
                audit_parts.append(f"Created by {created_by} on {created_date}")
            if last_modified_by and last_modified_date:
                audit_parts.append(f"Last modified by {last_modified_by} on {last_modified_date}")
            
            if audit_parts:
                audit_info = f"History: {'; '.join(audit_parts)}"
        
        rows.append(
            f"| `{md_escape(name)}` | `{ftype}` | {req} | {uniq} | {ext} | {length} | {prec} | {scale} | {formula} |"
        )
        
        # Add FLS info as a separate row if available
        if fls_info:
            rows.append(f"| *{md_escape(fls_info)}* |  |  |  |  |  |  |  |  |")
        
        # Add audit history info as a separate row if available
        if audit_info:
            rows.append(f"| *{md_escape(audit_info)}* |  |  |  |  |  |  |  |  |")

    parts = []
    parts.append("## Fields (truncated)" if len(fields) > max_rows else "## Fields")
    parts.append("")
    parts.append("| Field | Type | Req | Unique | ExtId | Len | Prec | Scale | Formula |")
    parts.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    parts.extend(rows if rows else ["| *(none)* |  |  |  |  |  |  |  |  |"])
    parts.append("")
    if len(fields) > max_rows:
        parts.append(f"> Showing first {max_rows} of {len(fields)} fields for brevity.")
        parts.append("")
    
    return "\n".join(parts)


def build_fls_details(obj: dict, max_rows: int) -> str:
    """Build detailed FLS sentences for chunks.jsonl file."""
    fields = obj.get("fields", []) or []
    # sort by name for stable diffs
    fields = sorted([f for f in fields if isinstance(f, dict)], key=lambda f: f.get("name", ""))
    fls_sentences = []
    
    for f in fields[:max_rows]:
        name = f.get("name", "")
        fls_summary = f.get("_flsSummary")
        
        if fls_summary:
            editable = fls_summary.get("editable_by", [])
            readonly = fls_summary.get("readonly_by", [])
            
            # Create detailed FLS sentence
            fls_sentence_parts = []
            if editable:
                fls_sentence_parts.append(f"editable by {', '.join(editable)}")
            if readonly:
                fls_sentence_parts.append(f"read-only for {', '.join(readonly)}")
            
            if fls_sentence_parts:
                fls_sentences.append(f"The '{name}' field is {' and '.join(fls_sentence_parts)}.")
    
    if fls_sentences:
        parts = []
        parts.append("## Field-Level Security Details")
        parts.append("")
        for sentence in fls_sentences:
            parts.append(f"- {sentence}")
        parts.append("")
        return "\n".join(parts)
    
    return ""


def object_to_markdown(obj: dict, top_fill: int, max_field_rows: int) -> str:
    blocks = [
        build_overview_block(obj),
        build_relationships_block(obj),
        build_usage_block(obj, top_fill),
        build_fields_table(obj, max_field_rows),
    ]
    return "\n".join([b for b in blocks if b])





def add_chunk_with_size_check(chunks: List[dict], obj_name: str, section: str, text: str, extra_meta: Dict[str, Any], max_tokens: int = 6000):
    """
    Add a chunk if it's within token limits, otherwise split it into multiple chunks.
    Includes cross-references to related chunks for better LLM context.
    """
    if not text or not text.strip():
        return
    
    token_count = estimate_tokens(text)
    
    if token_count <= max_tokens:
        # Normal case - add as single chunk
        chunks.append({
            "id": f"{obj_name}:{section}",
            "object": obj_name,
            "section": section,
            "text": text,
            "metadata": extra_meta,
        })
    else:
        # Split into multiple chunks
        text_chunks = split_large_text(text, max_tokens)
        total_parts = len(text_chunks)
        
        # Generate all chunk IDs first
        chunk_ids = [f"{obj_name}:{section}_part{i}" for i in range(1, total_parts + 1)]
        
        for i, chunk_text in enumerate(text_chunks, 1):
            chunk_meta = extra_meta.copy()
            chunk_meta["part"] = i
            chunk_meta["totalParts"] = total_parts
            
            # Add references to other parts for better LLM context
            if total_parts > 1:
                chunk_meta["relatedChunks"] = [
                    chunk_id for chunk_id in chunk_ids if chunk_id != f"{obj_name}:{section}_part{i}"
                ]
            
            chunks.append({
                "id": f"{obj_name}:{section}_part{i}",
                "object": obj_name,
                "section": f"{section}_part{i}",
                "text": chunk_text,
                "metadata": chunk_meta,
            })


def emit_corpus(objects_dir: Path, md_out_dir: Path, emit_jsonl: bool, top_fill: int, max_field_rows: int) -> Tuple[int, int]:
    md_out_dir.mkdir(parents=True, exist_ok=True)
    md_count = 0
    chunks: List[dict] = []

    for p in sorted(objects_dir.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = obj.get("name")
        if not name:
            continue
        md = object_to_markdown(obj, top_fill, max_field_rows)
        (md_out_dir / sanitize_filename(f"{name}.md")).write_text(md, encoding="utf-8")
        md_count += 1

        if emit_jsonl:
            meta = obj.get("_relationshipMetadata", {}) or {}
            base_meta = {
                "apiName": name,
                "label": obj.get("label"),
                "custom": bool(obj.get("custom")),
                "namespace": meta.get("namespace", ""),
                "isLikelyJunction": bool(meta.get("isLikelyJunction")),
            }
            
            # Use the new function for all chunks
            add_chunk_with_size_check(chunks, name, "overview", build_overview_block(obj), base_meta)
            add_chunk_with_size_check(chunks, name, "relationships", build_relationships_block(obj), base_meta)
            
            ub = build_usage_block(obj, top_fill)
            if ub:
                add_chunk_with_size_check(chunks, name, "usage", ub, base_meta)
            
            # Slim fields chunk - most likely to be too large
            fields = obj.get("fields", []) or []
            fields = sorted([f for f in fields if isinstance(f, dict)], key=lambda f: f.get("name", ""))
            
            # For fields, create smaller chunks if needed
            if len(fields) > 100:  # Likely to be large
                # Split fields into batches
                field_batch_size = 50
                for i in range(0, len(fields), field_batch_size):
                    batch = fields[i:i + field_batch_size]
                    slim = [f"{f.get('name')} : {f.get('type')}" for f in batch]
                    batch_meta = base_meta.copy()
                    batch_meta["fieldBatch"] = i // field_batch_size + 1
                    batch_meta["totalFieldBatches"] = (len(fields) + field_batch_size - 1) // field_batch_size
                    batch_meta["rows"] = len(slim)
                    batch_meta["totalFields"] = len(fields)
                    
                    add_chunk_with_size_check(
                        chunks,
                        name,
                        f"fields_slim_batch{i // field_batch_size + 1}",
                        "\n".join(slim),
                        batch_meta
                    )
            else:
                # Normal case for small field lists
                slim = [f"{f.get('name')} : {f.get('type')}" for f in fields[:max_field_rows]]
                add_chunk_with_size_check(
                    chunks,
                    name,
                    "fields_slim",
                    "\n".join(slim),
                    {**base_meta, "rows": len(slim), "totalFields": len(fields)},
                )
            
            # FLS details chunk
            fls_details = build_fls_details(obj, max_field_rows)
            if fls_details:
                add_chunk_with_size_check(chunks, name, "fls_details", fls_details, base_meta)

    # Add cross-reference security model chunks if metadata is available
    if emit_jsonl and (objects_dir.parent / "metadata").exists():
        try:
            # Load profiles and permission sets for security model information
            profiles_path = objects_dir.parent / "metadata" / "profiles.json"
            permission_sets_path = objects_dir.parent / "metadata" / "permission_sets.json"
            roles_path = objects_dir.parent / "metadata" / "roles.json"
            
            profiles = []
            permission_sets = []
            roles = []
            
            if profiles_path.exists():
                profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            if permission_sets_path.exists():
                permission_sets = json.loads(permission_sets_path.read_text(encoding="utf-8"))
            if roles_path.exists():
                roles = json.loads(roles_path.read_text(encoding="utf-8"))
            
            # Get list of included objects
            included = set()
            for p in sorted(objects_dir.glob("*.json")):
                try:
                    obj = json.loads(p.read_text(encoding="utf-8"))
                    name = obj.get("name")
                    if name:
                        included.add(name)
                except Exception:
                    continue
            
            # Create security model summary chunks for each object
            for obj_name in included:
                # Get object metadata for consistency
                obj_meta = {}
                for p in sorted(objects_dir.glob("*.json")):
                    try:
                        obj = json.loads(p.read_text(encoding="utf-8"))
                        if obj.get("name") == obj_name:
                            meta = obj.get("_relationshipMetadata", {}) or {}
                            obj_meta = {
                                "apiName": obj_name,
                                "label": obj.get("label"),
                                "custom": bool(obj.get("custom")),
                                "namespace": meta.get("namespace", ""),
                                "isLikelyJunction": bool(meta.get("isLikelyJunction")),
                            }
                            break
                    except Exception:
                        continue
                
                # Create security model summary
                security_text = f"# Security Model Summary for {obj_name}\n\n"
                security_text += f"**Object Type**: {obj_meta.get('label', obj_name)}\n"
                security_text += f"**Custom Object**: {'Yes' if obj_meta.get('custom') else 'No'}\n"
                security_text += f"**Namespace**: {obj_meta.get('namespace') or '(none)'}\n\n"
                
                security_text += "## Available Security Controls\n\n"
                security_text += f"- **Profiles**: {len(profiles)} total profiles available\n"
                security_text += f"- **Permission Sets**: {len(permission_sets)} total permission sets available\n"
                security_text += f"- **Roles**: {len(roles)} total roles available\n\n"
                
                security_text += "## Security Recommendations\n\n"
                security_text += "1. **Profiles**: Use profiles for basic access control\n"
                security_text += "2. **Permission Sets**: Use permission sets for granular permissions\n"
                security_text += "3. **Roles**: Use roles for record-level access control\n"
                security_text += "4. **Field-Level Security**: Configure field permissions for sensitive data\n"
                security_text += "5. **Sharing Rules**: Set up sharing rules for record access\n\n"
                
                security_text += "## Common Permission Patterns\n\n"
                security_text += "- **Read-Only Access**: Grant Read permission only\n"
                security_text += "- **Standard User Access**: Grant Read, Create, Edit permissions\n"
                security_text += "- **Admin Access**: Grant all permissions including View All, Modify All\n"
                security_text += "- **Custom Access**: Use permission sets for specific use cases\n\n"
                
                security_text += "## Object-Specific Considerations\n\n"
                if obj_meta.get('custom'):
                    security_text += "- **Custom Object**: Requires explicit permissions in profiles/permission sets\n"
                    security_text += "- **Namespace**: Consider namespace-specific permissions\n"
                else:
                    security_text += "- **Standard Object**: May have default profile permissions\n"
                    security_text += "- **Salesforce Managed**: Permissions may be controlled by Salesforce\n"
                
                if obj_meta.get('isLikelyJunction'):
                    security_text += "- **Junction Object**: Consider relationship-based access patterns\n"
                
                chunks.append({
                    "id": f"{obj_name}:security_model",
                    "object": obj_name,
                    "section": "security_model",
                    "text": security_text,
                    "metadata": {
                        **obj_meta,
                        "totalProfiles": len(profiles),
                        "totalPermissionSets": len(permission_sets),
                        "totalRoles": len(roles),
                        "source": "schema",
                        "type": "security_cross_reference"
                    }
                })
                
        except Exception as e:
            print(f"⚠ Warning: Could not create security model cross-reference chunks: {e}")

    jsonl_written = 0
    if emit_jsonl:
        jsonl_path = md_out_dir / "chunks.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                jsonl_written += 1
    return md_count, jsonl_written


# ----------------------------
# Token counting functions
# ----------------------------

# RAG Performance Configuration
RAG_CONFIG = {
    "default_retrieval_count": 20,  # Increased from 15 to ensure all parts are retrieved
    "max_retrieval_count": 50,      # Maximum chunks to retrieve
    "aggregation_enabled": True,    # Enable chunk aggregation logic
    "metadata_filtering": True,     # Enable metadata-based filtering
    "source_filter": "schema",      # Default source filter
}

def get_optimal_search_kwargs(object_name: str = None, custom_k: int = None) -> dict:
    """
    Generate optimal search parameters for RAG retrieval.
    
    Args:
        object_name: Optional object name for targeted filtering
        custom_k: Optional custom retrieval count
    
    Returns:
        Dictionary with optimized search parameters
    """
    k = custom_k or RAG_CONFIG["default_retrieval_count"]
    k = min(k, RAG_CONFIG["max_retrieval_count"])  # Cap at maximum
    
    search_kwargs = {
        "k": k,
        "filter": {"source": RAG_CONFIG["source_filter"]}
    }
    
    # Add object-specific filtering if provided
    if object_name and RAG_CONFIG["metadata_filtering"]:
        search_kwargs["filter"]["object"] = object_name
    
    return search_kwargs

def aggregate_related_chunks(retrieved_docs: list) -> list:
    """
    Aggregate related chunks to ensure complete information retrieval.
    
    This function groups documents by their base ID (without _part suffix)
    and ensures all parts of split content are included.
    
    Args:
        retrieved_docs: List of retrieved documents from vector search
        
    Returns:
        Aggregated list with complete chunk information
    """
    if not RAG_CONFIG["aggregation_enabled"]:
        return retrieved_docs
    
    # Group documents by base ID
    chunk_groups = {}
    
    for doc in retrieved_docs:
        # Extract base ID (remove _part suffix)
        base_id = doc.get("id", "")
        if "_part" in base_id:
            base_id = base_id.rsplit("_part", 1)[0]
        elif "_batch" in base_id:
            base_id = base_id.rsplit("_batch", 1)[0]
        
        if base_id not in chunk_groups:
            chunk_groups[base_id] = []
        chunk_groups[base_id].append(doc)
    
    # Aggregate chunks and add missing parts
    aggregated_docs = []
    
    for base_id, chunks in chunk_groups.items():
        # Check if we have split chunks
        split_chunks = [c for c in chunks if "_part" in c.get("id", "") or "_batch" in c.get("id", "")]
        
        if split_chunks:
            # This is split content - ensure we have all parts
            metadata = split_chunks[0].get("metadata", {})
            total_parts = metadata.get("totalParts", 1)
            related_chunks = metadata.get("relatedChunks", [])
            
            # Add information about missing parts
            if len(split_chunks) < total_parts:
                missing_parts = total_parts - len(split_chunks)
                aggregated_docs.append({
                    "id": f"{base_id}_aggregation_info",
                    "content": f"Note: This content was split into {total_parts} parts. "
                              f"Retrieved {len(split_chunks)} parts, {missing_parts} parts may be missing. "
                              f"Related chunks: {', '.join(related_chunks)}",
                    "metadata": {
                        "type": "aggregation_info",
                        "base_id": base_id,
                        "retrieved_parts": len(split_chunks),
                        "total_parts": total_parts,
                        "missing_parts": missing_parts,
                        "related_chunks": related_chunks
                    }
                })
        
        # Add all chunks for this base ID
        aggregated_docs.extend(chunks)
    
    return aggregated_docs

def get_rag_performance_tips() -> str:
    """
    Generate performance tips for RAG deployment.
    
    Returns:
        String with deployment recommendations
    """
    tips = f"""
# RAG Performance Optimization Tips

## Search Configuration
- Default retrieval count: {RAG_CONFIG['default_retrieval_count']} (increased from 15)
- Maximum retrieval count: {RAG_CONFIG['max_retrieval_count']}
- Source filter: "{RAG_CONFIG['source_filter']}"

## Recommended app.py Configuration
```python
# Basic search
search_kwargs = {get_optimal_search_kwargs()}

# Object-specific search
search_kwargs = {get_optimal_search_kwargs("Account")}

# Custom retrieval count
search_kwargs = {get_optimal_search_kwargs(custom_k=30)}
```

## Chunk Aggregation
- Aggregation enabled: {RAG_CONFIG['aggregation_enabled']}
- Automatically groups related chunks
- Provides missing part information
- Ensures complete context retrieval

## Metadata Filtering
- Object-specific filtering: {RAG_CONFIG['metadata_filtering']}
- Source-based filtering: {RAG_CONFIG['source_filter']}
- Combined filtering for targeted results
"""
    return tips

def estimate_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """
    Estimate the number of tokens in a text string for OpenAI models.
    Uses tiktoken if available, otherwise falls back to character-based estimation.
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # cl100k_base is used by text-embedding-3-small and text-embedding-3-large
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            pass
    
    # Fallback: rough estimate of 1 token per 4 characters
    return len(text) // 4


def split_large_text(text: str, max_tokens: int = 6000, overlap_tokens: int = 200) -> List[str]:
    """
    Split text into chunks that don't exceed max_tokens.
    Maintains overlap between chunks for context continuity.
    """
    # If text is small enough, return as-is
    if estimate_tokens(text) <= max_tokens:
        return [text]
    
    # Split by lines first (works well for field lists)
    lines = text.split('\n')
    
    chunks = []
    current_chunk_lines = []
    current_tokens = 0
    
    for line in lines:
        line_tokens = estimate_tokens(line + '\n')
        
        # If single line exceeds max, split it by characters
        if line_tokens > max_tokens:
            # Handle extremely long lines by splitting them
            words = line.split()
            sub_chunk = ""
            for word in words:
                test_chunk = sub_chunk + " " + word if sub_chunk else word
                if estimate_tokens(test_chunk) > max_tokens:
                    if sub_chunk:
                        chunks.append(sub_chunk)
                        sub_chunk = word
                    else:
                        # Single word too long, truncate it
                        chunks.append(word[:max_tokens * 4])  # Rough conversion
                        sub_chunk = ""
                else:
                    sub_chunk = test_chunk
            if sub_chunk:
                current_chunk_lines = [sub_chunk]
                current_tokens = estimate_tokens(sub_chunk)
        elif current_tokens + line_tokens > max_tokens:
            # Current chunk is full, start a new one
            if current_chunk_lines:
                chunks.append('\n'.join(current_chunk_lines))
            
            # Add overlap from the end of previous chunk
            overlap_lines = []
            overlap_token_count = 0
            for i in range(len(current_chunk_lines) - 1, -1, -1):
                line_tok = estimate_tokens(current_chunk_lines[i] + '\n')
                if overlap_token_count + line_tok <= overlap_tokens:
                    overlap_lines.insert(0, current_chunk_lines[i])
                    overlap_token_count += line_tok
                else:
                    break
            
            current_chunk_lines = overlap_lines + [line]
            current_tokens = overlap_token_count + line_tokens
        else:
            current_chunk_lines.append(line)
            current_tokens += line_tokens
    
    # Don't forget the last chunk
    if current_chunk_lines:
        chunks.append('\n'.join(current_chunk_lines))
    
    return chunks

# ----------------------------
# Pinecone upload functions
# ----------------------------

def _embedding_dims_for(model_name: str) -> int:
    """Known OpenAI embedding dimensions."""
    m = model_name.strip().lower()
    if "text-embedding-3-large" in m:
        return 3072
    elif "text-embedding-ada-002" in m:
        return 1536
    return 1536  # default to small

def _batched(iterable: Iterable, n: int):
    """Yield successive n-sized chunks from iterable."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch




def get_existing_vectors_from_pinecone(
    index_name: str,
    namespace: str = "",
    org_alias: str = ""
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch existing vectors from Pinecone to determine what's already there.
    
    Returns:
        Dict mapping object names to their vector metadata and chunk info
    """
    if not PINECONE_AVAILABLE:
        print("Pinecone libraries not available. Cannot check existing vectors.")
        return {}
    
    import time
    
    # Get environment variables
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY must be set to check existing vectors.")
        return {}
    
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        
        # Check if index exists
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"Pinecone index '{index_name}' does not exist. No existing vectors to check.")
            return {}
        
        index = pc.Index(index_name)
        
        # Build filter for this org if specified
        filter_dict = {}
        if org_alias:
            filter_dict["org_alias"] = org_alias
        
        print(f"Fetching existing vectors from Pinecone index '{index_name}'...")
        
        # Fetch all vectors (this might take a while for large indexes)
        existing_vectors = {}
        fetch_response = index.query(
            vector=[0] * 1536,  # Dummy vector for metadata-only query
            top_k=10000,  # Adjust based on expected size
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        for match in fetch_response.matches:
            metadata = match.metadata
            object_name = metadata.get("object", "")
            section = metadata.get("section", "")
            
            if object_name not in existing_vectors:
                existing_vectors[object_name] = {
                    "sections": {},
                    "last_updated": metadata.get("last_updated", ""),
                    "org_alias": metadata.get("org_alias", ""),
                    "vector_count": 0
                }
            
            if section not in existing_vectors[object_name]["sections"]:
                existing_vectors[object_name]["sections"][section] = {
                    "chunk_ids": [],
                    "hash": metadata.get("content_hash", "")
                }
            
            existing_vectors[object_name]["sections"][section]["chunk_ids"].append(match.id)
            existing_vectors[object_name]["vector_count"] += 1
        
        print(f"Found {len(existing_vectors)} objects with {sum(obj['vector_count'] for obj in existing_vectors.values())} total vectors")
        return existing_vectors
        
    except Exception as e:
        print(f"Error fetching existing vectors: {e}")
        return {}


def calculate_content_hash(content: str) -> str:
    """Calculate a hash of content for change detection."""
    import hashlib
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def identify_changed_objects(
    current_objects: List[Dict[str, Any]],
    existing_vectors: Dict[str, Dict[str, Any]],
    org_alias: str = ""
) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare current schema with existing vectors to identify changes.
    
    Returns:
        Tuple of (changed_objects, new_objects, deleted_objects)
    """
    current_object_names = {obj["name"] for obj in current_objects}
    existing_object_names = set(existing_vectors.keys())
    
    # Find new and deleted objects
    new_objects = list(current_object_names - existing_object_names)
    deleted_objects = list(existing_object_names - current_object_names)
    
    # Check for changed objects
    changed_objects = []
    
    for obj in current_objects:
        obj_name = obj["name"]
        if obj_name in existing_vectors:
            existing_obj = existing_vectors[obj_name]
            
            # Check if object has changed by comparing content hashes
            current_hash = calculate_content_hash(json.dumps(obj, sort_keys=True))
            existing_hash = existing_obj.get("content_hash", "")
            
            if current_hash != existing_hash:
                changed_objects.append(obj_name)
    
    print(f"Change detection results:")
    print(f"  • New objects: {len(new_objects)}")
    print(f"  • Changed objects: {len(changed_objects)}")
    print(f"  • Deleted objects: {len(deleted_objects)}")
    print(f"  • Unchanged objects: {len(current_object_names) - len(new_objects) - len(changed_objects)}")
    
    return changed_objects, new_objects, deleted_objects


def filter_chunks_for_incremental_update(
    chunks: List[Dict[str, Any]],
    changed_objects: List[str],
    new_objects: List[str],
    deleted_objects: List[str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filter chunks to only include those for changed/new objects.
    
    Returns:
        Tuple of (filtered_chunks, objects_to_delete)
    """
    objects_to_process = set(changed_objects + new_objects)
    objects_to_delete = set(deleted_objects)
    
    filtered_chunks = []
    for chunk in chunks:
        object_name = chunk.get("object", "")
        if object_name in objects_to_process:
            filtered_chunks.append(chunk)
    
    print(f"Incremental update: Processing {len(filtered_chunks)} chunks for {len(objects_to_process)} objects")
    print(f"Will delete vectors for {len(objects_to_delete)} removed objects")
    
    return filtered_chunks, list(objects_to_delete)


def delete_vectors_for_objects(
    index_name: str,
    objects_to_delete: List[str],
    namespace: str = "",
    org_alias: str = ""
) -> None:
    """Delete vectors for objects that no longer exist."""
    if not objects_to_delete:
        return
    
    if not PINECONE_AVAILABLE:
        print("Pinecone libraries not available. Cannot delete vectors.")
        return
    
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY must be set to delete vectors.")
        return
    
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(index_name)
        
        print(f"Deleting vectors for {len(objects_to_delete)} removed objects...")
        
        # Build filter for objects to delete
        filter_dict = {"object": {"$in": objects_to_delete}}
        if org_alias:
            filter_dict["org_alias"] = org_alias
        
        # Delete vectors in batches
        delete_response = index.delete(filter=filter_dict)
        print(f"Deleted vectors for removed objects")
        
    except Exception as e:
        print(f"Error deleting vectors: {e}")


def upload_chunks_to_pinecone_incremental(
    jsonl_path: Path,
    current_objects: List[Dict[str, Any]],
    *,
    index_name: str,
    namespace: str = "",
    embed_model: str = "text-embedding-3-small",
    batch_size: int = 96,
    max_retries: int = 5,
    retry_backoff_s: float = 1.5,
    org_alias_for_metadata: str = "",
    metric: str = "cosine",
    incremental: bool = True
) -> None:
    """
    Upload chunks to Pinecone with incremental update support.
    
    If incremental=True:
    - Checks existing vectors in Pinecone
    - Compares with current schema
    - Only uploads changed/new objects
    - Deletes vectors for removed objects
    """
    if not PINECONE_AVAILABLE:
        print("Pinecone libraries not available. Skipping upload.")
        return
    
    if not jsonl_path.exists():
        print(f"JSONL file not found: {jsonl_path}")
        return
    
    # Load all chunks
    chunks = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    
    if incremental:
        print("\n🔄 Starting incremental update process...")
        
        # Get existing vectors from Pinecone
        existing_vectors = get_existing_vectors_from_pinecone(
            index_name=index_name,
            namespace=namespace,
            org_alias=org_alias_for_metadata
        )
        
        # Identify changes
        changed_objects, new_objects, deleted_objects = identify_changed_objects(
            current_objects=current_objects,
            existing_vectors=existing_vectors,
            org_alias=org_alias_for_metadata
        )
        
        # Filter chunks for incremental update
        filtered_chunks, objects_to_delete = filter_chunks_for_incremental_update(
            chunks=chunks,
            changed_objects=changed_objects,
            new_objects=new_objects,
            deleted_objects=deleted_objects
        )
        
        # Delete vectors for removed objects
        if objects_to_delete:
            delete_vectors_for_objects(
                index_name=index_name,
                objects_to_delete=objects_to_delete,
                namespace=namespace,
                org_alias=org_alias_for_metadata
            )
        
        # Use filtered chunks for upload
        chunks_to_upload = filtered_chunks
        
        if not chunks_to_upload:
            print("✅ No changes detected. Skipping upload.")
            return
        
        print(f"🔄 Uploading {len(chunks_to_upload)} chunks for incremental update...")
    else:
        print("\n🔄 Starting full upload process...")
        chunks_to_upload = chunks
    
    # Call the original upload function with filtered chunks
    upload_chunks_to_pinecone(
        jsonl_path=jsonl_path,  # We'll create a temporary file with filtered chunks
        index_name=index_name,
        namespace=namespace,
        embed_model=embed_model,
        batch_size=batch_size,
        max_retries=max_retries,
        retry_backoff_s=retry_backoff_s,
        org_alias_for_metadata=org_alias_for_metadata,
        metric=metric,
        chunks_to_upload=chunks_to_upload  # Pass filtered chunks
    )


def upload_chunks_to_pinecone(
    jsonl_path: Path,
    *,
    index_name: str,
    namespace: str = "",
    embed_model: str = "text-embedding-3-small",
    batch_size: int = 96,
    max_retries: int = 5,
    retry_backoff_s: float = 1.5,
    org_alias_for_metadata: str = "",
    metric: str = "cosine",
    chunks_to_upload: List[Dict[str, Any]] = None
) -> None:
    """
    Embeds and uploads schema chunks to Pinecone with batching and retries.
    
    Features:
    - Batched embeddings to avoid rate limits
    - Exponential backoff retry logic
    - Auto-creates index if missing
    - Progress reporting
    - Namespace support for multi-tenancy
    """
    if not PINECONE_AVAILABLE:
        print("Pinecone libraries not available. Skipping upload.")
        return
    
    import time
    import math
    
    # Get environment variables
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    pinecone_cloud = os.environ.get("PINECONE_CLOUD", "aws")
    pinecone_region = os.environ.get("PINECONE_REGION", "us-east-1")
    
    if not all([pinecone_api_key, openai_api_key]):
        print("Error: PINECONE_API_KEY and OPENAI_API_KEY must be set in environment variables.")
        print("Skipping Pinecone upload.")
        return
    
    print(f"\nStarting upload to Pinecone index '{index_name}'" + 
          (f" (namespace='{namespace}')" if namespace else "") + "...")
    
    try:
        # Initialize clients
        oai_client = OpenAI(api_key=openai_api_key)
        pc = Pinecone(api_key=pinecone_api_key)
        
        # Get embedding dimensions
        dims = _embedding_dims_for(embed_model)
        
        # Check if index exists, create if it doesn't
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"Creating Pinecone index '{index_name}' (dims={dims}, metric={metric}, {pinecone_cloud}/{pinecone_region})...")
            pc.create_index(
                name=index_name,
                dimension=dims,
                metric=metric,
                spec=ServerlessSpec(cloud=pinecone_cloud, region=pinecone_region),
            )
            # Wait for index to be ready
            print("Waiting for index to be ready...")
            while True:
                desc = pc.describe_index(index_name)
                if desc.status.ready:
                    break
                time.sleep(1.0)
            print("Index ready!")
        
        # Get the index
        index = pc.Index(index_name)
        
        # Use provided chunks or load from file
        if chunks_to_upload is not None:
            chunks = chunks_to_upload
            print(f"Using {len(chunks)} filtered chunks for incremental update...")
        else:
            # Load all chunks first to show total count
            chunks = []
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        chunks.append(json.loads(line))
        
        total_chunks = len(chunks)
        print(f"Processing {total_chunks} chunks in batches of {batch_size}...")
        
        # Process in batches
        uploaded_count = 0
        skipped_count = 0
        
        for batch_num, batch in enumerate(_batched(chunks, batch_size), start=1):
            # Prepare texts for embedding with token limit checking
            texts = []
            batch_indices_to_process = []
            
            for idx, chunk in enumerate(batch):
                # Create embedding text
                text = f"{chunk.get('object', '')} - {chunk.get('section', '')}: {chunk.get('text', '')}"
                
                # Check token count
                token_count = estimate_tokens(text)
                max_embed_tokens = 7500  # Leave buffer below 8192
                
                if token_count > max_embed_tokens:
                    # Truncate text to fit
                    print(f"  ⚠ Warning: Chunk {chunk.get('id')} has {token_count} tokens, truncating to {max_embed_tokens}")
                    
                    # Rough truncation by character count (4 chars ≈ 1 token)
                    max_chars = max_embed_tokens * 4
                    text = text[:max_chars] + "... [truncated]"
                    
                    # Mark as truncated in metadata
                    chunk["_truncated"] = True
                
                texts.append(text)
                batch_indices_to_process.append(idx)
            
            # Embed with retries
            embeddings = None
            for attempt in range(max_retries):
                try:
                    response = oai_client.embeddings.create(
                        model=embed_model,
                        input=texts
                    )
                    embeddings = [item.embedding for item in response.data]
                    break
                except Exception as e:
                    if "maximum context length" in str(e):
                        # Token limit still hit - try individual embeddings
                        print(f"  ⚠ Batch embedding failed due to token limits, trying individual embeddings...")
                        embeddings = []
                        
                        for text in texts:
                            try:
                                response = oai_client.embeddings.create(
                                    model=embed_model,
                                    input=[text]  # Single text
                                )
                                embeddings.append(response.data[0].embedding)
                            except Exception as individual_error:
                                print(f"    ❌ Failed to embed individual chunk: {individual_error}")
                                embeddings.append(None)  # Placeholder
                        
                        # Filter out failed embeddings
                        valid_embeddings = []
                        valid_batch_indices = []
                        for i, emb in enumerate(embeddings):
                            if emb is not None:
                                valid_embeddings.append(emb)
                                valid_batch_indices.append(batch_indices_to_process[i])
                            else:
                                skipped_count += 1
                        
                        embeddings = valid_embeddings
                        batch_indices_to_process = valid_batch_indices
                        break
                    else:
                        # Other error - retry normally
                        if attempt >= max_retries - 1:
                            raise
                        sleep_s = retry_backoff_s * (2 ** attempt)
                        print(f"  ⚠ Embedding retry {attempt+1}/{max_retries} after error: {e}")
                        print(f"    Sleeping {sleep_s:.1f}s before retry...")
                        time.sleep(sleep_s)
            
            if not embeddings:
                print(f"  ❌ Failed to create embeddings for batch {batch_num}, skipping...")
                skipped_count += len(batch)
                continue
            
            # Prepare vectors with metadata (only for successfully embedded chunks)
            vectors = []
            for idx, embedding in zip(batch_indices_to_process, embeddings):
                chunk = batch[idx]
                chunk_metadata = chunk.get("metadata", {})
                
                # Build vector metadata
                metadata = {
                    "source": "schema",
                    "text": chunk.get("text", "")[:1000],  # Truncate for metadata limits
                    "object": chunk.get("object", ""),
                    "section": chunk.get("section", ""),
                    "org_alias": org_alias_for_metadata or "",
                    "api_name": chunk_metadata.get("apiName", ""),
                    "label": chunk_metadata.get("label", ""),
                    "custom": chunk_metadata.get("custom", False),
                    "namespace": chunk_metadata.get("namespace", ""),
                    "is_junction": chunk_metadata.get("isLikelyJunction", False),
                }
                
                # Add truncation flag if text was truncated
                if chunk.get("_truncated"):
                    metadata["truncated"] = True
                
                # Add part information if present
                if "part" in chunk_metadata:
                    metadata["part"] = chunk_metadata["part"]
                    metadata["totalParts"] = chunk_metadata["totalParts"]
                
                # Add related chunks information if present
                if "relatedChunks" in chunk_metadata:
                    metadata["relatedChunks"] = chunk_metadata["relatedChunks"]
                
                # Remove empty values to save space
                metadata = {k: v for k, v in metadata.items() if v not in ("", None, False)}
                
                vectors.append({
                    "id": f"{org_alias_for_metadata}:{chunk['id']}" if org_alias_for_metadata else chunk["id"],
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert with retries
            for attempt in range(max_retries):
                try:
                    if namespace:
                        index.upsert(vectors=vectors, namespace=namespace)
                    else:
                        index.upsert(vectors=vectors)
                    break
                except Exception as e:
                    if attempt >= max_retries - 1:
                        raise
                    sleep_s = retry_backoff_s * (2 ** attempt)
                    print(f"  ⚠ Upsert retry {attempt+1}/{max_retries} after error: {e}")
                    print(f"    Sleeping {sleep_s:.1f}s before retry...")
                    time.sleep(sleep_s)
            
            uploaded_count += len(vectors)
            progress_pct = (uploaded_count / total_chunks) * 100
            print(f"  ✓ Batch {batch_num}: Uploaded {uploaded_count}/{total_chunks} chunks ({progress_pct:.1f}%)")
        
        # Final statistics
        print(f"\n✅ Successfully uploaded {uploaded_count} schema chunks to Pinecone")
        if skipped_count > 0:
            print(f"   Skipped {skipped_count} chunks due to embedding failures")
        
        # Calculate success rate
        total_processed = uploaded_count + skipped_count
        if total_processed > 0:
            success_rate = (uploaded_count / total_processed) * 100
            print(f"   Success rate: {success_rate:.1f}% ({uploaded_count}/{total_processed})")
        
        print(f"   Index: '{index_name}'" + (f", Namespace: '{namespace}'" if namespace else ""))
        
        # Get and display index stats
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count
        print(f"   Index now contains {total_vectors:,} total vectors")
        if stats.namespaces and namespace in stats.namespaces:
            ns_count = stats.namespaces[namespace].vector_count
            print(f"   Namespace '{namespace}' contains {ns_count:,} vectors")
        
    except Exception as e:
        print(f"\n❌ Error during Pinecone upload: {e}")
        import traceback
        traceback.print_exc()


# ----------------------------
# Parallel Processing Functions
# ----------------------------

def process_automation_for_object(obj: dict, org_alias: str, throttle_ms: int) -> dict:
    """Process automation dependencies for a single object with all API calls."""
    name = obj.get("name")
    if not name:
        return obj
    
    try:
        # Get automation dependencies
        automation_deps = get_automation_dependencies(org_alias, name)
        
        # Get field-level security
        fls_data = get_field_level_security(org_alias, name)
        
        # Get custom field audit history
        history_data = get_custom_field_history(org_alias, name)
        
        # Get code complexity metrics
        complexity_data = get_code_complexity(org_alias, name)
        
        # Initialize _relationshipMetadata if it doesn't exist
        if "_relationshipMetadata" not in obj:
            obj["_relationshipMetadata"] = {}
        
        obj["_relationshipMetadata"]["automationSummary"] = automation_deps
        obj["_relationshipMetadata"]["automationSummary"]["code_complexity"] = complexity_data
        
        # Inject FLS and audit history data into each field
        for field in obj.get("fields", []):
            field_name = field.get("name")
            
            # Inject FLS data if available
            if field_name and field_name in fls_data:
                field["_flsSummary"] = fls_data[field_name]
            
            # Inject audit history data if field is custom and history is available
            if field.get("custom", False) and field_name and field_name in history_data:
                field["_auditHistory"] = history_data[field_name]
        
        # Add throttling to respect API limits
        if throttle_ms > 0:
            time.sleep(throttle_ms / 1000.0)
            
        return obj
        
    except Exception as e:
        print(f"  !! Failed to get automation/FLS/audit/complexity data for {name}: {e}")
        # Initialize with empty automation summary on error
        if "_relationshipMetadata" not in obj:
            obj["_relationshipMetadata"] = {}
        obj["_relationshipMetadata"]["automationSummary"] = {"flows": [], "triggers": [], "code_complexity": {"triggers": [], "classes": []}}
        return obj


def process_quality_adoption_for_object(obj: dict, org_alias: str, usage_summaries: dict, throttle_ms: int) -> dict:
    """Process data quality and user adoption metrics for a single object."""
    name = obj.get("name")
    if not name:
        return obj
    
    # Get usage summary for this object
    usage_summary = usage_summaries.get(name, {})
    if not usage_summary:
        return obj
    
    try:
        # Get data quality metrics
        quality_data = get_data_quality_metrics(org_alias, name, usage_summary)
        usage_summary["data_quality"] = quality_data
        
        # Get user adoption metrics
        adoption_data = get_user_adoption_metrics(org_alias, name)
        usage_summary["user_adoption"] = adoption_data
        
        # Update the usage summary in the object
        if "_relationshipMetadata" not in obj:
            obj["_relationshipMetadata"] = {}
        obj["_relationshipMetadata"]["usageSummary"] = usage_summary
        
        # Add throttling to respect API limits
        if throttle_ms > 0:
            time.sleep(throttle_ms / 1000.0)
            
        return obj
        
    except Exception as e:
        print(f"  !! Failed to get quality/adoption data for {name}: {e}")
        # Initialize with empty data on error
        if "_relationshipMetadata" not in obj:
            obj["_relationshipMetadata"] = {}
        if "usageSummary" not in obj["_relationshipMetadata"]:
            obj["_relationshipMetadata"]["usageSummary"] = {}
        obj["_relationshipMetadata"]["usageSummary"]["data_quality"] = {"picklist_distributions": {}, "data_freshness": None}
        obj["_relationshipMetadata"]["usageSummary"]["user_adoption"] = {"top_owning_profiles": []}
        return obj


def process_automation_parallel(objects: List[dict], org_alias: str, throttle_ms: int, max_workers: int = 10) -> List[dict]:
    """Process automation dependencies for all objects in parallel with rate limiting."""
    print(f"Processing automation dependencies with {max_workers} concurrent workers...")
    
    # Calculate optimal batch size based on Salesforce API limits (200 calls/minute)
    # Each object makes 4 API calls, so we can process 50 objects per minute
    # With max_workers=10, we can process 10 objects simultaneously
    batch_size = max(1, len(objects) // max_workers)
    
    processed_objects = []
    total_objects = len(objects)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_obj = {
            executor.submit(process_automation_for_object, obj, org_alias, throttle_ms): obj 
            for obj in objects
        }
        
        # Process completed tasks with progress reporting
        completed = 0
        for future in concurrent.futures.as_completed(future_to_obj):
            obj = future_to_obj[future]
            try:
                processed_obj = future.result()
                processed_objects.append(processed_obj)
                completed += 1
                
                if completed % 25 == 0:
                    print(f"  … automation dependencies, FLS, audit history, and code complexity {completed}/{total_objects} objects processed")
                    
            except Exception as e:
                print(f"  !! Exception processing {obj.get('name', 'unknown')}: {e}")
                processed_objects.append(obj)  # Keep original object on error
    
    return processed_objects


def process_quality_adoption_parallel(objects: List[dict], org_alias: str, usage_summaries: dict, throttle_ms: int, max_workers: int = 10) -> List[dict]:
    """Process data quality and user adoption metrics for all objects in parallel."""
    print(f"Processing data quality and user adoption metrics with {max_workers} concurrent workers...")
    
    processed_objects = []
    total_objects = len(objects)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_obj = {
            executor.submit(process_quality_adoption_for_object, obj, org_alias, usage_summaries, throttle_ms): obj 
            for obj in objects
        }
        
        # Process completed tasks with progress reporting
        completed = 0
        for future in concurrent.futures.as_completed(future_to_obj):
            obj = future_to_obj[future]
            try:
                processed_obj = future.result()
                processed_objects.append(processed_obj)
                completed += 1
                
                if completed % 25 == 0:
                    print(f"  … data quality and user adoption {completed}/{total_objects} objects processed")
                    
            except Exception as e:
                print(f"  !! Exception processing {obj.get('name', 'unknown')}: {e}")
                processed_objects.append(obj)  # Keep original object on error
    
    return processed_objects


# ----------------------------
# Main
# ----------------------------


def main():
    global SF_BIN

    ap = argparse.ArgumentParser(
        description="Fetch + Split Salesforce schema for LLM/RAG (+ optional usage stats + Markdown/JSONL corpus)."
    )
    # CLI location
    ap.add_argument(
        "--sf-path",
        default="",
        help=(
            "Full path to sf(.ps1/.cmd/.exe) if not on PATH (e.g., C:\\\\Users\\you\\AppData\\Roaming\\npm\\sf.ps1)."
        ),
    )

    # Fetch controls
    ap.add_argument("--org-alias", default=os.environ.get("SF_ORG_ALIAS", "TP"), help="Salesforce org alias (sf auth). Can also be set via SF_ORG_ALIAS environment variable.")
    ap.add_argument(
        "--fetch",
        choices=["all", "seeds", "none"],
        default="all",
        help="What to fetch from the org before splitting. 'none' = use existing schema/raw.",
    )
    ap.add_argument("--seeds", default="", help="Comma-separated seed objects (used when --fetch=seeds).")
    ap.add_argument("--depth", type=int, default=1, help="Neighborhood depth for --fetch=seeds.")
    ap.add_argument(
        "--prefilter-noise",
        action="store_true",
        help="Skip describing noisy scaffolding objects (*History,*Feed,*ChangeEvent, etc.). Saves API calls.",
    )
    ap.add_argument(
        "--ignore-namespaces",
        default="",
        help="Comma-separated namespaces to exclude (e.g., npsp,sbqq). Applied during fetch and split.",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip objects that already exist in raw/ or stats/ (when enabled).",
    )
    ap.add_argument("--retries", type=int, default=2, help="Describe/Stats retries per object.")
    ap.add_argument("--throttle-ms", type=int, default=150, help="Sleep between describe calls (ms).")
    ap.add_argument("--backoff-ms", type=int, default=400, help="Initial backoff for describe retries (ms).")
    ap.add_argument(
        "--api-versions",
        default=",".join(DEFAULT_API_VERSIONS),
        help="Comma-separated fallback API versions (e.g., 64.0,63.0,62.0).",
    )
    ap.add_argument("--max-objects", type=int, default=None, help="Limit number of objects (debug).")

    # Split/annotate controls
    ap.add_argument("-o", "--output", default=str(Path.cwd()), help="Output folder root.")
    ap.add_argument("--filter-noise", action="store_true", help="Exclude noisy/system objects in final outputs.")
    ap.add_argument("--clean-output", action="store_true", help="Remove previous outputs before writing.")
    ap.add_argument("-i", "--input", default="", help="Path to an existing schema.json (used if --fetch=none).")

    # Stats controls
    ap.add_argument(
        "--with-stats",
        action="store_true",
        help="Also compute object counts + field fill-rates (sampled).",
    )
    ap.add_argument("--stats-sample", type=int, default=500, help="Sample size per object for fill-rates.")
    ap.add_argument(
        "--stats-order-by",
        default="LastModifiedDate DESC",
        help="ORDER BY clause for sampling (e.g., 'CreatedDate DESC'). Empty string disables ordering.",
    )
    ap.add_argument(
        "--stats-resume",
        action="store_true",
        help="Skip stats for objects that already have stats/*.usage.json",
    )

    # Automation controls
    ap.add_argument(
        "--with-automation",
        action="store_true",
        help="Also fetch automation dependencies, field-level security, audit history, code complexity, data quality, and user adoption metrics for each object.",
    )
    ap.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Maximum number of concurrent workers for automation processing (default: 10). Higher values speed up processing but may hit API limits.",
    )

    # Metadata controls
    ap.add_argument(
        "--with-metadata",
        action="store_true",
        help="Also fetch org-wide metadata (profiles, permission sets, roles, etc.) for comprehensive admin guidance.",
    )

    # Corpus emission
    ap.add_argument("--emit-markdown", action="store_true", help="Emit Markdown corpus from objects/*.json")
    ap.add_argument(
        "--emit-jsonl",
        action="store_true",
        help="Emit chunks.jsonl alongside Markdown (good for vector DB ingestion)",
    )
    ap.add_argument("--markdown-output", default="md", help="Output folder for Markdown/JSONL")
    ap.add_argument("--max-field-rows", type=int, default=400, help="Max field rows per object in corpus")
    ap.add_argument("--top-fill", type=int, default=25, help="Top-N fields by fill-rate in corpus")

    # Pinecone upload flags
    ap.add_argument(
        "--push-to-pinecone",
        action="store_true",
        help="Upload generated JSONL chunks to Pinecone vector database"
    )
    ap.add_argument(
        "--incremental-update",
        action="store_true",
        help="Enable incremental updates - only upload changed/new objects to Pinecone"
    )
    ap.add_argument(
        "--pinecone-index",
        default=os.environ.get("PINECONE_INDEX_NAME", "salesforce-schema"),
        help="Pinecone index name (default from PINECONE_INDEX_NAME env var)"
    )
    ap.add_argument(
        "--pinecone-namespace",
        default=os.environ.get("PINECONE_NAMESPACE", ""),
        help="Pinecone namespace for multi-tenancy (optional)"
    )
    ap.add_argument(
        "--embed-model",
        default=os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        help="OpenAI embedding model to use"
    )
    ap.add_argument(
        "--embed-batch-size",
        type=int,
        default=int(os.environ.get("EMBED_BATCH_SIZE", "96")),
        help="Batch size for embedding requests (default: 96)"
    )
    ap.add_argument("--rag-tips", action="store_true", help="Generate RAG performance optimization tips")

    args = ap.parse_args()

    # Log which org alias is being used
    print(f"Using org alias: {args.org_alias}")

    # Resolve CLI once
    SF_BIN = resolve_sf(args.sf_path)

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    ignored_ns = {s.strip() for s in args.ignore_namespaces.split(",") if s.strip()}

    # Clean outputs if requested
    if args.clean_output:
        for p in ["objects", "raw", "stats", args.markdown_output]:
            try:
                shutil.rmtree(out_root / p)
            except Exception:
                pass
        for fname in (
            "edges.csv",
            "edges.clean.csv",
            "nodes.csv",
            "nodes.clean.csv",
            "relationships-index.json",
            "sobject-list.json",
            "sobject-list.clean.json",
            "schema.json",
            "object_counts.csv",
            "field_fill_rates.csv",
        ):
            try:
                os.remove(out_root / fname)
            except Exception:
                pass

    api_versions = [v.strip() for v in args.api_versions.split(",") if v.strip()]

    # 1) FETCH (optional)
    all_names_input: List[str] = []
    if args.fetch != "none":
        seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
        names, errors = fetch_describes(
            FetchConfig(
                org=args.org_alias,
                out_root=out_root,
                prefilter_noise=args.prefilter_noise,
                prefilter_namespaces=ignored_ns,
                throttle_ms=args.throttle_ms,
                retries=args.retries,
                backoff_ms=args.backoff_ms,
                max_objects=args.max_objects,
                resume=args.resume,
                mode=args.fetch,
                seeds=seeds,
                depth=args.depth,
                api_versions=api_versions,
            )
        )
        all_names_input = names
        if errors:
            print(f"NOTE: {len(errors)} objects failed to describe. See raw/_errors.log")
        count = combine_raw_to_schema(out_root / "raw", out_root / "schema.json")
        print(f"Combined schema objects: {count}")
        schema_path = out_root / "schema.json"
    else:
        if not args.input:
            raise SystemExit("When --fetch=none, you must pass --input path to schema.json")
        schema_path = Path(args.input)
        data = safe_json_load(schema_path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("objects"), list):
            all_names_input = [o.get("name") for o in data["objects"] if isinstance(o, dict) and o.get("name")]
        elif isinstance(data, list):
            all_names_input = [o.get("name") for o in data if isinstance(o, dict) and o.get("name")]

    # 2) SPLIT / ANNOTATE
    raw = schema_path.read_text(encoding="utf-8-sig")
    data = safe_json_load(raw)
    objects_raw = data.get("objects") if isinstance(data, dict) else (data if isinstance(data, list) else None)
    if objects_raw is None:
        raise SystemExit("Expected schema.json to be {'objects': [...]} or a list of describes.")
    cleaned: Dict[str, dict] = {}
    for o in objects_raw:
        if isinstance(o, dict) and o.get("name"):
            cleaned[o["name"]] = o
    objects = list(cleaned.values())

    # Filter noisy/system + namespaces
    pre_len = len(objects)
    if args.filter_noise:
        objects = [o for o in objects if not is_noise_object(o["name"])]
    if ignored_ns:
        objects = [o for o in objects if not is_ignored_namespace(o["name"], ignored_ns)]
    if pre_len != len(objects):
        print(f"Filtered {pre_len - len(objects)} objects via noise/namespaces; {len(objects)} remain.")
    if not objects:
        raise SystemExit("No valid objects found in schema.json after cleaning/filtering.")

    # Relationship summaries
    rel_summaries = build_relationships(objects)
    included = {o["name"] for o in objects}

    # 3) (Optional) Stats: counts + field fill-rates
    usage_summaries: Optional[Dict[str, dict]] = None
    if args.with_stats:
        order_by = args.stats_order_by.strip() or None
        usage_summaries = compute_stats_for_all(
            org=args.org_alias,
            objects=objects,
            out_root=out_root,
            sample_n=args.stats_sample,
            order_by=order_by,
            retries=args.retries,
            throttle_ms=args.throttle_ms,
            resume=args.stats_resume or args.resume,
        )

    # 3.5) Get automation dependencies, field-level security, audit history, and code complexity for each object
    if args.with_automation:
        print("Fetching automation dependencies, field-level security, audit history, and code complexity...")
        objects = process_automation_parallel(
            objects=objects,
            org_alias=args.org_alias,
            throttle_ms=args.throttle_ms,
            max_workers=args.max_workers
        )

    # 3.6) Get data quality and user adoption metrics for each object
    if args.with_automation and usage_summaries:
        print("Fetching data quality and user adoption metrics...")
        objects = process_quality_adoption_parallel(
            objects=objects,
            org_alias=args.org_alias,
            usage_summaries=usage_summaries,
            throttle_ms=args.throttle_ms,
            max_workers=args.max_workers
        )

    # 3.7) Collect org-wide metadata
    if args.with_metadata:
        print("Fetching org-wide metadata (profiles, permission sets, roles)...")
        metadata_dir = out_root / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch profiles
        profiles = get_all_profiles(args.org_alias)
        if profiles:
            (metadata_dir / "profiles.json").write_text(
                json.dumps(profiles, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
            print(f"  ✓ Found {len(profiles)} profiles")
        
        # Fetch permission sets
        permission_sets = get_all_permission_sets(args.org_alias)
        if permission_sets:
            (metadata_dir / "permission_sets.json").write_text(
                json.dumps(permission_sets, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
            print(f"  ✓ Found {len(permission_sets)} permission sets")
        
        # Fetch roles
        roles = get_all_roles(args.org_alias)
        if roles:
            (metadata_dir / "roles.json").write_text(
                json.dumps(roles, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
            print(f"  ✓ Found {len(roles)} roles")
        
        # Generate markdown summaries
        print("  Generating markdown summaries...")
        
        # Create profiles summary
        if profiles:
            profiles_md = create_profile_markdown_summary(profiles)
            (metadata_dir / "profiles.md").write_text(profiles_md, encoding="utf-8")
            print(f"  ✓ Created profiles.md")
        
        # Create permission sets summary
        if permission_sets:
            permission_sets_md = create_permission_set_markdown_summary(permission_sets)
            (metadata_dir / "permission_sets.md").write_text(permission_sets_md, encoding="utf-8")
            print(f"  ✓ Created permission_sets.md")
        
        # Create roles summary
        if roles:
            roles_md = create_role_markdown_summary(roles)
            (metadata_dir / "roles.md").write_text(roles_md, encoding="utf-8")
            print(f"  ✓ Created roles.md")
        
        # Create comprehensive metadata summary
        metadata_summary = f"""# Salesforce Org Metadata Summary

## Overview
This document provides a comprehensive overview of the Salesforce org's metadata including profiles, permission sets, and roles.

## Summary Statistics
- **Profiles:** {len(profiles) if profiles else 0}
- **Permission Sets:** {len(permission_sets) if permission_sets else 0}
- **Roles:** {len(roles) if roles else 0}

## Files Generated
- `profiles.json` - Raw profile data
- `profiles.md` - Profile summary and details
- `permission_sets.json` - Raw permission set data
- `permission_sets.md` - Permission set summary and details
- `roles.json` - Raw role data
- `roles.md` - Role hierarchy and details

## Usage
These files provide comprehensive information about the org's security model and can be used for:
- Security audits and compliance
- User access management
- Permission set optimization
- Role hierarchy analysis
- Administrative documentation

For detailed information, refer to the individual markdown files.
"""
        (metadata_dir / "README.md").write_text(metadata_summary, encoding="utf-8")
        print(f"  ✓ Created metadata README.md")
        
        # Generate metadata corpus if markdown emission is enabled
        if args.emit_markdown:
            print("  Generating metadata corpus...")
            md_dir = out_root / args.markdown_output
            md_count, jsonl_count = emit_metadata_corpus(
                metadata_dir, 
                md_dir, 
                args.emit_jsonl,
                args.org_alias
            )
            if md_count > 0:
                print(f"  ✓ Created org_metadata.md")
            if jsonl_count > 0:
                print(f"  ✓ Created {jsonl_count} metadata chunks")

    # 4) Write per-object JSON files
    write_per_object_files(objects, rel_summaries, out_root, included, usage_summaries, ignored_ns)

    # Graph/summary CSVs
    write_edges(rel_summaries, out_root, "edges.csv")
    rel_summaries_clean = {
        k: {
            "outbound": [e for e in v.get("outbound", []) if e.get("toObject") in included],
            "inbound": [e for e in v.get("inbound", []) if e.get("fromObject") in included],
            "isLikelyJunction": v.get("isLikelyJunction", False),
        }
        for k, v in rel_summaries.items()
    }
    write_edges(rel_summaries_clean, out_root, "edges.clean.csv")
    objects_by_name = {o["name"]: o for o in objects}
    write_nodes(rel_summaries, objects_by_name, included, out_root, "nodes.csv")
    write_nodes(rel_summaries_clean, objects_by_name, included, out_root, "nodes.clean.csv")

    # Emit sobject list files
    if not all_names_input:
        all_names_input = list(cleaned.keys())
    write_sobject_lists(all_names_input, included, out_root)

    # 5) (Optional) Emit Markdown / JSONL corpus
    if args.emit_markdown or args.emit_jsonl:
        md_dir = out_root / args.markdown_output
        md_count, jsonl_count = emit_corpus(
            out_root / "objects",
            md_dir,
            emit_jsonl=args.emit_jsonl,
            top_fill=args.top_fill,
            max_field_rows=args.max_field_rows,
        )
        print(f"✓ Markdown files: {md_count} → {md_dir}")
        if args.emit_jsonl:
            print(f"✓ chunks.jsonl rows: {jsonl_count} → {md_dir / 'chunks.jsonl'}")
    
    # 6) Generate metadata corpus if enabled
    metadata_md_count = 0
    metadata_jsonl_count = 0
    if args.with_metadata and (out_root / "metadata").exists():
        metadata_md_count, metadata_jsonl_count = emit_metadata_corpus(
            out_root / "metadata",
            md_dir,
            emit_jsonl=args.emit_jsonl
        )
        print(f"✓ Metadata markdown files: {metadata_md_count} → {md_dir}")
        if args.emit_jsonl:
            print(f"✓ metadata_chunks.jsonl rows: {metadata_jsonl_count}")
            
            # Combine JSONL files
            if metadata_jsonl_count > 0:
                combined_path = md_dir / "all_chunks.jsonl"
                with combined_path.open("w", encoding="utf-8") as outfile:
                    # Copy main chunks
                    chunks_path = md_dir / "chunks.jsonl"
                    if chunks_path.exists():
                        with chunks_path.open("r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                    
                    # Append metadata chunks
                    metadata_chunks_path = md_dir / "metadata_chunks.jsonl"
                    if metadata_chunks_path.exists():
                        with metadata_chunks_path.open("r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                
                print(f"✓ Combined all_chunks.jsonl: {jsonl_count + metadata_jsonl_count} total rows")
                
                # Update the path for Pinecone upload
                jsonl_path = combined_path
            else:
                jsonl_path = md_dir / "chunks.jsonl"
        else:
            jsonl_path = md_dir / "chunks.jsonl"
    else:
        jsonl_path = md_dir / "chunks.jsonl"

    # 7) (Optional) Upload to Pinecone
    if args.push_to_pinecone and args.emit_jsonl:
        if jsonl_path.exists():
            metric = os.environ.get("PINECONE_METRIC", "cosine")
            
            if args.incremental_update:
                # Use incremental upload
                upload_chunks_to_pinecone_incremental(
                    jsonl_path=jsonl_path,
                    current_objects=objects,
                    index_name=args.pinecone_index,
                    namespace=args.pinecone_namespace,
                    embed_model=args.embed_model,
                    batch_size=args.embed_batch_size,
                    org_alias_for_metadata=args.org_alias,
                    metric=metric,
                    incremental=True
                )
            else:
                # Use full upload
                upload_chunks_to_pinecone(
                    jsonl_path,
                    index_name=args.pinecone_index,
                    namespace=args.pinecone_namespace,
                    embed_model=args.embed_model,
                    batch_size=args.embed_batch_size,
                    org_alias_for_metadata=args.org_alias,
                    metric=metric,
                )
        else:
            print("⚠ Pinecone upload skipped: chunks.jsonl not found")
    elif args.push_to_pinecone and not args.emit_jsonl:
        print("⚠ Pinecone upload skipped: --emit-jsonl not specified")

    # Final summary
    print(f"\n" + "="*60)
    print(f"📊 FINAL SUMMARY")
    print(f"="*60)
    print(f"✓ Objects processed: {len(objects)}")
    print(f"✓ Output directory: {out_root}")
    
    if args.emit_jsonl:
        # Determine which JSONL file to analyze
        if args.with_metadata and (out_root / "metadata").exists() and metadata_jsonl_count > 0:
            jsonl_path = md_dir / "all_chunks.jsonl"
            total_chunks = jsonl_count + metadata_jsonl_count
        else:
            jsonl_path = md_dir / "chunks.jsonl"
            total_chunks = jsonl_count
        
        if jsonl_path.exists():
            # Count total chunks and analyze token usage
            large_chunks = 0
            split_chunks = 0
            
            try:
                with jsonl_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            chunk = json.loads(line)
                            
                            # Check for split chunks
                            if "_part" in chunk.get("section", "") or "_batch" in chunk.get("section", ""):
                                split_chunks += 1
                            
                            # Check for large chunks (near token limit)
                            text = f"{chunk.get('object', '')} - {chunk.get('section', '')}: {chunk.get('text', '')}"
                            token_count = estimate_tokens(text)
                            if token_count > 6000:  # Near the 7500 limit
                                large_chunks += 1
                
                print(f"✓ JSONL chunks generated: {total_chunks}")
                if split_chunks > 0:
                    print(f"  └─ Split into multiple parts: {split_chunks} chunks")
                if large_chunks > 0:
                    print(f"  └─ Large chunks (>6000 tokens): {large_chunks} chunks")
                
            except Exception as e:
                print(f"⚠ Could not analyze JSONL file: {e}")
    
    if args.push_to_pinecone and args.emit_jsonl:
        print(f"✓ Pinecone upload: Enabled")
        if args.incremental_update:
            print(f"  └─ Mode: Incremental update (only changed/new objects)")
        else:
            print(f"  └─ Mode: Full upload")
        print(f"  └─ Index: {args.pinecone_index}")
        if args.pinecone_namespace:
            print(f"  └─ Namespace: {args.pinecone_namespace}")
        print(f"  └─ Embedding model: {args.embed_model}")
        print(f"  └─ Batch size: {args.embed_batch_size}")
    
    print(f"✓ Token limit handling: Active")
    print(f"  └─ Max tokens per chunk: 6000 (with 1500 buffer)")
    print(f"  └─ Automatic splitting: Enabled")
    print(f"  └─ Truncation fallback: Enabled")
    
    # Add metadata summary if collected
    if args.with_metadata:
        metadata_dir = out_root / "metadata"
        if metadata_dir.exists():
            profiles_file = metadata_dir / "profiles.json"
            permission_sets_file = metadata_dir / "permission_sets.json"
            roles_file = metadata_dir / "roles.json"
            
            profiles_count = len(json.loads(profiles_file.read_text())) if profiles_file.exists() else 0
            permission_sets_count = len(json.loads(permission_sets_file.read_text())) if permission_sets_file.exists() else 0
            roles_count = len(json.loads(roles_file.read_text())) if roles_file.exists() else 0
            
            print(f"✓ Metadata collected: {metadata_dir}")
            print(f"  └─ Profiles: {profiles_count}")
            print(f"  └─ Permission Sets: {permission_sets_count}")
            print(f"  └─ Roles: {roles_count}")
            print(f"  └─ Markdown summaries: profiles.md, permission_sets.md, roles.md")
            
            # Check for metadata corpus files
            org_metadata_file = md_dir / "org_metadata.md"
            metadata_chunks_file = md_dir / "metadata_chunks.jsonl"
            if org_metadata_file.exists():
                print(f"  └─ Comprehensive overview: org_metadata.md")
            if metadata_chunks_file.exists():
                try:
                    metadata_chunks_count = sum(1 for _ in metadata_chunks_file.open("r", encoding="utf-8"))
                    print(f"  └─ Vector chunks: {metadata_chunks_count} metadata chunks")
                except Exception:
                    pass
            
            # Check for security model cross-reference chunks
            chunks_file = md_dir / "chunks.jsonl"
            if chunks_file.exists():
                try:
                    security_chunks_count = sum(1 for line in chunks_file.open("r", encoding="utf-8") if "security_model" in line)
                    if security_chunks_count > 0:
                        print(f"  └─ Security model chunks: {security_chunks_count} cross-reference chunks")
                except Exception:
                    pass
    
    # Generate RAG performance tips if requested
    if args.rag_tips:
        tips_file = out_root / "rag_performance_tips.md"
        tips_content = get_rag_performance_tips()
        tips_file.write_text(tips_content, encoding="utf-8")
        print(f"✓ RAG performance tips: {tips_file}")
        print(f"  └─ Search optimization: {RAG_CONFIG['default_retrieval_count']} chunks (increased from 15)")
        print(f"  └─ Chunk aggregation: Enabled")
        print(f"  └─ Metadata filtering: Enabled")
    
    print(f"="*60)
    print(f"✅ Processing complete!")
    print(f"="*60)


if __name__ == "__main__":
    main()

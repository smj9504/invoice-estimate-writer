#!/usr/bin/env python
"""Check all registered routes in the FastAPI application"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def check_routes():
    """Check available routes"""
    
    print("Checking API Routes")
    print("=" * 50)
    
    # Check OpenAPI schema to see all registered routes
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get('paths', {})
            
            print("\nRegistered API Endpoints:")
            print("-" * 30)
            
            # Sort paths for better readability
            sorted_paths = sorted(paths.keys())
            
            for path in sorted_paths:
                methods = paths[path].keys()
                methods_str = ', '.join([m.upper() for m in methods if m != 'parameters'])
                print(f"  {path:<40} [{methods_str}]")
            
            # Check specifically for invoice endpoints
            print("\n\nInvoice-related endpoints:")
            print("-" * 30)
            invoice_paths = [p for p in sorted_paths if 'invoice' in p.lower()]
            if invoice_paths:
                for path in invoice_paths:
                    methods = paths[path].keys()
                    methods_str = ', '.join([m.upper() for m in methods if m != 'parameters'])
                    print(f"  {path:<40} [{methods_str}]")
            else:
                print("  ⚠️  No invoice endpoints found!")
                
        else:
            print(f"Failed to get OpenAPI schema: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    
    # Test specific endpoints
    print("\nTesting Specific Endpoints:")
    print("-" * 30)
    
    test_endpoints = [
        ("GET", "/api/invoices/"),
        ("POST", "/api/invoices/"),
        ("GET", "/invoices/"),
        ("POST", "/invoices/"),
    ]
    
    for method, endpoint in test_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json={})
            
            status = "✓" if response.status_code != 404 else "✗"
            print(f"  {status} {method:6} {endpoint:<30} -> {response.status_code}")
        except Exception as e:
            print(f"  ✗ {method:6} {endpoint:<30} -> Error: {e}")

if __name__ == "__main__":
    check_routes()
#!/usr/bin/env python3
"""
Generate a simple security report from Trivy scan results
"""

import json
import os
import sys

def count_vulnerabilities(json_file):
    """Count vulnerabilities by severity"""
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"File not found: {json_file}")
        return None
    
    # Get file size
    file_size = os.path.getsize(json_file)
    if file_size == 0:
        print(f"File is empty: {json_file}")
        return None
    
    try:
        # Read file with explicit UTF-8 encoding and handle errors
        with open(json_file, 'r', encoding='utf-8', errors='replace') as f:
            # Parse JSON
            data = json.loads(f.read())
            
            # Initialize counts
            counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
            
            # Check if results exist
            if 'Results' not in data:
                print(f"No results found in {json_file}")
                return counts
            
            # Count vulnerabilities
            for result in data['Results']:
                if 'Vulnerabilities' not in result:
                    continue
                
                for vuln in result['Vulnerabilities']:
                    severity = vuln.get('Severity', 'UNKNOWN').upper()
                    if severity in counts:
                        counts[severity] += 1
            
            return counts
    except Exception as e:
        print(f"Error processing {json_file}: {str(e)}")
        return None

def main():
    """Generate a security report"""
    frontend_file = os.path.join('reports', 'frontend-scan.json')
    backend_file = os.path.join('reports', 'backend-scan.json')
    
    # Check if files exist
    if not os.path.exists(frontend_file) or not os.path.exists(backend_file):
        print("Error: Scan result files not found")
        print(f"Frontend file: {frontend_file} - Exists: {os.path.exists(frontend_file)}")
        print(f"Backend file: {backend_file} - Exists: {os.path.exists(backend_file)}")
        return 1
    
    # Count vulnerabilities
    print("\nCounting vulnerabilities in scan results...")
    frontend_counts = count_vulnerabilities(frontend_file) or {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    backend_counts = count_vulnerabilities(backend_file) or {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    
    # Calculate totals
    total_counts = {}
    for severity in frontend_counts:
        total_counts[severity] = frontend_counts.get(severity, 0) + backend_counts.get(severity, 0)
    
    # Print summary
    print("\n===== SECURITY SCAN SUMMARY =====")
    print("\nVulnerabilities by severity:")
    print(f"{'SEVERITY':<10} {'FRONTEND':<10} {'BACKEND':<10} {'TOTAL':<10}")
    print("-" * 40)
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
        print(f"{severity:<10} {frontend_counts.get(severity, 0):<10} {backend_counts.get(severity, 0):<10} {total_counts.get(severity, 0):<10}")
    
    # Determine risk level
    risk_level = "LOW"
    if total_counts.get("CRITICAL", 0) > 0 or total_counts.get("HIGH", 0) > 10:
        risk_level = "HIGH"
    elif total_counts.get("HIGH", 0) > 0 or total_counts.get("MEDIUM", 0) > 10:
        risk_level = "MEDIUM"
    
    print("\nOverall Risk Assessment:", risk_level)
    print("==============================\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
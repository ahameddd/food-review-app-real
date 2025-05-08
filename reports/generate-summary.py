#!/usr/bin/env python3
"""
Generate a security summary report from Trivy scan results
"""

import json
import os
import sys
from datetime import datetime

# Get the script directory for correct file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_scan_results(filename):
    """Load Trivy scan results from a JSON file"""
    filepath = os.path.join(SCRIPT_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: File {filepath} is not valid JSON: {str(e)}")
        return None

def count_vulnerabilities_by_severity(results):
    """Count vulnerabilities by severity"""
    if not results or 'Results' not in results:
        return {}
    
    counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "UNKNOWN": 0
    }
    
    for result in results['Results']:
        if 'Vulnerabilities' not in result:
            continue
        
        for vuln in result['Vulnerabilities']:
            severity = vuln.get('Severity', 'UNKNOWN').upper()
            if severity in counts:
                counts[severity] += 1
    
    return counts

def generate_report():
    """Generate a security summary report"""
    frontend_results = load_scan_results('frontend-scan.json')
    backend_results = load_scan_results('backend-scan.json')
    
    if not frontend_results or not backend_results:
        print("Error: Could not load scan results")
        return 1
    
    frontend_counts = count_vulnerabilities_by_severity(frontend_results)
    backend_counts = count_vulnerabilities_by_severity(backend_results)
    
    # Calculate totals
    total_counts = {}
    for severity in frontend_counts:
        total_counts[severity] = frontend_counts.get(severity, 0) + backend_counts.get(severity, 0)
    
    # Generate report
    report = {
        "generated_at": datetime.now().isoformat(),
        "images_scanned": [
            frontend_results.get('ArtifactName', 'frontend'),
            backend_results.get('ArtifactName', 'backend')
        ],
        "frontend_vulnerabilities": frontend_counts,
        "backend_vulnerabilities": backend_counts,
        "total_vulnerabilities": total_counts,
        "risk_assessment": "HIGH" if (total_counts.get("CRITICAL", 0) > 0 or total_counts.get("HIGH", 0) > 10) else 
                           "MEDIUM" if (total_counts.get("HIGH", 0) > 0 or total_counts.get("MEDIUM", 0) > 10) else 
                           "LOW"
    }
    
    # Save report to file
    output_filepath = os.path.join(SCRIPT_DIR, 'security-summary.json')
    with open(output_filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary to console
    print("\n===== SECURITY SCAN SUMMARY =====")
    print(f"Generated at: {report['generated_at']}")
    print(f"Images scanned: {', '.join(report['images_scanned'])}")
    print("\nVulnerabilities by severity:")
    print(f"{'SEVERITY':<10} {'FRONTEND':<10} {'BACKEND':<10} {'TOTAL':<10}")
    print("-" * 40)
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
        print(f"{severity:<10} {frontend_counts.get(severity, 0):<10} {backend_counts.get(severity, 0):<10} {total_counts.get(severity, 0):<10}")
    
    print("\nOverall Risk Assessment:", report["risk_assessment"])
    print("==============================\n")
    
    print(f"Detailed report saved to: {output_filepath}")
    
    # Return exit code based on risk assessment
    if report["risk_assessment"] == "HIGH":
        return 2
    elif report["risk_assessment"] == "MEDIUM":
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(generate_report()) 
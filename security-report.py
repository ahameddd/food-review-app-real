import json
import os
import sys

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def analyze_scan_results(results):
    if results is None:
        return {"error": "No data found"}
    
    vulnerability_count = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "UNKNOWN": 0
    }
    
    vulnerability_details = []
    
    # Trivy sometimes changes its output format, so we need to handle different structures
    if isinstance(results, list):
        for result in results:
            if "Results" in result:
                for scan_result in result.get("Results", []):
                    for vuln in scan_result.get("Vulnerabilities", []):
                        severity = vuln.get("Severity", "UNKNOWN")
                        vulnerability_count[severity] += 1
                        vulnerability_details.append({
                            "ID": vuln.get("VulnerabilityID", "Unknown"),
                            "Package": vuln.get("PkgName", "Unknown"),
                            "Severity": severity,
                            "Title": vuln.get("Title", "No title provided")
                        })
    
    return {
        "counts": vulnerability_count,
        "details": vulnerability_details[:10]  # Show only top 10 vulnerabilities
    }

def main():
    frontend_path = os.path.join("reports", "frontend-scan.json")
    backend_path = os.path.join("reports", "backend-scan.json")
    
    print("=== Security Scan Analysis ===\n")
    
    # Check if files exist
    files_to_check = [frontend_path, backend_path]
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"Warning: Scan result file not found: {file_path}")
    
    # Frontend scan
    print("Frontend Scan Results:")
    frontend_results = load_json_file(frontend_path)
    if frontend_results:
        frontend_analysis = analyze_scan_results(frontend_results)
        print(f"  Vulnerabilities found: {sum(frontend_analysis['counts'].values())}")
        for severity, count in frontend_analysis['counts'].items():
            print(f"    {severity}: {count}")
        
        if frontend_analysis['details']:
            print("\n  Notable vulnerabilities:")
            for vuln in frontend_analysis['details']:
                print(f"    - {vuln['ID']} ({vuln['Severity']}): {vuln['Title']} in {vuln['Package']}")
        else:
            print("  No vulnerabilities found or empty scan result.")
    
    print("\n" + "-" * 40 + "\n")
    
    # Backend scan
    print("Backend Scan Results:")
    backend_results = load_json_file(backend_path)
    if backend_results:
        backend_analysis = analyze_scan_results(backend_results)
        print(f"  Vulnerabilities found: {sum(backend_analysis['counts'].values())}")
        for severity, count in backend_analysis['counts'].items():
            print(f"    {severity}: {count}")
        
        if backend_analysis['details']:
            print("\n  Notable vulnerabilities:")
            for vuln in backend_analysis['details']:
                print(f"    - {vuln['ID']} ({vuln['Severity']}): {vuln['Title']} in {vuln['Package']}")
        else:
            print("  No vulnerabilities found or empty scan result.")
    
    # Summary
    print("\n" + "=" * 40)
    print("Security Scan Summary")
    print("=" * 40)
    
    fe_count = sum(analyze_scan_results(frontend_results)['counts'].values()) if frontend_results else 0
    be_count = sum(analyze_scan_results(backend_results)['counts'].values()) if backend_results else 0
    
    print(f"Total vulnerabilities: {fe_count + be_count}")
    print(f"  Frontend: {fe_count}")
    print(f"  Backend: {be_count}")
    
    if fe_count + be_count == 0:
        print("\nNo vulnerabilities detected! Your containers appear to be secure.")
    else:
        print("\nRecommendation: Review the detailed scan reports in the 'reports' directory")
        print("and update dependencies to resolve identified vulnerabilities.")

if __name__ == "__main__":
    main() 
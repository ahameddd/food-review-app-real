#!/usr/bin/env python3
"""
Security Audit Script
---------------------
This script performs a security audit on the project code to identify
potential security vulnerabilities.
"""

import os
import re
import sys
import subprocess
import json
from datetime import datetime

def check_dependency_vulnerabilities():
    """Check for vulnerable dependencies using pip-audit."""
    try:
        print("Checking for vulnerable dependencies...")
        result = subprocess.run(
            ["pip-audit", "-r", "requirements.txt", "--format", "json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Warning: pip-audit completed with errors")
            
        # Parse results
        try:
            audit_results = json.loads(result.stdout)
            vulnerabilities = []
            
            for dep in audit_results.get("dependencies", []):
                for vuln in dep.get("vulnerabilities", []):
                    vulnerabilities.append({
                        "package": dep.get("name"),
                        "version": dep.get("version"),
                        "vulnerability": vuln.get("id"),
                        "severity": vuln.get("severity"),
                        "description": vuln.get("description"),
                        "fix_version": vuln.get("fix_versions", ["unknown"])[0]
                    })
            
            return vulnerabilities
        except json.JSONDecodeError:
            print("Warning: Could not parse pip-audit output")
            return []
    except FileNotFoundError:
        print("Error: pip-audit not found. Install with 'pip install pip-audit'")
        return []

def check_security_patterns():
    """Check for security issues in code patterns."""
    issues = []
    
    patterns = {
        r"os\.system\s*\(": "OS command injection risk",
        r"subprocess\.call\s*\(": "Command injection risk if user input is used",
        r"subprocess\.Popen\s*\(": "Command injection risk if user input is used",
        r"eval\s*\(": "Eval is dangerous and should be avoided",
        r"exec\s*\(": "Exec is dangerous and should be avoided",
        r"request\.args\.get\([^,)]+\)": "Unsanitized query parameter usage",
        r"request\.form\.get\([^,)]+\)": "Unsanitized form data usage",
        r"json\.loads\(request\.data": "Unchecked JSON deserialization",
        r"pickle\.loads": "Unsafe deserialization with pickle",
        r"\.execute\(['\"]": "SQL injection risk with string queries",
        r"password.{0,20}=.{0,20}['\"][^'\"]+['\"]": "Hardcoded password",
        r"api.?key.{0,20}=.{0,20}['\"][^'\"]+['\"]": "Hardcoded API key",
        r"secret.{0,20}=.{0,20}['\"][^'\"]+['\"]": "Hardcoded secret",
        r"CORS\(.*origins.{0,10}=.{0,10}['\"]\\*.{0,3}['\"]": "CORS wildcard origin",
        r"jsonify\(.*\).*\n.*return": "Missing Content-Type headers in response",
        r"@app\.route.*methods=\[[^]]*['\"](PUT|DELETE)['\"]": "Missing CSRF protection for state-changing methods",
        r"render_template\([^,)]+,\s*[^)]*\)": "Template injection risk",
        r"<script>": "XSS risk with embedded script",
        r"\[\s*\{.*\}\s*\]\.join\(''\)": "Possible XSS with array-to-string conversion"
    }
    
    python_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    print(f"Analyzing {len(python_files)} Python files...")
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check each pattern
            for pattern, issue_desc in patterns.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Get context (line number and the matching line)
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.splitlines()[line_num - 1].strip()
                    
                    issues.append({
                        "file": file_path,
                        "line": line_num,
                        "code": line_content,
                        "issue": issue_desc,
                        "pattern": pattern
                    })
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
    
    return issues

def check_missing_security_headers():
    """Check for missing security headers in Flask app."""
    missing_headers = []
    
    # Look for app instance
    found_app = False
    app_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if "app = Flask" in content:
                            app_files.append(file_path)
                            found_app = True
                except Exception:
                    continue
    
    if not found_app:
        missing_headers.append({
            "issue": "Could not locate Flask app instance",
            "recommendation": "Ensure Flask app is properly initialized"
        })
        return missing_headers
    
    # Check for security headers in app files
    header_checks = {
        "X-Content-Type-Options": False,
        "X-XSS-Protection": False,
        "X-Frame-Options": False,
        "Content-Security-Policy": False,
        "Strict-Transport-Security": False,
        "flask_talisman": False
    }
    
    for file_path in app_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            for header in header_checks:
                if header in content:
                    header_checks[header] = True
        except Exception:
            continue
    
    # Add missing headers to the list
    for header, found in header_checks.items():
        if not found:
            if header == "flask_talisman":
                missing_headers.append({
                    "issue": "Flask-Talisman not found",
                    "recommendation": "Use Flask-Talisman for security headers"
                })
            else:
                missing_headers.append({
                    "issue": f"Missing security header: {header}",
                    "recommendation": f"Add {header} header to responses"
                })
    
    return missing_headers

def check_authentication_security():
    """Check for authentication and session security issues."""
    issues = []
    
    auth_patterns = {
        r"session\s*\[\s*['\"]\w+['\"]\s*\]\s*=": "Session data manipulation without validation",
        r"request\.cookies\.get\(": "Direct cookie access without validation",
        r"@app\.route.*methods.*login": "Login endpoint - ensure rate limiting is applied",
        r"token\s*=\s*request\.": "Token or auth data accessed from request"
    }
    
    python_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check if file deals with authentication
            if "login" in content.lower() or "auth" in content.lower() or "session" in content.lower():
                # Check for secure session configuration
                if "app.config['SESSION_COOKIE_SECURE'] = True" not in content:
                    issues.append({
                        "file": file_path,
                        "issue": "Session cookies not set to secure",
                        "recommendation": "Add app.config['SESSION_COOKIE_SECURE'] = True"
                    })
                
                if "app.config['SESSION_COOKIE_HTTPONLY'] = True" not in content:
                    issues.append({
                        "file": file_path,
                        "issue": "Session cookies not set to HttpOnly",
                        "recommendation": "Add app.config['SESSION_COOKIE_HTTPONLY'] = True"
                    })
                
                # Check for patterns
                for pattern, issue_desc in auth_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Get context
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = content.splitlines()[line_num - 1].strip()
                        
                        issues.append({
                            "file": file_path,
                            "line": line_num,
                            "code": line_content,
                            "issue": issue_desc
                        })
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
    
    return issues

def main():
    print("="*80)
    print("Security Audit Report")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check for vulnerable dependencies
    vulnerabilities = check_dependency_vulnerabilities()
    if vulnerabilities:
        print("\nVulnerable Dependencies:")
        print("-"*80)
        for vuln in vulnerabilities:
            print(f"Package: {vuln['package']} (v{vuln['version']})")
            print(f"Vulnerability: {vuln['vulnerability']} ({vuln['severity']})")
            print(f"Description: {vuln['description']}")
            print(f"Fixed in: v{vuln['fix_version']}")
            print()
    else:
        print("\nNo vulnerable dependencies found.")
    
    # Check for security issues in code
    code_issues = check_security_patterns()
    if code_issues:
        print("\nCode Security Issues:")
        print("-"*80)
        for issue in code_issues:
            print(f"File: {issue['file']}, Line: {issue['line']}")
            print(f"Issue: {issue['issue']}")
            print(f"Code: {issue['code']}")
            print()
    else:
        print("\nNo code security issues found.")
    
    # Check for missing security headers
    header_issues = check_missing_security_headers()
    if header_issues:
        print("\nSecurity Header Issues:")
        print("-"*80)
        for issue in header_issues:
            print(f"Issue: {issue['issue']}")
            print(f"Recommendation: {issue['recommendation']}")
            print()
    else:
        print("\nNo security header issues found.")
    
    # Check authentication security
    auth_issues = check_authentication_security()
    if auth_issues:
        print("\nAuthentication Security Issues:")
        print("-"*80)
        for issue in auth_issues:
            if "line" in issue:
                print(f"File: {issue['file']}, Line: {issue['line']}")
                print(f"Issue: {issue['issue']}")
                print(f"Code: {issue['code']}")
            else:
                print(f"File: {issue['file']}")
                print(f"Issue: {issue['issue']}")
                print(f"Recommendation: {issue['recommendation']}")
            print()
    else:
        print("\nNo authentication security issues found.")
    
    # Generate recommendations
    print("\nRecommendations:")
    print("-"*80)
    if vulnerabilities:
        print("1. Update vulnerable dependencies to their fixed versions")
    if code_issues:
        print("2. Review and fix code issues, focusing on input validation and sanitization")
    if header_issues:
        print("3. Implement missing security headers using Flask-Talisman")
    if auth_issues:
        print("4. Improve authentication security with proper session configuration")
    
    print("\nAdditional Recommendations:")
    print("5. Implement CSP (Content Security Policy) to mitigate XSS attacks")
    print("6. Use parameterized queries to prevent SQL injection")
    print("7. Add rate limiting to all API endpoints, especially authentication")
    print("8. Implement CSRF protection for state-changing requests")
    print("9. Ensure proper input validation and sanitization")
    print("10. Implement proper error handling to avoid information disclosure")
    
    # Write report to file
    report_filename = f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"Security Audit Report\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Write vulnerable dependencies
        f.write("Vulnerable Dependencies:\n")
        f.write("-"*80 + "\n")
        if vulnerabilities:
            for vuln in vulnerabilities:
                f.write(f"Package: {vuln['package']} (v{vuln['version']})\n")
                f.write(f"Vulnerability: {vuln['vulnerability']} ({vuln['severity']})\n")
                f.write(f"Description: {vuln['description']}\n")
                f.write(f"Fixed in: v{vuln['fix_version']}\n\n")
        else:
            f.write("No vulnerable dependencies found.\n\n")
        
        # Write code issues
        f.write("Code Security Issues:\n")
        f.write("-"*80 + "\n")
        if code_issues:
            for issue in code_issues:
                f.write(f"File: {issue['file']}, Line: {issue['line']}\n")
                f.write(f"Issue: {issue['issue']}\n")
                f.write(f"Code: {issue['code']}\n\n")
        else:
            f.write("No code security issues found.\n\n")
        
        # Write header issues
        f.write("Security Header Issues:\n")
        f.write("-"*80 + "\n")
        if header_issues:
            for issue in header_issues:
                f.write(f"Issue: {issue['issue']}\n")
                f.write(f"Recommendation: {issue['recommendation']}\n\n")
        else:
            f.write("No security header issues found.\n\n")
        
        # Write authentication issues
        f.write("Authentication Security Issues:\n")
        f.write("-"*80 + "\n")
        if auth_issues:
            for issue in auth_issues:
                if "line" in issue:
                    f.write(f"File: {issue['file']}, Line: {issue['line']}\n")
                    f.write(f"Issue: {issue['issue']}\n")
                    f.write(f"Code: {issue['code']}\n\n")
                else:
                    f.write(f"File: {issue['file']}\n")
                    f.write(f"Issue: {issue['issue']}\n")
                    f.write(f"Recommendation: {issue['recommendation']}\n\n")
        else:
            f.write("No authentication security issues found.\n\n")
        
        # Write recommendations
        f.write("Recommendations:\n")
        f.write("-"*80 + "\n")
        if vulnerabilities:
            f.write("1. Update vulnerable dependencies to their fixed versions\n")
        if code_issues:
            f.write("2. Review and fix code issues, focusing on input validation and sanitization\n")
        if header_issues:
            f.write("3. Implement missing security headers using Flask-Talisman\n")
        if auth_issues:
            f.write("4. Improve authentication security with proper session configuration\n")
        
        f.write("\nAdditional Recommendations:\n")
        f.write("5. Implement CSP (Content Security Policy) to mitigate XSS attacks\n")
        f.write("6. Use parameterized queries to prevent SQL injection\n")
        f.write("7. Add rate limiting to all API endpoints, especially authentication\n")
        f.write("8. Implement CSRF protection for state-changing requests\n")
        f.write("9. Ensure proper input validation and sanitization\n")
        f.write("10. Implement proper error handling to avoid information disclosure\n")
    
    print(f"\nReport written to: {report_filename}")

if __name__ == "__main__":
    main() 
import subprocess
import json
import os

def run_bandit_scan(file_path):
    """
    Bandit is a security tool that reads Python code and
    detects dangerous patterns — like hardcoded passwords,
    use of eval(), SQL injection risks etc.
    """
    try:
        result = subprocess.run(
            ["bandit", "-r", file_path, "-f", "json", "-q"],
            capture_output=True,
            text=True
        )
        
        # Bandit returns JSON — parse it
        if result.stdout:
            data = json.loads(result.stdout)
            issues = data.get("results", [])
            
            formatted = []
            for issue in issues:
                formatted.append({
                    "file": issue.get("filename"),
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),  # LOW, MEDIUM, HIGH
                    "confidence": issue.get("issue_confidence"),
                    "issue": issue.get("issue_text"),
                    "code": issue.get("code"),
                })
            return formatted
        return []
        
    except FileNotFoundError:
        print("Bandit not found — run: pip install bandit")
        return []
    except json.JSONDecodeError:
        return []

def scan_repository(repo_path):
    """Scan every Python file in a folder for security issues."""
    all_issues = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                issues = run_bandit_scan(full_path)
                all_issues.extend(issues)
                print(f"Scanned: {file} — {len(issues)} issues found")
    
    return all_issues

def get_severity_summary(issues):
    """Count how many HIGH, MEDIUM, LOW issues exist."""
    summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for issue in issues:
        severity = issue.get("severity", "LOW").upper()
        if severity in summary:
            summary[severity] += 1
    return summary

if __name__ == "__main__":
    # Create a test file with intentional vulnerabilities
    test_code = """
import os
import subprocess

password = "hardcoded_secret_123"
api_key = "sk-abc123supersecret"

def run_command(user_input):
    os.system(user_input)

def evaluate_code(code_string):
    eval(code_string)

def get_user(username):
    query = "SELECT * FROM users WHERE name = " + username
    return query
"""
    # Write test file
    with open("test_vulnerable.py", "w") as f:
        f.write(test_code)
    
    print("Scanning test_vulnerable.py for security issues...\n")
    issues = run_bandit_scan("test_vulnerable.py")
    
    print(f"\nFound {len(issues)} security issues:\n")
    for issue in issues:
        print(f"  Line {issue['line']} | {issue['severity']} | {issue['issue']}")
    
    print(f"\nSummary: {get_severity_summary(issues)}")
    
    # Clean up test file
    os.remove("test_vulnerable.py")
"""Code Review Plugin — Analyze Python code for issues."""
import ast
import re
from typing import Dict, Any, List

def analyze_code(code: str, filename: str = "unknown.py") -> Dict[str, Any]:
    """Analyze Python code for syntax errors, style issues, and potential bugs."""
    issues: List[Dict[str, Any]] = []
    warnings: List[str] = []
    
    # Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "status": "error",
            "error_type": "syntax_error",
            "message": str(e),
            "line": e.lineno,
            "col": e.offset,
            "filename": filename,
        }
    
    # Check for bare except
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append({
                    "type": "except",
                    "severity": "warning",
                    "message": "Bare 'except' clause — catches all exceptions including KeyboardInterrupt",
                    "line": node.lineno,
                })
    
    # Check for unused imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.asname or alias.name)
    
    # Simple usage check
    for imp in list(imports):
        if imp not in code or code.count(imp) <= 1:
            issues.append({
                "type": "import",
                "severity": "info",
                "message": f"Import '{imp}' may be unused",
                "line": 0,
            })
    
    # Check for hardcoded passwords
    if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', code, re.IGNORECASE):
        issues.append({
            "type": "security",
            "severity": "critical",
            "message": "Hardcoded password/secret detected",
            "line": 0,
        })
    
    # Line length check
    for i, line in enumerate(code.split('\n'), 1):
        if len(line) > 100:
            issues.append({
                "type": "style",
                "severity": "low",
                "message": f"Line {i} exceeds 100 characters ({len(line)})",
                "line": i,
            })
    
    return {
        "status": "analyzed",
        "filename": filename,
        "issues": issues,
        "issue_count": len(issues),
        "warnings": warnings,
    }

# Plugin manifest
PLUGIN_INFO = {
    "name": "code-review",
    "version": "1.0.0",
    "description": "Analyze Python code for syntax errors, style issues, and potential bugs",
}

# Tool registry
TOOLS = {
    "analyze_code": analyze_code,
}

def get_tools():
    return TOOLS

# Code Review Skill

## Description
Review code for security, quality, and best practices.

## Trigger Keywords
- review code, code review, tinjau kode, periksa kode, check code, review

## Behavior Contract

### 1. Read Code Carefully
- Identify the programming language and framework
- Map the code structure and data flow
- Note any external dependencies or API calls

### 2. Check Security
- **Critical**: SQL injection, XSS, CSRF, auth bypass, RCE
- **High**: Insecure deserialization, path traversal, SSRF
- **Medium**: Missing input validation, weak crypto, hardcoded secrets
- **Info**: Missing rate limiting, verbose error messages

### 3. Check Quality
- Code duplication and DRY violations
- Proper error handling and logging
- Naming conventions and readability
- Performance concerns (N+1 queries, memory leaks)

### 4. Check Best Practices
- SOLID principles adherence
- Design patterns usage
- Testing coverage indicators
- Documentation completeness

### 5. Output Format
- Group findings by severity (critical → info)
- For each finding: what, where, why, fix suggestion
- End with overall assessment score (1-10)

## Output Example
```
## Code Review Results

### Critical
1. **SQL Injection in login handler** (line 42)
   - Vulnerability: user input concatenated directly into query
   - Fix: Use parameterized queries

### Warnings
1. **Missing input validation** (line 15)
   - Issue: email field not validated
   - Fix: Add regex validation

Overall: 6/10 — needs security improvements
```

## Constraints
- Never execute code being reviewed
- Never modify source code directly (suggest only)
- Always explain the "why" behind each finding
- Prioritize security over style

# Tool Execution Skill

## Description
Execute system commands, read files, check system status.

## Trigger Keywords
- jalankan, execute, run, baca file, cek, check, install, build, test, deploy, status

## Behavior Contract

### 1. Identify Command Type
- Shell commands (ls, cat, git, npm, etc.)
- File operations (read, write, edit)
- System checks (disk, memory, processes)

### 2. Validate Safety
- Refuse dangerous commands (rm -rf /, chmod 777, etc.)
- Validate file paths (no sandbox escape)
- Check command injection

### 3. Execute (via Hermes terminal tool)
- Run command safely
- Capture stdout/stderr
- Return structured output

### 4. Output Format
```
## Command: [command]
```
[output]
```

Status: [success/error]
```

## Constraints
- Never execute destructive commands
- Always validate paths
- Log all command execution
- Return structured output

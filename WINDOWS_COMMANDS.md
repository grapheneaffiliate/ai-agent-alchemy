# Windows PowerShell Command Reference

**CRITICAL: This system runs on Windows PowerShell, NOT bash/Unix**

## Common Command Mistakes to Avoid

### ❌ DO NOT USE (Unix/Linux)
- `head` - Does not exist in PowerShell
- `tail` - Does not exist in PowerShell
- `grep` - Does not exist in PowerShell
- `cat` - Use `Get-Content` instead
- `ls` - Use `Get-ChildItem` or `dir`
- `rm` - Use `Remove-Item`
- `mv` - Use `Move-Item`
- `cp` - Use `Copy-Item`

### ✅ USE INSTEAD (PowerShell)

| Task | Unix | PowerShell |
|------|------|------------|
| First N lines | `head -n 10 file.txt` | `Get-Content file.txt -Head 10` |
| Last N lines | `tail -n 10 file.txt` | `Get-Content file.txt -Tail 10` |
| Search text | `grep "pattern" file` | `Select-String "pattern" file` |
| List files | `ls` | `Get-ChildItem` or `dir` |
| Read file | `cat file.txt` | `Get-Content file.txt` |
| Delete file | `rm file.txt` | `Remove-Item file.txt` |
| Move file | `mv old new` | `Move-Item old new` |
| Copy file | `cp old new` | `Copy-Item old new` |
| Find command | `which cmd` | `Get-Command cmd` |
| Environment | `echo $PATH` | `$env:PATH` |

## Piping Output

### First N lines of command output:
```powershell
# ❌ Wrong
python script.py | head -n 50

# ✅ Correct
python script.py | Select-Object -First 50
```

### Search in output:
```powershell
# ❌ Wrong
python script.py | grep "error"

# ✅ Correct
python script.py | Select-String "error"
```

### Redirect output:
```powershell
# Both work similarly
python script.py > output.txt          # Overwrite
python script.py >> output.txt         # Append
python script.py 2>&1 | Out-File log.txt  # With errors
```

## Common Patterns

### Read first 100 lines of Python output:
```powershell
python -m src.agent.cli run | Select-Object -First 100
```

### Test and capture output:
```powershell
python test_script.py 2>&1 | Tee-Object -FilePath log.txt
```

### Check if command exists:
```powershell
Get-Command python -ErrorAction SilentlyContinue
```

## System Information

- **OS**: Windows 11
- **Shell**: PowerShell (cmd.exe as default but PowerShell available)
- **Python**: Available via `python` command
- **Working Directory**: c:\Users\atchi\spec-kit

## Quick Reference

Always remember:
1. Check SYSTEM INFORMATION in environment_details
2. It says "Default Shell: C:\WINDOWS\system32\cmd.exe"
3. PowerShell commands work in cmd.exe context
4. When in doubt, use PowerShell-native commands
5. Test commands don't fail with "not recognized" errors

## Auto-Reminder

Before running ANY command with pipes or utilities, ask:
- "Is this a Unix command?"
- "Am I on Windows?"
- "Should I use PowerShell equivalent?"

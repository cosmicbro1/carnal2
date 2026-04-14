#!/usr/bin/env python
"""
Demo: Testing Carnal's agent capabilities
"""
import json
import platform
from agents import toolkit

print("=" * 60)
print("CARNAL 2.0 - AGENT SYSTEM DEMO")
print("=" * 60)

# 1. List files
print("\n[1] Listing files in project...")
result = toolkit.list_files(".")
print(json.dumps(result, indent=2))

# 2. Read a file
print("\n[2] Reading README.md...")
result = toolkit.read_file("README.md")
if "content" in result:
    print(result["content"][:500] + "...")
else:
    print(result)

# 3. Python code execution
print("\n[3] Executing Python code...")
code = """
import math
result = math.sqrt(16) + 2**3
print(f'Math result: {result}')
"""
result = toolkit.execute_python(code)
print(json.dumps(result, indent=2))

# 4. Command execution
print("\n[4] Executing system command...")
if platform.system() == "Windows":
    cmd = "dir"
else:
    cmd = "ls -la"
result = toolkit.execute_command(cmd, shell=True)
print(json.dumps(result, indent=2)[:500])

# 5. Execution logs
print("\n[5] Execution logs:")
for log in toolkit.get_logs():
    print(f"  - {log['type']}: {log.get('status', 'unknown')}")

print("\n" + "=" * 60)
print("Agent system is working! 🤖")
print("=" * 60)

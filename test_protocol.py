#!/usr/bin/env python
"""Test MCP protocol via subprocess."""

import subprocess
import json
import time

# Start server process
proc = subprocess.Popen(
    ['.venv/bin/python', '-m', 'src.server'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Send initialize
init_msg = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}

print("Sending initialize...")
proc.stdin.write(json.dumps(init_msg) + '\n')
proc.stdin.flush()

# Wait and read response
time.sleep(1)
print("\nWaiting for response...")

try:
    # Try to read with timeout
    import select
    ready, _, _ = select.select([proc.stdout], [], [], 2)
    if ready:
        response = proc.stdout.readline()
        print(f"Response: {response}")

        # Parse and pretty print
        if response:
            resp_obj = json.loads(response)
            print(f"\n✅ Got response:")
            print(json.dumps(resp_obj, indent=2))
    else:
        print("❌ No response within timeout")

    # Check stderr
    ready, _, _ = select.select([proc.stderr], [], [], 0.1)
    if ready:
        errors = proc.stderr.read()
        if errors:
            print(f"\n⚠️ Stderr: {errors}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    proc.terminate()
    proc.wait(timeout=2)

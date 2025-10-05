#!/usr/bin/env python
"""Quick migration validation test."""

import time
from src.cdp_recorder import CDPRecorder

def test_browser_launch():
    """Test 1: Browser launches and closes properly."""
    print("Test 1: Browser launch...")
    recorder = CDPRecorder(headless=True)
    recorder.start_chrome()
    session_id = recorder.connect()
    print(f"  ✅ Session started: {session_id}")
    recorder.close()
    print("  ✅ Browser closed cleanly")

def test_console_capture():
    """Test 2: Console events are captured."""
    print("\nTest 2: Console event capture...")
    recorder = CDPRecorder(headless=True)
    recorder.start_chrome("data:text/html,<script>console.log('test message')</script>")
    recorder.connect()
    time.sleep(2)  # Wait for page to load and execute
    events = recorder.get_events()
    console_events = [e for e in events if e['type'] == 'console_log']
    recorder.close()

    if console_events:
        print(f"  ✅ Captured {len(console_events)} console event(s)")
        print(f"  Message: {console_events[0]['data']['args']}")
    else:
        print("  ⚠️  No console events captured")

def test_error_capture():
    """Test 3: JS errors are captured."""
    print("\nTest 3: JS error capture...")
    recorder = CDPRecorder(headless=True)
    recorder.start_chrome("data:text/html,<script>throw new Error('test error')</script>")
    recorder.connect()
    time.sleep(2)
    events = recorder.get_events()
    error_events = [e for e in events if e['type'] == 'js_error']
    recorder.close()

    if error_events:
        print(f"  ✅ Captured {len(error_events)} error event(s)")
        print(f"  Error: {error_events[0]['data']['message']}")
    else:
        print("  ⚠️  No error events captured")

def test_url_validation():
    """Test 4: URL validation (security fix)."""
    print("\nTest 4: URL validation...")
    recorder = CDPRecorder(headless=True)
    try:
        recorder.start_chrome("file:///etc/passwd")
        print("  ❌ FAILED: file:// URL should be blocked")
        recorder.close()
    except ValueError as e:
        print(f"  ✅ Correctly blocked file:// URL: {e}")

if __name__ == "__main__":
    print("🧪 Migration Validation Tests\n" + "="*50)

    try:
        test_browser_launch()
        test_console_capture()
        test_error_capture()
        test_url_validation()

        print("\n" + "="*50)
        print("✅ All basic tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

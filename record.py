#!/usr/bin/env python
"""Simple CLI wrapper for recording browser sessions."""

import sys
import time
from src.cdp_recorder import CDPRecorder
from src.event_processor import EventProcessor
from src.storage import RecordingStorage

def main():
    if len(sys.argv) < 2:
        print("Usage: python record.py <url>")
        sys.exit(1)

    url = sys.argv[1]

    # Setup
    storage = RecordingStorage(recordings_dir="recordings")
    event_processor = EventProcessor()

    # Start recording
    print(f"Starting Chrome and recording session for: {url}")
    recorder = CDPRecorder()
    recorder.start_chrome(url=url)
    session_id = recorder.connect()

    print(f"\n✅ Recording started!")
    print(f"📝 Session ID: {session_id}")
    print(f"🌐 Chrome opened at: {url}")
    print("\n👉 Interact with the browser now...")
    print("   Press ENTER when done to stop recording\n")

    # Wait for user
    input()

    # Stop and save
    print("\n⏹️  Stopping recording...")
    session_data = recorder.stop()

    processed_events = event_processor.process_events(session_data["events"])
    session_data["events"] = processed_events

    file_path = storage.save_recording(session_data, url=url)

    recorder.close()

    print(f"\n✅ Recording saved to: {file_path}")
    print(f"📊 Total events: {len(processed_events)}")

    # Show summary
    summary = event_processor.analyze_events(processed_events)
    print(f"\n📈 Summary:")
    print(f"   - DOM mutations: {summary['dom_mutations']}")
    print(f"   - Console logs: {summary['console_logs']}")
    print(f"   - JS errors: {summary['js_errors']}")
    print(f"   - Masked events: {summary['masked_events']}")
    print(f"\n💾 Session ID: {session_id}")

if __name__ == "__main__":
    main()

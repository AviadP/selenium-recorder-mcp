"""MCP server for Selenium test recording."""

import os
import re
import json
from typing import Optional, Any

import mcp.types as types
from mcp.server import Server

from .cdp_recorder import CDPRecorder
from .event_processor import EventProcessor
from .storage import RecordingStorage


app = Server("selenium-recorder")

active_recorders: dict[str, CDPRecorder] = {}
storage = RecordingStorage(recordings_dir="recordings")
event_processor = EventProcessor()


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="start_recording",
            description="Start recording browser interactions. Opens Chrome and records DOM mutations, console logs, and JS errors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Optional URL to navigate to on start",
                    },
                    "sensitive_selectors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional additional CSS selectors for sensitive fields to mask",
                    },
                },
            },
        ),
        types.Tool(
            name="stop_recording",
            description="Stop recording session and save to JSON file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from start_recording",
                    },
                },
                "required": ["session_id"],
            },
        ),
        types.Tool(
            name="get_recording",
            description="Get recording metadata by session ID. Returns event type breakdown and file path by default. Use filters (limit, event_types, offset, timestamps) to retrieve actual events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to retrieve",
                    },
                    "event_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by event types (e.g., ['click', 'console_log']). If omitted, returns all types.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of events to return. If omitted, returns all events.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of events to skip before returning results (for pagination). Default: 0",
                    },
                    "from_timestamp": {
                        "type": "string",
                        "description": "ISO timestamp - only return events after this time",
                    },
                    "to_timestamp": {
                        "type": "string",
                        "description": "ISO timestamp - only return events before this time",
                    },
                },
                "required": ["session_id"],
            },
        ),
        types.Tool(
            name="analyze_recording",
            description="Analyze recording and get summary statistics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to analyze",
                    },
                },
                "required": ["session_id"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}

    if name == "start_recording":
        return await start_recording(arguments)
    if name == "stop_recording":
        return await stop_recording(arguments)
    if name == "get_recording":
        return await get_recording(arguments)
    if name == "analyze_recording":
        return await analyze_recording(arguments)

    raise ValueError(f"Unknown tool: {name}")


async def start_recording(arguments: dict) -> list[types.TextContent]:
    """
    Start recording browser session.

    Args:
        arguments (dict): Tool arguments with optional url and sensitive_selectors.

    Returns:
        list[types.TextContent]: Response with session_id.
    """
    url = arguments.get("url")
    sensitive_selectors = arguments.get("sensitive_selectors", [])

    # Playwright handles browser location automatically
    headless = os.environ.get("HEADLESS", "false").lower() == "true"

    recorder = CDPRecorder(headless=headless)
    await recorder.start_chrome(url=url)
    session_id = await recorder.connect()

    active_recorders[session_id] = recorder

    global event_processor
    if sensitive_selectors:
        event_processor = EventProcessor(sensitive_selectors=sensitive_selectors)

    return [
        types.TextContent(
            type="text",
            text=f"Recording started. Session ID: {session_id}\n"
            f"Chrome browser opened{' at ' + url if url else ''}.\n"
            "Interact with the browser manually. Call stop_recording when done.",
        )
    ]


async def stop_recording(arguments: dict) -> list[types.TextContent]:
    """
    Stop recording and save to file.

    Args:
        arguments (dict): Tool arguments with session_id.

    Returns:
        list[types.TextContent]: Response with file path.
    """
    session_id = arguments.get("session_id")
    if not session_id:
        raise ValueError("session_id is required")

    # Validate session_id format (security - prevent injection)
    if not re.match(r'^[a-f0-9-]{36}$', session_id):
        raise ValueError("Invalid session_id format")

    recorder = active_recorders.get(session_id)
    if not recorder:
        raise ValueError(f"No active recording found for session: {session_id}")

    try:
        session_data = recorder.stop()

        processed_events = event_processor.process_events(session_data["events"])
        session_data["events"] = processed_events

        file_path = storage.save_recording(session_data)
    finally:
        # Ensure cleanup happens even if processing fails
        try:
            await recorder.close()
        finally:
            if session_id in active_recorders:
                del active_recorders[session_id]

    return [
        types.TextContent(
            type="text",
            text=f"Recording stopped and saved to: {file_path}\n"
            f"Total events recorded: {len(processed_events)}",
        )
    ]


async def get_recording(arguments: dict) -> list[types.TextContent]:
    """
    Get recording metadata or filtered events.

    Args:
        arguments (dict): Tool arguments with session_id and optional filters.

    Returns:
        list[types.TextContent]: Recording data - metadata only by default, events if filters provided.
    """
    session_id = arguments.get("session_id")
    if not session_id:
        raise ValueError("session_id is required")

    # Validate session_id format (security - prevent injection)
    if not re.match(r'^[a-f0-9-]{36}$', session_id):
        raise ValueError("Invalid session_id format")

    # Extract filter parameters
    event_types = arguments.get("event_types")
    limit = arguments.get("limit")
    offset = arguments.get("offset", 0)
    from_timestamp = arguments.get("from_timestamp")
    to_timestamp = arguments.get("to_timestamp")

    # Detect if any filters are provided
    has_filters = any([
        event_types,           # Non-empty list
        limit is not None,     # Explicit limit (including 0)
        from_timestamp,        # Timestamp provided
        to_timestamp,          # Timestamp provided
        offset > 0             # Positive offset
    ])

    # Load recording with or without events based on filters
    recording = storage.load_filtered_recording(
        session_id=session_id,
        event_types=event_types,
        limit=limit,
        offset=offset,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        include_events=has_filters,
    )

    if not recording:
        raise ValueError(f"Recording not found: {session_id}")

    # Build appropriate summary based on response type
    metadata = recording.get("metadata", {})
    file_path = recording.get("file_path", "")

    if "events" in recording:
        # Events included - show filter summary
        total = metadata.get("total_events", 0)
        returned = metadata.get("returned_events", 0)
        filters = metadata.get("filters_applied")

        summary = f"Session: {session_id}\n"
        summary += f"File: {file_path}\n"
        summary += f"Events: {returned}/{total}\n"
        if filters:
            summary += f"Filters: {json.dumps(filters, indent=2)}\n"
        summary += "\n"
    else:
        # Metadata only - show breakdown and usage instructions
        total = metadata.get("total_events", 0)
        breakdown = metadata.get("event_type_breakdown", {})

        summary = f"Session: {session_id}\n"
        summary += f"File: {file_path}\n"
        summary += f"Total events: {total}\n\n"
        summary += "Event type breakdown:\n"
        for event_type, count in sorted(breakdown.items(), key=lambda x: -x[1]):
            summary += f"  {event_type}: {count}\n"
        summary += f"\nℹ️  Use filters to retrieve events:\n"
        summary += f"   - limit: Max number of events to return\n"
        summary += f"   - event_types: List of event types to include\n"
        summary += f"   - offset: Skip first N events (pagination)\n"
        summary += f"   - from_timestamp/to_timestamp: Time range filter\n"
        summary += f"\nOr read the file directly: {file_path}\n"
        summary += "\n"

    return [
        types.TextContent(
            type="text",
            text=summary + json.dumps(recording, indent=2),
        )
    ]


async def analyze_recording(arguments: dict) -> list[types.TextContent]:
    """
    Analyze recording and get summary.

    Args:
        arguments (dict): Tool arguments with session_id.

    Returns:
        list[types.TextContent]: Analysis summary.
    """
    session_id = arguments.get("session_id")
    if not session_id:
        raise ValueError("session_id is required")

    # Validate session_id format (security - prevent injection)
    if not re.match(r'^[a-f0-9-]{36}$', session_id):
        raise ValueError("Invalid session_id format")

    recording = storage.load_recording(session_id)
    if not recording:
        raise ValueError(f"Recording not found: {session_id}")

    events = recording.get("events", [])
    summary = event_processor.analyze_events(events)

    return [
        types.TextContent(
            type="text",
            text=f"Recording Analysis for {session_id}:\n\n{json.dumps(summary, indent=2)}",
        )
    ]


async def main():
    """Run MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

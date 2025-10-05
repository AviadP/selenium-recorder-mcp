"""MCP server for Selenium test recording."""

import os
import json
from pathlib import Path
from typing import Optional, Any

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

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
            description="Get recording data by session ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to retrieve",
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

    chrome_path = os.environ.get(
        "CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )

    recorder = CDPRecorder(chrome_path=chrome_path)
    recorder.start_chrome(url=url)
    session_id = recorder.connect()

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

    recorder = active_recorders.get(session_id)
    if not recorder:
        raise ValueError(f"No active recording found for session: {session_id}")

    session_data = recorder.stop()

    processed_events = event_processor.process_events(session_data["events"])
    session_data["events"] = processed_events

    file_path = storage.save_recording(session_data)

    recorder.close()
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
    Get recording data.

    Args:
        arguments (dict): Tool arguments with session_id.

    Returns:
        list[types.TextContent]: Recording data as JSON.
    """
    session_id = arguments.get("session_id")
    if not session_id:
        raise ValueError("session_id is required")

    recording = storage.load_recording(session_id)
    if not recording:
        raise ValueError(f"Recording not found: {session_id}")

    return [
        types.TextContent(
            type="text",
            text=json.dumps(recording, indent=2),
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

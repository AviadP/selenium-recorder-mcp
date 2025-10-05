# Selenium Test Recorder MCP Server

MCP server for recording comprehensive browser interactions using Chrome DevTools Protocol (CDP). Records DOM mutations, console logs, and JavaScript errors while you manually interact with a website.

## Features

- **Click Tracking**: Captures every click with full element details (XPath, CSS selector, attributes, text content, coordinates)
- **Comprehensive Recording**: Captures DOM mutations, console logs, and JS errors
- **Manual Interaction**: Record while you manually navigate and interact with browser
- **Sensitive Field Masking**: Automatically masks password fields and other sensitive data
- **Smart Filtering**: Query recordings by event type, time range, or pagination - prevents large context dumps
- **Metadata-First**: See event breakdown before retrieving data - safe by default
- **JSON Output**: Structured data for analysis and test generation
- **Claude Code Integration**: Use via MCP tools in Claude Code

## What's New

### Smart Query Filtering (Breaking Change)

The `get_recording` tool now returns **metadata only by default** to prevent large responses that can fill up Claude's context window.

**Before:**
```
get_recording(session_id) → Returns all events (could be 70k+ tokens)
```

**Now:**
```
get_recording(session_id) → Returns metadata only (event breakdown, file path)
get_recording(session_id, limit=50) → Returns first 50 events
get_recording(session_id, event_types=["click"]) → Returns only click events
```

**Benefits:**
- ✅ No more accidental context overflow warnings
- ✅ See what's available before requesting data
- ✅ Filter to exactly what you need
- ✅ Paginate large recordings

**Migration:** Add any filter parameter to get events (e.g., `limit`, `event_types`, `offset`)

See [Querying Recordings with Filters](#querying-recordings-with-filters) for details.

## Installation

```bash
cd selenium-recorder-mcp
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Requirements

- Python 3.10+
- Google Chrome (or Chromium-based browser)
- macOS, Linux, or Windows

## Quick Start (Standalone Script)

**Easiest way to use - no MCP setup required:**

```bash
cd selenium-recorder-mcp
source .venv/bin/activate
python record.py https://www.example.com
```

This will:
1. Open Chrome at the URL
2. Start recording clicks, DOM mutations, console logs, and JS errors
3. Let you manually interact (login, navigate, click, etc.)
4. Press ENTER when done to stop recording
5. Save recording to `recordings/` folder as JSON

Example output:
```
✅ Recording started!
📝 Session ID: 550e8400-e29b-41d4-a716-446655440000
🌐 Chrome opened at: https://www.example.com

👉 Interact with the browser now...
   Press ENTER when done to stop recording

[... you interact with the browser ...]

⏹️  Stopping recording...
✅ Recording saved to: recordings/550e8400_20250930_143022.json
📊 Total events: 247

📈 Summary:
   - Clicks: 12
   - DOM mutations: 189
   - Console logs: 52
   - JS errors: 6
   - Masked events: 3
```

## Setup (MCP Server Integration)

### Configure Claude Code MCP

**Method 1: Using `claude mcp add` command (Recommended)**

From your terminal, run:

```bash
claude mcp add selenium-recorder \
  --scope user \
  -- /bin/zsh -lc '
    cd /path/to/selenium-recorder-mcp &&
    exec ./.venv/bin/python -m src.server
  '
```

Replace `/path/to/selenium-recorder-mcp` with your actual installation directory.

**If Chrome is not in the default location, add the `--env` flag:**

```bash
claude mcp add selenium-recorder \
  --scope user \
  --env CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  -- /bin/zsh -lc '
    cd /path/to/selenium-recorder-mcp &&
    exec ./.venv/bin/python -m src.server
  '
```

**Default Chrome paths:**
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Linux: `/usr/bin/google-chrome`
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`

**For bash users, replace `/bin/zsh -lc` with `/bin/bash -lc`**

**Notes:**
- `--scope user` makes it available across all your projects
- The `-lc` flag ensures a login shell with proper environment setup
- `exec` replaces the shell process with Python for cleaner process management

---

**Method 2: Manual JSON configuration (Alternative)**

Add to your Claude Code MCP settings (`~/.claude/mcp_settings.json`):

```json
{
  "mcpServers": {
    "selenium-recorder": {
      "command": "/path/to/selenium-recorder-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/selenium-recorder-mcp",
      "env": {
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

**Important:** Use absolute paths for both `command` and `cwd` fields.

## Usage

### Method 1: Standalone Script (Recommended for getting started)

```bash
python record.py https://www.sport5.co.il
```

1. Chrome opens automatically
2. Manually interact (login, navigate, click)
3. Press ENTER to stop
4. Recording saved to `recordings/` folder

Then share the recording JSON file with Claude Code for analysis or test generation!

### Method 2: MCP Server (Advanced - Claude Code Integration)

After configuring MCP settings and restarting Claude Code:

**Workflow:**
1. **Start Recording** - Opens Chrome and begins recording
2. **Manual Interaction** - Login, navigate, interact with the site
3. **Stop Recording** - Saves events to JSON file
4. **Analyze/Generate** - Use Claude Code to analyze or generate test code

**MCP Tools:**

#### `start_recording`

Start recording browser session.

**Parameters:**
- `url` (optional): URL to navigate to on start
- `sensitive_selectors` (optional): Additional CSS selectors for sensitive fields

**Returns:** Session ID

**Example:**
```
start_recording with url "https://example.com"
```

#### `stop_recording`

Stop recording and save to JSON.

**Parameters:**
- `session_id` (required): Session ID from start_recording

**Returns:** File path to saved recording

**Example:**
```
stop_recording with session_id "abc-123-def"
```

#### `get_recording`

Retrieve recording metadata or filtered events.

**Parameters:**
- `session_id` (required): Session ID to retrieve
- `event_types` (optional): Array of event types to filter (e.g., `["click", "console_log"]`)
- `limit` (optional): Maximum number of events to return
- `offset` (optional): Number of events to skip (for pagination)
- `from_timestamp` (optional): ISO timestamp - only return events after this time
- `to_timestamp` (optional): ISO timestamp - only return events before this time

**Returns:**
- **Without filters**: Metadata only (event type breakdown, file path, total count) - prevents large responses
- **With any filter**: Filtered events matching criteria

**Examples:**
```
# Get metadata only (safe, no large dumps)
get_recording with session_id "abc-123"

# Get first 50 events
get_recording with session_id "abc-123" and limit 50

# Get only click events
get_recording with session_id "abc-123" and event_types ["click"]

# Get clicks and DOM changes
get_recording with session_id "abc-123" and event_types ["click", "dom_attribute_modified"]
```

#### `analyze_recording`

Get summary statistics.

**Parameters:**
- `session_id` (required): Session ID to analyze

**Returns:** Event summary and counts

### Example Session with Claude Code

```
You: Start recording https://myapp.com/login

Claude: [calls start_recording]
Recording started. Session ID: 550e8400-e29b-41d4-a716-446655440000
Chrome browser opened at https://myapp.com/login.
Interact with the browser manually. Call stop_recording when done.

[You manually login and navigate through the app]

You: Stop recording with session_id 550e8400-e29b-41d4-a716-446655440000

Claude: [calls stop_recording]
Recording stopped and saved to: recordings/550e8400-e29b-41d4-a716-446655440000_20250115_143022.json
Total events recorded: 247

You: What's in the recording?

Claude: [calls get_recording with session_id only - no filters]
Session: 550e8400-e29b-41d4-a716-446655440000
File: recordings/550e8400-e29b-41d4-a716-446655440000_20250115_143022.json
Total events: 247

Event type breakdown:
  dom_attribute_modified: 89
  console_log: 52
  dom_set_child_nodes: 45
  click: 12
  dom_character_data_modified: 43
  js_error: 6

ℹ️  Use filters to retrieve events (limit, event_types, offset, timestamps)
Or read the file directly.

You: Show me just the click events

Claude: [calls get_recording with event_types=["click"]]
Session: 550e8400-e29b-41d4-a716-446655440000
Events: 12/247
Filters: {"event_types": ["click"]}

[Returns 12 click events with full details]

You: Generate a Selenium test from the click events

Claude: [uses the 12 click events to generate test code]
```

## Querying Recordings with Filters

The `get_recording` tool now supports powerful filtering to prevent large context dumps and retrieve only the data you need.

### Default Behavior (Metadata Only)

**Without any filters, `get_recording` returns metadata only:**

```
get_recording with session_id "abc-123"
```

**Returns:**
- Session information (URL, timestamps, file path)
- Total event count
- Event type breakdown (shows count per event type)
- Usage instructions
- **No events** - prevents accidentally filling context with large responses

This is **safe by default** and helps you understand what's in the recording before requesting specific data.

### Retrieving Events with Filters

**To get actual events, use any filter parameter:**

#### Limit Events (Pagination)
```
# First 50 events
get_recording with session_id "abc-123" and limit 50

# Next 50 events (pagination)
get_recording with session_id "abc-123" and limit 50 and offset 50
```

#### Filter by Event Type
```
# Only clicks
get_recording with session_id "abc-123" and event_types ["click"]

# Clicks and DOM mutations
get_recording with session_id "abc-123" and event_types ["click", "dom_attribute_modified", "dom_set_child_nodes"]

# Exclude noisy console logs - get everything else
get_recording with session_id "abc-123" and event_types ["click", "js_error", "dom_attribute_modified"]
```

#### Time Range Filtering
```
# Events after a specific time
get_recording with session_id "abc-123" and from_timestamp "2025-01-15T14:30:00"

# Events in a time window
get_recording with session_id "abc-123" and from_timestamp "2025-01-15T14:30:00" and to_timestamp "2025-01-15T14:35:00"
```

#### Combined Filters
```
# Click events only, first 100
get_recording with session_id "abc-123" and event_types ["click"] and limit 100

# Recent errors only
get_recording with session_id "abc-123" and event_types ["js_error"] and from_timestamp "2025-01-15T14:30:00"
```

### Filter Extensibility

Filters are **event-type agnostic** and work with any event type:
- Current event types: `click`, `console_log`, `js_error`, `dom_attribute_modified`, `dom_set_child_nodes`, `dom_character_data_modified`, `document_updated`
- When new event types are added (e.g., `window_resize`, `network_request`), they're **immediately filterable** with no code changes
- Just use the event type name in the `event_types` array

### Typical Workflow

1. **Get overview** - Call without filters to see event breakdown
2. **Filter what you need** - Request specific event types or ranges
3. **Paginate if needed** - Use `limit` and `offset` for large result sets
4. **Generate/analyze** - Use filtered data for test generation or analysis

**Example:**
```
# Step 1: What's in the recording?
get_recording with session_id "abc-123"
→ Shows: 514 events (click: 45, console_log: 320, js_error: 12, ...)

# Step 2: I only care about user interactions
get_recording with session_id "abc-123" and event_types ["click"]
→ Returns: 45 click events

# Step 3: Generate test from clicks
[Claude uses 45 click events to generate Selenium test]
```

## Output Format

Recordings are saved as JSON:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com",
  "start_time": "2025-01-15T14:30:15.123456",
  "end_time": "2025-01-15T14:35:22.654321",
  "events": [
    {
      "type": "dom_attribute_modified",
      "timestamp": "2025-01-15T14:30:18.123456",
      "data": {
        "node_id": 42,
        "name": "value",
        "value": "***MASKED***",
        "_masked": true
      }
    },
    {
      "type": "console_log",
      "timestamp": "2025-01-15T14:30:20.123456",
      "data": {
        "level": "info",
        "args": ["User logged in successfully"]
      }
    },
    {
      "type": "js_error",
      "timestamp": "2025-01-15T14:30:25.123456",
      "data": {
        "message": "TypeError: Cannot read property 'id' of undefined",
        "stack": "..."
      }
    }
  ],
  "metadata": {
    "saved_at": "2025-01-15T14:35:22.987654",
    "event_count": 247
  }
}
```

## Sensitive Field Masking

By default, these fields are masked:
- `input[type="password"]`
- `input[name*="password"]`
- `input[name*="passwd"]`
- `input[id*="password"]`
- `input[name*="secret"]`
- `input[name*="token"]`

Add custom sensitive selectors:

```
start_recording with sensitive_selectors ["input[name='credit-card']", "input[id='ssn']"]
```

## Event Types

### Click Events
- `click`: User click interactions with comprehensive element details:
  - **Identification**: Tag name, ID, classes, all attributes
  - **Content**: Text content (first 200 chars), innerHTML (first 500 chars)
  - **Selectors**: XPath and CSS selector for precise element location
  - **Links/Media**: href (for links), src (for images)
  - **Position**: Click coordinates (x, y) and page position
  - **Context**: Viewport size and current URL

**Example click event:**
```json
{
  "type": "click",
  "timestamp": "2025-01-15T14:30:22.123456",
  "data": {
    "tagName": "A",
    "id": "login-button",
    "className": "btn btn-primary",
    "classList": ["btn", "btn-primary"],
    "attributes": {"href": "/login", "target": "_self"},
    "textContent": "Login",
    "innerHTML": "Login",
    "xpath": "//*[@id=\"login-button\"]",
    "cssSelector": "#login-button",
    "href": "https://example.com/login",
    "coordinates": {"x": 150, "y": 200, "pageX": 150, "pageY": 200},
    "viewport": {"width": 1920, "height": 1080},
    "url": "https://example.com"
  }
}
```

### DOM Events
- `document_updated`: Document structure changed
- `dom_set_child_nodes`: Child nodes added/modified
- `dom_attribute_modified`: Element attribute changed
- `dom_character_data_modified`: Text content changed

### Runtime Events
- `console_log`: Console output (log, info, warn, error)
- `js_error`: JavaScript exception thrown

## Troubleshooting

### Chrome doesn't open
- Check `CHROME_PATH` is correct
- Ensure Chrome is installed
- Try absolute path to Chrome executable

### No events recorded
- Check Chrome DevTools console for errors
- Ensure page allows remote debugging
- Some CSP policies may block CDP

### MCP server fails to connect from another folder
- Use absolute paths in `mcp_settings.json` for the `command` field
- Example: `"/Users/username/selenium-recorder-mcp/.venv/bin/python"`
- The `cwd` setting only affects where the process runs, not where the command is found

### Sensitive data not masked
- Add custom selectors via `sensitive_selectors`
- Check field naming patterns match defaults
- Review event_processor.py patterns

## Use Cases

1. **Test Generation**: Record manual workflow, generate Selenium tests
2. **Bug Reproduction**: Capture exact DOM state during error
3. **Performance Analysis**: Track DOM mutations and console logs
4. **Debugging**: See all browser events during interaction

## Architecture

```
┌─────────────────┐
│  Claude Code    │
│   (MCP Client)  │
└────────┬────────┘
         │
         │ MCP Protocol
         │
┌────────▼────────┐
│  server.py      │  MCP Tools
│  (MCP Server)   │  - start_recording
└────────┬────────┘  - stop_recording
         │           - get_recording
         │           - analyze_recording
         │
┌────────▼──────────────────────────┐
│  cdp_recorder.py                  │
│  - Launch Chrome w/ debug port    │
│  - Connect via CDP                │
│  - Inject click tracking JS       │
│  - Listen to DOM/Runtime events   │
└────────┬──────────────────────────┘
         │
┌────────▼──────────────────────────┐
│  event_processor.py               │
│  - Mask sensitive fields          │
│  - Enrich events                  │
│  - Analyze patterns               │
└────────┬──────────────────────────┘
         │
┌────────▼──────────────────────────┐
│  storage.py                       │
│  - Save as JSON                   │
│  - Load recordings                │
│  - List/delete                    │
└───────────────────────────────────┘
```

## Development

Run server directly:

```bash
python -m src.server
```

## License

MIT

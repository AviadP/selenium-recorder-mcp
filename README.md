# Selenium Test Recorder MCP Server

MCP server for recording comprehensive browser interactions using Chrome DevTools Protocol (CDP). Records DOM mutations, console logs, and JavaScript errors while you manually interact with a website.

## Features

- **Click Tracking**: Captures every click with full element details (XPath, CSS selector, attributes, text content, coordinates)
- **Comprehensive Recording**: Captures DOM mutations, console logs, and JS errors
- **Manual Interaction**: Record while you manually navigate and interact with browser
- **Sensitive Field Masking**: Automatically masks password fields and other sensitive data
- **JSON Output**: Structured data for analysis and test generation
- **Claude Code Integration**: Use via MCP tools in Claude Code

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

### 1. Configure Chrome Path (if needed)

Set `CHROME_PATH` environment variable if Chrome is not in default location:

```bash
export CHROME_PATH="/path/to/chrome"
```

**Default paths:**
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Linux: `/usr/bin/google-chrome`
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`

### 2. Configure Claude Code MCP

Add to your Claude Code MCP settings (`~/.claude/mcp_settings.json`):

**Important:** Use absolute paths for the Python command to ensure it works from any directory.

```json
{
  "mcpServers": {
    "selenium-recorder": {
      "command": "/absolute/path/to/selenium-recorder-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/selenium-recorder-mcp",
      "env": {
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

**Example (macOS/Linux):**
```json
{
  "mcpServers": {
    "selenium-recorder": {
      "command": "/Users/username/selenium-recorder-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/username/selenium-recorder-mcp"
    }
  }
}
```

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

Retrieve recording data.

**Parameters:**
- `session_id` (required): Session ID to retrieve

**Returns:** Full recording JSON

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

You: Analyze the recording

Claude: [calls analyze_recording]
Recording Analysis for 550e8400-e29b-41d4-a716-446655440000:
- Total events: 247
- Clicks: 12
- DOM mutations: 189
- Console logs: 52
- JS errors: 6
- Masked events: 3

You: Generate a Selenium test from this recording

Claude: [reads recording, generates test code]
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

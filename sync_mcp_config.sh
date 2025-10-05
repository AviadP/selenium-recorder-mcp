#!/bin/bash
# Script to sync MCP settings to all Claude Code project directories

SOURCE_CONFIG="/Users/apolak/.claude/mcp_settings.json"
BACKUP_SUFFIX=".backup.$(date +%Y%m%d_%H%M%S)"

echo "🔍 Finding all .claude directories..."
echo ""

# Find all .claude directories in home folder
claude_dirs=$(find /Users/apolak -type d -name ".claude" 2>/dev/null | grep -v "/.venv/" | grep -v "/node_modules/")

if [ -z "$claude_dirs" ]; then
    echo "❌ No .claude directories found"
    exit 1
fi

echo "Found directories:"
echo "$claude_dirs" | nl
echo ""

# Check if source config exists
if [ ! -f "$SOURCE_CONFIG" ]; then
    echo "❌ Source config not found: $SOURCE_CONFIG"
    exit 1
fi

echo "📋 Source config:"
cat "$SOURCE_CONFIG"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Process each directory
while IFS= read -r dir; do
    target_file="$dir/mcp_settings.json"

    echo "📁 Processing: $dir"

    # Skip the source directory
    if [ "$dir" = "$(dirname "$SOURCE_CONFIG")" ]; then
        echo "   ⏭️  Skipping source directory"
        echo ""
        continue
    fi

    # Check if target already exists
    if [ -f "$target_file" ]; then
        echo "   ⚠️  Config already exists, creating backup..."
        cp "$target_file" "${target_file}${BACKUP_SUFFIX}"
        echo "   💾 Backup created: ${target_file}${BACKUP_SUFFIX}"
    fi

    # Copy config
    cp "$SOURCE_CONFIG" "$target_file"

    if [ $? -eq 0 ]; then
        echo "   ✅ Config synced successfully"
    else
        echo "   ❌ Failed to sync config"
    fi

    echo ""
done <<< "$claude_dirs"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Sync complete!"
echo ""
echo "Next steps:"
echo "1. Restart Claude Code or run /mcp in each session"
echo "2. The selenium-recorder MCP server should now be available in all projects"

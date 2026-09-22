#!/usr/bin/env bash
# opus5-lean MCP Server (Bash implementation)
# Simple MCP stdio server that wraps opus5-lean CLI commands

set -euo pipefail

# Ensure Python 3.11 is available
export PATH="/root/.pyenv/versions/3.11.15/bin:$PATH"

# Check opus5-lean is installed
if ! command -v opus5-lean &>/dev/null; then
    echo '{"jsonrpc":"2.0","error":{"code":-32000,"message":"opus5-lean CLI not installed. Run: pip install -e /projects/sandbox/Claude-Opus5"},"id":1}'
    exit 1
fi

# Simple MCP stdio implementation
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Extract method name (e.g., "mcp/opus5-lean/count")
    method=$(echo "$line" | grep -o '"method":"[^"]*"' | sed 's/"method":"//;s/"$//' || echo "")
    
    case "$method" in
        mcp/opus5-lean/count)
            # Extract prompt from params (base64 encoded in JSON)
            prompt=$(echo "$line" | sed 's/.*"prompt":"//;s/".*//' | base64 -d 2>/dev/null || echo "")
            
            # Write to temp file and count
            tmp=$(mktemp)
            echo -n "$prompt" > "$tmp"
            output=$(opus5-lean count "$tmp" 2>&1 || echo "ERROR")
            rm -f "$tmp"
            
            # Escape for JSON
            escaped_output=$(echo "$output" | tr '\n' ' ' | sed 's/"/\\"/g')
            echo "{\"jsonrpc\":\"2.0\",\"result\":{\"output\":\"$escaped_output\"},\"id\":1}"
            ;;
            
        mcp/opus5-lean/slim)
            prompt=$(echo "$line" | sed 's/.*"prompt":"//;s/".*//' | base64 -d 2>/dev/null || echo "")
            
            tmp=$(mktemp)
            echo -n "$prompt" > "$tmp"
            output=$(opus5-lean slim "$tmp" --stdout 2>&1 || echo "ERROR")
            rm -f "$tmp"
            
            escaped_output=$(echo "$output" | tr '\n' ' ' | sed 's/"/\\"/g')
            echo "{\"jsonrpc\":\"2.0\",\"result\":{\"output\":\"$escaped_output\"},\"id\":1}"
            ;;
            
        mcp/opus5-lean/cost)
            echo '{"jsonrpc":"2.0","result":{"note":"Use: opus5-lean cost --input N --output N --model claude-opus-5 --requests N"},"id":1}'
            ;;
            
        mcp/opus5-lean/cache)
            echo '{"jsonrpc":"2.0","result":{"note":"Cache planning requires segment JSON file, use: opus5-lean cache segments.json --rpd 1000"},"id":1}'
            ;;
            
        mcp/opus5-lean/sweep)
            echo '{"jsonrpc":"2.0","result":{"note":"Sweep requires API key with credit. Use: opus5-lean sweep task.md --require \"pattern\" --trials 3"},"id":1}'
            ;;
            
        *)
            echo "{\"jsonrpc\":\"2.0\",\"error\":{\"code\":-32601,\"message\":\"Unknown method: $method\"},\"id\":1}"
            ;;
    esac
done

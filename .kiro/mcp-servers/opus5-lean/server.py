#!/usr/bin/env python3
"""
opus5-lean MCP Server
Token-efficiency server for Claude Opus 5.
Measures prompt costs, strips wasted tokens, plans cache strategies.
"""

import argparse
import json
import sys
import subprocess
from typing import Any, Dict, Optional

def run_opus5(args: list[str]) -> tuple[int, str]:
    """Run opus5-lean CLI and capture output."""
    try:
        result = subprocess.run(
            ["opus5-lean"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return 1, "Error: opus5-lean CLI not installed. Run: pip install -e /projects/sandbox/Claude-Opus5"

def tool_opus5_count(params: Dict[str, Any]) -> Dict[str, Any]:
    """opus5_count: Count tokens and estimate cost."""
    prompt = params.get("prompt", "")
    model = params.get("model", "claude-opus-5")
    
    # Write prompt to temp file for counting
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        code, output = run_opus5(["count", temp_path, "--model", model, "--json"])
        if code == 0:
            return {"result": output.strip()}
        return {"error": output}
    finally:
        import os
        os.unlink(temp_path)

def tool_opus5_slim(params: Dict[str, Any]) -> Dict[str, Any]:
    """opus5_slim: Strip wasted tokens from prompt."""
    prompt = params.get("prompt", "")
    aggressive = params.get("aggressive", False)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        args = ["slim", temp_path]
        if aggressive:
            args.append("--aggressive")
        args.extend(["--json", "--output", "stdout"])
        
        code, output = run_opus5(args)
        if code == 0:
            return {"result": output.strip()}
        return {"error": output}
    finally:
        import os
        os.unlink(temp_path)

def tool_opus5_cache_plan(params: Dict[str, Any]) -> Dict[str, Any]:
    """opus5_cache_plan: Plan cache strategy."""
    segments = params.get("segments", [])
    rpd = params.get("requests_per_day", 1000)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(segments, f)
        temp_path = f.name
    
    try:
        code, output = run_opus5(["cache", temp_path, "--rpd", str(rpd), "--json"])
        if code == 0:
            return {"result": output.strip()}
        return {"error": output}
    finally:
        import os
        os.unlink(temp_path)

def tool_opus5_cost_estimate(params: Dict[str, Any]) -> Dict[str, Any]:
    """opus5_cost_estimate: Calculate cost estimate."""
    input_tokens = params.get("input_tokens", 0)
    output_tokens = params.get("output_tokens", 0)
    requests = params.get("requests", 1)
    model = params.get("model", "claude-opus-5")
    use_cache = params.get("use_cache", False)
    
    cache_flag = "--use-cache" if use_cache else ""
    code, output = run_opus5([
        "cost", 
        "--input", str(input_tokens),
        "--output", str(output_tokens),
        "--requests", str(requests),
        "--model", model,
        cache_flag,
        "--json"
    ])
    
    if code == 0:
        return {"result": output.strip()}
    return {"error": output}

def tool_opus5_sweep(params: Dict[str, Any]) -> Dict[str, Any]:
    """opus5_sweep: Find cheapest effort level."""
    prompt = params.get("prompt", "")
    require = params.get("require", "")
    trials = params.get("trials", 3)
    efforts = ",".join(params.get("efforts", ["low", "medium", "high"]))
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        code, output = run_opus5([
            "sweep", temp_path,
            "--require", require,
            "--trials", str(trials),
            "--efforts", efforts,
            "--json"
        ])
        if code == 0:
            return {"result": output.strip()}
        return {"error": output}
    finally:
        import os
        os.unlink(temp_path)

# Tool dispatch table
TOOLS = {
    "opus5_count": tool_opus5_count,
    "opus5_slim": tool_opus5_slim,
    "opus5_cache_plan": tool_opus5_cache_plan,
    "opus5_cost_estimate": tool_opus5_cost_estimate,
    "opus5_sweep": tool_opus5_sweep,
}

def main():
    parser = argparse.ArgumentParser(description="opus5-lean MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Use stdio transport")
    args = parser.parse_args()
    
    if args.stdio:
        # Simple stdio implementation
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                tool_name = msg.get("method", "").split("/")[-1]
                params = msg.get("params", {})
                
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](params)
                    response = {
                        "id": msg.get("id"),
                        "result": result
                    }
                else:
                    response = {
                        "id": msg.get("id"),
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
                print(json.dumps(response))
            except Exception as e:
                print(json.dumps({"error": {"code": -32603, "message": str(e)}}))
    else:
        print("SSE transport not implemented in this minimal server")
        sys.exit(1)

if __name__ == "__main__":
    main()

# mcp-image-viewer

Claude Code plugin that automatically displays images returned by MCP tools.

## Problem

When MCP tools return images (login QR codes, charts, screenshots, etc.), Claude Code CLI shows an `[Image]` placeholder instead of the actual image. This makes workflows like MCP-based login impossible without workarounds.

## Solution

A zero-config PostToolUse hook that:
1. Intercepts all MCP tool responses
2. Detects base64-encoded images (PNG/JPEG) in the response
3. Saves to a temp file and opens with the system image viewer

Works with **any** MCP server — no configuration needed.

## Install

### From marketplace

```shell
/plugin install mcp-image-viewer@claude-plugins-official
```

### Local testing

```bash
claude --plugin-dir /path/to/mcp-image-viewer
```

## Supported Image Sources

| Source | Format | Example |
|--------|--------|---------|
| MCP content array | `{"type":"image","source":{"data":"..."}}` | Login QR codes |
| JSON fields | `qrcode_base64`, `image_base64`, etc. | API responses with embedded images |
| Data URLs | `data:image/png;base64,...` | Inline image data |
| Raw base64 in text | Long base64 string with PNG/JPEG header | Fallback detection |

## How It Works

```
MCP tool executes (e.g., get_login_qrcode)
    ↓
PostToolUse hook fires (matcher: mcp__*)
    ↓
Hook scans tool_response for base64 image data
    ↓
Image found → save to /tmp → open with system viewer
    ↓
No image → exit silently (no performance impact)
```

## Platform Support

| OS | Viewer | Command |
|----|--------|---------|
| macOS | Preview | `open` |
| Linux | Default viewer | `xdg-open` |

## Use Cases

- **MCP login QR codes** — Xiaohongshu, WeChat, Slack, etc.
- **MCP-generated charts** — Data visualization tools
- **MCP screenshots** — Browser automation, monitoring tools
- **Any MCP image** — Automatically detected and displayed

## Requirements

- Claude Code 1.0.33+
- Python 3.10+ (no extra packages)

## Testing

```bash
# Test with sample data
echo '{"tool_name":"mcp__test__qr","tool_input":{},"tool_response":[{"type":"image","source":{"data":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}}]}' | python3 hooks/display_qr.py
# Should open a 1x1 pixel PNG in your system viewer
```

## License

MIT

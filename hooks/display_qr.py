#!/usr/bin/env python3
"""PostToolUse hook: detect base64 image in MCP tool response and open in system viewer.

Automatically intercepts all MCP tool responses, extracts base64-encoded images
(QR codes, charts, screenshots, etc.), and opens them with the system image viewer.

Supported image sources:
  - MCP content array: [{"type":"image","source":{"data":"base64..."}}]
  - JSON fields: qrcode_base64, image_base64, etc.
  - Data URLs: data:image/png;base64,...
  - Raw base64 strings in text
"""

import base64
import json
import os
import re
import sys
import tempfile


def open_image(image_bytes, filename="image.png"):
    """Save image to temp file and open with system viewer."""
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)

    if sys.platform == "darwin":
        os.system(f'open "{tmp_path}"')
    elif sys.platform.startswith("linux"):
        os.system(f'xdg-open "{tmp_path}" 2>/dev/null &')


def extract_image(tool_response):
    """Extract base64 image data from MCP tool response."""
    data = tool_response

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return _find_in_text(data)

    if isinstance(data, list):
        return _find_in_list(data)

    if isinstance(data, dict):
        return _find_in_dict(data)

    return None


def _find_in_list(items):
    """Search MCP content array for image data."""
    for item in items:
        if not isinstance(item, dict):
            continue

        # MCP image content: {"type":"image","source":{"data":"base64..."}}
        if item.get("type") == "image":
            source = item.get("source", {})
            b64 = source.get("data", "") if isinstance(source, dict) else ""
            if b64:
                result = _decode(b64)
                if result:
                    return result

        # MCP text content might contain embedded base64
        if item.get("type") == "text":
            text = item.get("text", "")
            result = _find_in_text(text)
            if result:
                return result

        # Generic dict search
        result = _find_in_dict(item)
        if result:
            return result

    return None


IMAGE_FIELDS = (
    "qrcode_base64", "qrcode_data_url", "image_base64",
    "base64", "qr_base64", "qr_image", "image_data",
    "screenshot_base64", "chart_base64",
)


def _find_in_dict(data):
    """Recursively search dict for base64 image data."""
    if not isinstance(data, dict):
        return None

    for key in IMAGE_FIELDS:
        value = data.get(key)
        if isinstance(value, str) and len(value) > 50:
            result = _decode(value)
            if result:
                return result

    for value in data.values():
        if isinstance(value, dict):
            result = _find_in_dict(value)
            if result:
                return result
        elif isinstance(value, list):
            result = _find_in_list(value)
            if result:
                return result

    return None


def _decode(value):
    """Decode a base64 image value, handling data URLs."""
    if not value or len(value) < 50:
        return None

    if value.startswith("data:image"):
        parts = value.split(",", 1)
        if len(parts) == 2:
            value = parts[1]

    try:
        decoded = base64.b64decode(value)
        if decoded[:4] == b"\x89PNG" or decoded[:2] == b"\xff\xd8":
            return decoded
    except Exception:
        pass

    return None


def _find_in_text(text):
    """Try to find base64-encoded image in raw text."""
    pattern = r'[A-Za-z0-9+/]{100,}={0,2}'
    for match in re.finditer(pattern, text):
        result = _decode(match.group())
        if result:
            return result
    return None


def main():
    """Hook entry point. Reads PostToolUse JSON from stdin."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return

    if not raw.strip():
        return

    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = hook_data.get("tool_name", "")
    tool_response = hook_data.get("tool_response", "")

    if not tool_name.startswith("mcp__"):
        return

    image_bytes = extract_image(tool_response)
    if not image_bytes:
        return

    filename = f"mcp_image_{tool_name}.png"
    open_image(image_bytes, filename)


if __name__ == "__main__":
    main()

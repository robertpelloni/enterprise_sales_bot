"""
Marketing Bot - Chrome DevTools Protocol Utilities

Browser automation helpers for CDP-based platforms (Reddit, Twitter, LinkedIn).
"""

import json
import time
import urllib.request
from typing import Optional

import websocket

from . import config


def get_browser_ws() -> Optional[str]:
    """Get browser-level WebSocket URL for creating tabs."""
    try:
        resp = urllib.request.urlopen(
            f"http://{config.CDP_HOST}:{config.CDP_PORT}/json/version",
            timeout=5,
        )
        info = json.loads(resp.read())
        return info.get("webSocketDebuggerUrl")
    except Exception:
        return None


def create_tab(browser_ws: str, url: str = "about:blank") -> Optional[str]:
    """Create a new browser tab and return its WebSocket URL."""
    try:
        ws = websocket.create_connection(browser_ws, timeout=15)
        ws.send(
            json.dumps(
                {"id": 1, "method": "Target.createTarget", "params": {"url": url}}
            )
        )
        time.sleep(2)

        target_id = None
        for _ in range(5):
            try:
                ws.settimeout(3)
                d = json.loads(ws.recv())
                if d.get("id") == 1:
                    target_id = d.get("result", {}).get("targetId")
                    break
            except Exception:
                continue

        ws.close()

        if target_id:
            resp = urllib.request.urlopen(
                f"http://{config.CDP_HOST}:{config.CDP_PORT}/json",
                timeout=5,
            )
            tabs = json.loads(resp.read())
            for tab in tabs:
                if tab.get("id") == target_id:
                    return tab.get("webSocketDebuggerUrl")
    except Exception as e:
        print(f"[CDP] Error creating tab: {e}")

    return None


def send_and_recv(
    ws: websocket.WebSocket,
    msg_id: int,
    method: str,
    params: Optional[dict] = None,
    timeout: int = 8,
) -> Optional[str]:
    """Send CDP command and get response value."""
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)

    result = None
    for _ in range(10):
        try:
            ws.settimeout(timeout)
            data = json.loads(ws.recv())
            if data.get("id") == msg_id:
                result = data.get("result", {}).get("result", {}).get("value")
                break
        except websocket.WebSocketTimeoutException:
            break
        except Exception:
            break
    return result


def navigate(ws: websocket.WebSocket, url: str, wait: int = 6) -> bool:
    """Navigate to URL and wait for load."""
    try:
        ws.send(
            json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}})
        )
        time.sleep(wait)
        return True
    except Exception as e:
        print(f"[CDP] Navigation error: {e}")
        return False


def wait_for_element(
    ws: websocket.WebSocket,
    selector: str,
    timeout: int = 10,
    msg_id: int = 100,
) -> bool:
    """Wait for an element to appear on the page."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = send_and_recv(
            ws,
            msg_id,
            "Runtime.evaluate",
            {
                "expression": f"!!document.querySelector('{selector}')",
                "returnByValue": True,
            },
        )
        if result:
            return True
        time.sleep(0.5)
    return False


def type_text(ws: websocket.WebSocket, text: str, msg_id: int = 200) -> bool:
    """Type text character by character using Input.insertText."""
    try:
        ws.send(
            json.dumps(
                {"id": msg_id, "method": "Input.insertText", "params": {"text": text}}
            )
        )
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"[CDP] Type error: {e}")
        return False


def click_element(
    ws: websocket.WebSocket,
    selector: str,
    msg_id: int = 300,
) -> bool:
    """Click an element by selector."""
    result = send_and_recv(
        ws,
        msg_id,
        "Runtime.evaluate",
        {
            "expression": f"""
            (function() {{
                var el = document.querySelector('{selector}');
                if (el) {{
                    el.click();
                    return 'clicked';
                }}
                return 'not found';
            }})()
            """,
            "returnByValue": True,
        },
    )
    return result == "clicked"


def fill_input(
    ws: websocket.WebSocket,
    selector: str,
    value: str,
    msg_id: int = 400,
) -> bool:
    """Fill an input field with a value."""
    result = send_and_recv(
        ws,
        msg_id,
        "Runtime.evaluate",
        {
            "expression": f"""
            (function() {{
                var el = document.querySelector('{selector}');
                if (el) {{
                    el.value = {json.dumps(value)};
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return 'filled';
                }}
                return 'not found';
            }})()
            """,
            "returnByValue": True,
        },
    )
    return result == "filled"


def get_page_text(
    ws: websocket.WebSocket,
    max_length: int = 1000,
    msg_id: int = 500,
) -> str:
    """Get visible text content from the page."""
    result = send_and_recv(
        ws,
        msg_id,
        "Runtime.evaluate",
        {
            "expression": f"document.body.innerText.substring(0, {max_length})",
            "returnByValue": True,
        },
    )
    return result or ""

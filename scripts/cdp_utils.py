#!/usr/bin/env python3
"""
CDP Utilities - Shared Chrome DevTools Protocol utilities
Extracted from autonomous_marketing.py
"""
import websocket
import json
import time


class CDPSession:
    """Manages Chrome DevTools Protocol sessions"""

    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    def connect(self):
        """Connect to CDP session"""
        try:
            self.ws = websocket.create_connection(self.ws_url, timeout=15)
            return True
        except Exception as e:
            print(f"CDP connection error: {e}")
            return False

    def send_command(self, method, params=None, timeout=5):
        """Send CDP command and wait for response"""
        if not self.ws:
            if not self.connect():
                return None

        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}

        try:
            self.ws.send(json.dumps(msg))

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    self.ws.settimeout(1)
                    data = json.loads(self.ws.recv())
                    if data.get("id") == self.msg_id:
                        return data.get("result", {})
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    print(f"CDP recv error: {e}")
                    break

            return None
        except Exception as e:
            print(f"CDP send error: {e}")
            return None

    def navigate(self, url):
        """Navigate to URL"""
        return self.send_command("Page.navigate", {"url": url})

    def evaluate(self, expression, timeout=5):
        """Evaluate JavaScript expression"""
        return self.send_command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            timeout,
        )

    def click(self, selector):
        """Click element by selector"""
        return self.evaluate(f"""
            (function() {{
                var el = document.querySelector('{selector}');
                if (el) {{
                    el.click();
                    return 'clicked';
                }}
                return 'not found';
            }})()
        """)

    def type_text(self, text):
        """Type text using Input.insertText"""
        return self.send_command("Input.insertText", {"text": text})

    def press_key(self, key):
        """Press a key"""
        return self.send_command(
            "Input.dispatchKeyEvent",
            {
                "type": "keyDown",
                "key": key,
                "code": key,
                "text": key if len(key) == 1 else "",
            },
        )

    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass


def get_browser_ws():
    """Get browser WebSocket URL from CDP"""
    import urllib.request
    try:
        resp = urllib.request.urlopen("http://localhost:9222/json/version", timeout=5)
        return json.loads(resp.read()).get("webSocketDebuggerUrl")
    except Exception:
        return None


def create_tab(browser_ws, url="about:blank"):
    """Create a new tab and return its WebSocket URL"""
    import urllib.request
    
    ws = websocket.create_connection(browser_ws, timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}}))
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
        resp = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
        tabs = json.loads(resp.read())
        for t in tabs:
            if t.get("id") == target_id:
                return t.get("webSocketDebuggerUrl")
    
    return None


def send_and_recv(ws, msg_id, method, params=None, timeout=8):
    """Send CDP command and receive response (standalone function version)"""
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    time.sleep(1)
    result = None
    for _ in range(15):
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


def navigate(ws, url, wait=7):
    """Navigate to URL (standalone function version)"""
    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
    time.sleep(wait)
    for _ in range(10):
        try:
            ws.settimeout(0.5)
            ws.recv()
        except Exception:
            break


def log(msg):
    """Log with timestamp"""
    import sys
    ts = time.strftime("%H:%M:%S")
    sys.stdout.buffer.write(f"[{ts}] {msg}\n".encode("utf-8"))
    sys.stdout.flush()

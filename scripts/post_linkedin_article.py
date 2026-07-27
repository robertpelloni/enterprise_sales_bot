import websocket
import json
import time
import sys


def post_article(article_file, article_num, total):
    ws_url = "ws://localhost:9222/devtools/page/C915DA41DC13BB4937A4A972B5A19BD3"

    with open(article_file, "r", encoding="utf-8") as f:
        article = json.load(f)

    title = article["title"]
    content = article["content"]
    lines = content.split("\n")
    if lines[0].strip() == title:
        lines = lines[1:]
    content = "\n".join(lines).strip()

    ws = websocket.create_connection(ws_url, timeout=15)

    # Navigate to new article
    ws.send(
        json.dumps(
            {
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": "https://www.linkedin.com/article/new/"},
            }
        )
    )
    time.sleep(6)

    # Focus title
    ws.send(
        json.dumps(
            {
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "(function(){var e=document.getElementById('article-editor-headline__textarea');if(e){e.focus();e.value='';return 'ok';}return 'no';})()",
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(1)
    for _ in range(5):
        try:
            ws.settimeout(2)
            d = json.loads(ws.recv())
            if d.get("id") == 2:
                break
        except:
            continue

    # Type title
    ws.send(
        json.dumps({"id": 3, "method": "Input.insertText", "params": {"text": title}})
    )
    time.sleep(1)
    for _ in range(5):
        try:
            ws.settimeout(2)
            d = json.loads(ws.recv())
            if d.get("id") == 3:
                break
        except:
            continue

    # Focus body
    ws.send(
        json.dumps(
            {
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "(function(){var e=document.querySelector('div[contenteditable=true]');if(e){e.focus();return 'ok';}return 'no';})()",
                    "returnByValue": True,
                },
            }
        )
    )
    time.sleep(1)
    for _ in range(5):
        try:
            ws.settimeout(2)
            d = json.loads(ws.recv())
            if d.get("id") == 4:
                break
        except:
            continue

    # Type body (limit to 3000 chars for LinkedIn)
    body_text = content[:3000]
    ws.send(
        json.dumps(
            {"id": 5, "method": "Input.insertText", "params": {"text": body_text}}
        )
    )
    time.sleep(2)
    for _ in range(5):
        try:
            ws.settimeout(2)
            d = json.loads(ws.recv())
            if d.get("id") == 5:
                break
        except:
            continue

    ws.close()

    print(f"Article {article_num}/{total} filled: {title}")
    print(f"Content: {len(body_text)} chars")


if __name__ == "__main__":
    article_file = sys.argv[1]
    article_num = int(sys.argv[2])
    total = int(sys.argv[3])
    post_article(article_file, article_num, total)

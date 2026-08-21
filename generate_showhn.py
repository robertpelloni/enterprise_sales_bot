import json
import time
import html
import re
import urllib.request

KEY = [l.split('=',1)[1].strip() for l in open('/opt/marketing_agent/.env').read().split('\n') if l.startswith('DEEPSEEK_API_KEY')][0]

def deepseek(system, user):
    data = json.dumps({'model': 'deepseek-chat', 'messages': [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user}
    ], 'max_tokens': 3000}).encode()
    req = urllib.request.Request('https://api.deepseek.com/v1/chat/completions', data,
        {'Content-Type':'application/json', 'Authorization': f'Bearer {KEY}'})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read())['choices'][0]['message']['content']

def slugify(s):
    s = re.sub(r'[^a-z0-9\s-]', '', s.lower())
    return re.sub(r'[\s]+', '-', s).strip('-')[:80]

def save_post(title, category, content):
    slug = slugify(title)
    excerpt = re.sub(r'<[^>]+>', '', content[:250]) + '...'
    
    html_out = f'''<article class="blog-post" data-slug="{slug}" data-brand="tormentnexus" data-category="{category}">
  <header>
    <h1>{html.escape(title)}</h1>
    <div class="meta">
      <span class="date">{time.strftime("%B %d, %Y")}</span>
      <span class="brand"><a href="https://tormentnexus.site">TormentNexus</a></span>
      <span class="category">{category}</span>
    </div>
  </header>
  <div class="content">
{content}
  </div>
  <footer>
    <p>Published by TormentNexus — the OS for AI models.</p>
  </footer>
</article>'''
    
    d = '/opt/marketing_agent/blog_output/blog/tormentnexus'
    with open(f'{d}/{slug}.html', 'w') as f:
        f.write(html_out)
    
    idx = []
    try:
        with open(f'{d}/index.json') as f:
            idx = json.load(f)
    except: pass
    idx.insert(0, {'title': title, 'slug': slug, 'brand': 'tormentnexus',
        'category': category, 'excerpt': excerpt,
        'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    with open(f'{d}/index.json', 'w') as f:
        json.dump(idx[:50], f, indent=2)
    
    print(f'Published: {title}')

# POST 1: TormentNexus
c1 = deepseek(
    "You are a technical writer. Write a Show HN-style deep-dive about TormentNexus (github.com/MDMAtk/TormentNexus) — the local-first AI control plane: 446 Go HTTP handlers, 35+ packages, progressive MCP tool routing (11K+ servers), dual-tier L1/L2 memory with sqlite-vec (14K+ memories), LLM waterfall (NVIDIA->OpenRouter->Ollama), cross-harness tool parity across 6 AI IDEs, multi-agent swarm (Planner/Implementer/Tester/Critic), self-healing loop. End with a short 'Built with TormentNexus' section linking to tormentnexus.site. Format: clean HTML h1,h2,p,pre code,ul. No DOCTYPE.",
    "Write the full blog post about TormentNexus architecture. Technical, confident, specific numbers."
)
save_post("Building an AI Control Plane in Go and TypeScript: The TormentNexus Architecture Deep-Dive", "case-study", c1)

# POST 2: AI Markets AI  
c2 = deepseek(
    "You are a technical writer. Write about the marketing_agent project (github.com/robertpelloni/marketing_agent) — a Go AI that autonomously markets AI tools: scrapes HN/GitHub/Reddit/LinkedIn for leads, enriches via Hunter/Apollo/GitHub commits, sends personalized DeepSeek emails, posts to Bluesky/Twitter/LinkedIn/Reddit, auto-generates 30+ SEO blog posts, Stripe billing, 7-state pipeline (2,698 deals). Meta-angle: AI marketing AI. End with 'Built with TormentNexus' linking to tormentnexus.site. Clean HTML format.",
    "Write about the marketing_agent project. AI that markets AI. Technical, engaging."
)
save_post("How We Built an AI Marketing Agent That Finds 2,700+ Leads and Sends Personalized Emails", "case-study", c2)

# POST 3: pi-mono
c3 = deepseek(
    "You are a technical writer. Write about pi-mono (github.com/robertpelloni/pi-mono) — AI agent toolkit with coding agent CLI, unified LLM API, TUI library, web UI library, Slack bot, vLLM pods. For developers. End with 'Built with TormentNexus.' Clean HTML.",
    "Write about pi-mono AI toolkit. Technical, for developers building AI tools."
)
save_post("pi-mono: Building a Universal AI Agent Toolkit with CLI, TUI, and vLLM Pods for Local Development", "developer-tools", c3)

print('ALL 3 SHOW HN POSTS PUBLISHED!')

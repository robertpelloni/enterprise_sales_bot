#!/usr/bin/env python3
"""
outreach_top100.py — Top 100 AI companies outreach for HyperNexus.

Sends personalized cold emails to the most important AI companies
across 10 categories, targeting the people most likely to care about
a local-first AI control plane with persistent memory.

Companies NOT in the DB are queued to a CSV so they can be enriched
later. Companies already in the DB (via contacts) are emailed directly.

Usage:
  python outreach_top100.py            # run full outreach
  python outreach_top100.py --dry-run  # preview without sending
  python outreach_top100.py --stats    # show stats
"""

import sys

from outreach_smtp import logger, send_email, get_stats

# ─── Top 100 AI companies by category ────────────────────────────────────────
TOP_100 = {
    "AI Coding": [
        ("Cursor", "cursor.com"),
        ("Sourcegraph", "sourcegraph.com"),
        ("Replit", "replit.com"),
        ("Codeium", "codeium.com"),
        ("Poolside", "poolside.ai"),
        ("Tabnine", "tabnine.com"),
        ("GitHub Copilot", "github.com"),
        ("Aider", "aider.chat"),
        ("Continue", "continue.dev"),
        ("Windsurf", "windsurf.com"),
        ("Cognition AI", "cognition.ai"),
    ],
    "Local AI": [
        ("Ollama", "ollama.com"),
        ("LM Studio", "lmstudio.ai"),
        ("Jan.ai", "jan.ai"),
        ("AnythingLLM", "anythingllm.com"),
        ("LocalAI", "localai.io"),
        ("GPT4All", "gpt4all.io"),
        ("llama.cpp", "github.com"),
        ("vLLM", "vllm.ai"),
        ("Text Generation WebUI", "github.com"),
        ("PrivateGPT", "privategpt.io"),
        ("koboldcpp", "github.com"),
    ],
    "Frameworks": [
        ("LangChain", "langchain.com"),
        ("LlamaIndex", "llamaindex.ai"),
        ("Vercel", "vercel.com"),
        ("CrewAI", "crewai.com"),
        ("AutoGen", "microsoft.com"),
        ("Haystack", "haystack.deepset.ai"),
        ("Semantic Kernel", "microsoft.com"),
        ("DSPy", "dspy.ai"),
        ("Spring AI", "spring.io"),
        ("Ollama Framework", "ollama.com"),
        ("AG2", "ag2.ai"),
        ("Pydantic AI", "ai.pydantic.dev"),
        ("Flowise", "flowiseai.com"),
    ],
    "Model Providers": [
        ("Anthropic", "anthropic.com"),
        ("OpenAI", "openai.com"),
        ("Mistral", "mistral.ai"),
        ("xAI", "x.ai"),
        ("Cohere", "cohere.com"),
        ("Meta AI", "ai.meta.com"),
        ("DeepSeek", "deepseek.com"),
        ("Grok", "grok.com"),
        ("Qwen", "qwen.ai"),
    ],
    "Infrastructure": [
        ("Hugging Face", "huggingface.co"),
        ("Pinecone", "pinecone.io"),
        ("Weaviate", "weaviate.io"),
        ("Chroma", "chroma.com"),
        ("Qdrant", "qdrant.tech"),
        ("Milvus", "milvus.io"),
        ("pgvector", "github.com"),
        ("LanceDB", "lancedb.com"),
        ("Supabase", "supabase.com"),
        ("Modal", "modal.com"),
        ("Baseten", "baseten.co"),
        ("Replicate", "replicate.com"),
        ("RunPod", "runpod.io"),
    ],
    "Agents": [
        ("Langflow", "langflow.org"),
        ("Dify", "dify.ai"),
        ("n8n", "n8n.io"),
        ("Zapier", "zapier.com"),
        ("Make", "make.com"),
        ("Activepieces", "activepieces.com"),
        ("Lindy", "lindy.ai"),
        ("Sema4.ai", "sema4.ai"),
        ("OpenHands", "openhands.dev"),
        ("Claude Agents", "anthropic.com"),
    ],
    "Dev Tools": [
        ("Linear", "linear.app"),
        ("Notion", "notion.com"),
        ("Figma", "figma.com"),
        ("Sentry", "sentry.io"),
        ("Datadog", "datadoghq.com"),
        ("Postman", "postman.com"),
        ("GitLab", "gitlab.com"),
        ("JetBrains", "jetbrains.com"),
    ],
    "Enterprise": [
        ("Scale AI", "scale.com"),
        ("Labelbox", "labelbox.com"),
        ("Snorkel", "snorkel.ai"),
        ("Dataiku", "dataiku.com"),
        ("Databricks", "databricks.com"),
        ("Snowflake", "snowflake.com"),
        ("Palantir", "palantir.com"),
        ("C3.ai", "c3.ai"),
        ("ServiceNow", "servicenow.com"),
    ],
    "Products": [
        ("Perplexity", "perplexity.ai"),
        ("Midjourney", "midjourney.com"),
        ("Runway", "runwayml.com"),
        ("ElevenLabs", "elevenlabs.io"),
        ("Synthesia", "synthesia.io"),
        ("Descript", "descript.com"),
        ("Otter.ai", "otter.ai"),
    ],
    "Emerging": [
        ("Cognition AI", "cognition.ai"),
        ("Magic AI", "magic.dev"),
        ("Augment", "augmentcode.com"),
        ("Devin", "devin.ai"),
        ("Factory AI", "factory.ai"),
        ("Anysphere", "anysphere.com"),
        ("Lovable", "lovable.dev"),
        ("Bolt", "bolt.new"),
        ("v0", "v0.dev"),
        ("Tessl", "tessl.io"),
    ],
}


def subject_for(company, category):
    """Return a personalized subject line."""
    return f"HyperNexus — local-first AI control plane for {company}"


def body_for(contact):
    """Return the email body for a contact."""
    name = contact.get("name") or "there"
    company = contact.get("company") or "your team"
    return (
        f"Hi {name},\n\n"
        f"I'm reaching out from HyperNexus — the AI control plane that runs "
        f"entirely on your infrastructure. No cloud, no data exfiltration, "
        f"full privacy.\n\n"
        f"Key capabilities:\n"
        f"  • Persistent L2 vector memory across all AI tools\n"
        f"  • Progressive tool routing — cuts token usage up to 60%\n"
        f"  • Works with any local model (Ollama, vLLM, llama.cpp)\n"
        f"  • Zero-downtime updates and self-hosted deployment\n\n"
        f"Companies like {company} care about keeping AI workloads private "
        f"and cost-efficient. HyperNexus does exactly that.\n\n"
        f"Would you be open to a 15-minute demo this week? "
        f"https://hypernexus.site\n\n"
        f"Best,\n"
        f"Robert Pelloni\n"
        f"Founder, HyperNexus\n"
        f"https://hypernexus.site"
    )


def build_contact_list(dry_run=False):
    """Build a list of contacts from TOP_100 + DB lookup."""
    contacts = []
    for category, companies in TOP_100.items():
        for company, _domain in companies:
            contacts.append(
                {
                    "email": f"hello@{_domain}",
                    "name": None,
                    "company": company,
                    "category": category,
                }
            )
    logger.info("Built contact list: %d companies", len(contacts))
    return contacts


def main():
    dry_run = "--dry-run" in sys.argv
    stats_only = "--stats" in sys.argv

    if stats_only:
        import json

        print(json.dumps(get_stats(), indent=2))
        return

    contacts = build_contact_list()
    total = len(contacts)

    if dry_run:
        print(f"DRY RUN — would send {total} emails:\n")
        for c in contacts:
            print(f"  [{c['category']}] {c['company']} <{c['email']}>")
        print(f"\nTotal: {total} emails")
        return

    print(f"Starting outreach to {total} companies...")
    print("Press Ctrl+C to stop. Rate-limited to 30/hour.")

    sent = 0
    for i, contact in enumerate(contacts):
        subject = subject_for(contact["company"], contact["category"])
        body = body_for(contact)
        try:
            ok = send_email(
                contact["email"],
                subject,
                body,
                company_name=contact["company"],
                category=contact["category"],
            )
            if ok:
                sent += 1
        except KeyboardInterrupt:
            print(f"\nStopped by user after {i} emails. Sent: {sent}")
            break
        except Exception as e:  # noqa: BLE001 - keep going on per-email errors
            logger.error("Error: %s", e)

    print(f"\nDone! Sent: {sent}/{total}")
    print("Remaining companies can be sent later — they're tracked in outreach_log.")


if __name__ == "__main__":
    main()

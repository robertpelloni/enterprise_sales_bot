-- Outreach tracking table for the HyperNexus outreach automation suite
CREATE TABLE IF NOT EXISTS outreach_log (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts (id) ON DELETE SET NULL,
    company_name TEXT,
    contact_email TEXT NOT NULL,
    category TEXT,
    subject TEXT,
    body TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    attempt INTEGER NOT NULL DEFAULT 1,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_outreach_log_email ON outreach_log (
    contact_email
);
CREATE INDEX IF NOT EXISTS idx_outreach_log_status ON outreach_log (status);

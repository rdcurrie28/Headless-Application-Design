CREATE TABLE IF NOT EXISTS customers (
    customer_id    TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    segment        TEXT,
    region         TEXT,
    account_owner  TEXT,
    salesforce_id  TEXT UNIQUE,
    contact_name   TEXT,
    contact_phone  TEXT,
    address        TEXT
);

-- Databases created before the contact fields existed.
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_name  TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS address       TEXT;

CREATE INDEX IF NOT EXISTS customers_name_idx  ON customers (lower(name));
CREATE INDEX IF NOT EXISTS customers_owner_idx ON customers (account_owner);

CREATE TABLE IF NOT EXISTS rep_actions (
    action_id    BIGSERIAL PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers (customer_id),
    action_type  TEXT NOT NULL CHECK (action_type IN ('call','email','meeting','qbr','renewal','upsell','escalation','other')),
    note         TEXT NOT NULL,
    created_by   TEXT NOT NULL,
    due_date     DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rep_actions_customer_idx ON rep_actions (customer_id, created_at DESC);

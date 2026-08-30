-- === PostgreSQL Migration: Billing + Plugin Marketplace + Usage ===
-- Fix for /plugins 500 error and missing tables

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    plan TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active',
    billing_email TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    role TEXT DEFAULT 'member',
    status TEXT DEFAULT 'active',
    last_login TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    plan TEXT NOT NULL DEFAULT 'free',
    status TEXT DEFAULT 'active',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    stripe_subscription_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage Events
CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id),
    event_type TEXT NOT NULL,
    quantity FLOAT NOT NULL,
    unit TEXT NOT NULL,
    cost FLOAT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    amount FLOAT NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending',
    stripe_invoice_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cost Tracking
CREATE TABLE IF NOT EXISTS cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    service TEXT NOT NULL,
    cost FLOAT NOT NULL,
    period DATE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SLA Monitoring
CREATE TABLE IF NOT EXISTS sla_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    metric TEXT NOT NULL,
    value FLOAT NOT NULL,
    threshold FLOAT,
    status TEXT DEFAULT 'ok',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plugin Marketplace
CREATE TABLE IF NOT EXISTS plugin_marketplace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    version TEXT DEFAULT '1.0.0',
    author TEXT,
    category TEXT DEFAULT 'utility',
    tags JSONB[] DEFAULT '{}',
    icon TEXT,
    price FLOAT DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    downloads INTEGER DEFAULT 0,
    rating FLOAT DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT false,
    source_code_url TEXT,
    documentation_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plugin Reviews
CREATE TABLE IF NOT EXISTS plugin_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID REFERENCES plugin_marketplace(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    permissions JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 100,
    last_used TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_org ON usage_events(org_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_events(created_at);
CREATE INDEX IF NOT EXISTS idx_subs_org ON subscriptions(org_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_invoices_org ON invoices(org_id);
CREATE INDEX IF NOT EXISTS idx_cost_org ON cost_tracking(org_id);
CREATE INDEX IF NOT EXISTS idx_sla_org ON sla_monitoring(org_id);
CREATE INDEX IF NOT EXISTS idx_plugin_name ON plugin_marketplace(name);
CREATE INDEX IF NOT EXISTS idx_plugin_public ON plugin_marketplace(is_public);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys_v2(user_id);

-- Insert sample data
INSERT INTO organizations (name, slug) VALUES ('Default Org', 'default') ON CONFLICT DO NOTHING;
INSERT INTO plugin_marketplace (name, display_name, description, version, author, category, is_public, is_approved)
VALUES 
    ('code-review', 'Code Review', 'AI-powered code review', '1.0.0', 'Aeryn', 'development', true, true),
    ('research', 'Research', 'Deep research assistant', '1.0.0', 'Aeryn', 'productivity', true, true),
    ('database', 'Database Manager', 'Manage databases', '1.0.0', 'Aeryn', 'development', true, true),
    ('deploy', 'Deploy', 'Deploy applications', '1.0.0', 'Aeryn', 'devops', true, true),
    ('analytics', 'Analytics', 'Track metrics', '1.0.0', 'Aeryn', 'analytics', true, true),
    ('security', 'Security Scanner', 'Vulnerability scanning', '1.0.0', 'Aeryn', 'security', true, true)
ON CONFLICT DO NOTHING;

-- === Fix: Change user_id from UUID to TEXT ===
-- Reason: Code uses string user_id (e.g., 'dashboard'), but schema had UUID type
-- This caused: "invalid input syntax for type uuid: dashboard"

-- Drop FK constraints blocking type change
ALTER TABLE plugin_reviews DROP CONSTRAINT IF EXISTS plugin_reviews_user_id_fkey;
ALTER TABLE plugin_reviews DROP CONSTRAINT IF EXISTS plugin_reviews_plugin_id_fkey;
ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_org_id_fkey;
ALTER TABLE usage_events DROP CONSTRAINT IF EXISTS usage_events_user_id_fkey;
ALTER TABLE usage_events DROP CONSTRAINT IF EXISTS usage_events_org_id_fkey;
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS invoices_org_id_fkey;
ALTER TABLE api_keys_v2 DROP CONSTRAINT IF EXISTS api_keys_v2_user_id_fkey;

-- Change user_id to TEXT in all tables
ALTER TABLE plugins ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE plugin_reviews ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE subscriptions ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE usage_events ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS tokens_input INTEGER DEFAULT 0;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS tokens_output INTEGER DEFAULT 0;
ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS endpoint TEXT;
ALTER TABLE notifications ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE notification_history ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE daily_log ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE user_notifications ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE reminders ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE quiet_hours ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE feedback ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE behavior_adjustments ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE audit_log ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE cost_tracking ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE sla_monitoring ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE task_queue ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE workflow_runs ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE workspace_members ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE workspaces ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE api_keys_v2 ALTER COLUMN user_id TYPE TEXT;

-- Rename columns that conflict with reserved words
ALTER TABLE plugins RENAME COLUMN user_id TO owner_id;
ALTER TABLE plugin_reviews RENAME COLUMN user_id TO reviewer_id;

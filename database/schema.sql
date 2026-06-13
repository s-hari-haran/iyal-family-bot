-- Family Financial Memory OS Database Schema
-- Run this script in the Supabase SQL Editor to provision tables and RLS policies.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Families Table
CREATE TABLE IF NOT EXISTS families (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Members Table
CREATE TABLE IF NOT EXISTS members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    role TEXT NOT NULL DEFAULT 'member', -- e.g., 'parent', 'child', 'grandparent'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Expenses Table (supporting three-tier confirmation status and memory importance levels)
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    category TEXT NOT NULL DEFAULT 'misc', -- e.g., 'groceries', 'utilities', 'rent', 'fuel', 'tuition'
    date DATE NOT NULL DEFAULT current_date,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'needs_review', 'pending_confirmation')),
    importance_level TEXT NOT NULL CHECK (importance_level IN ('low', 'medium', 'high')) DEFAULT 'low',
    call_id TEXT NOT NULL, -- Idempotency key from Bolna execution
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_call_expense UNIQUE (call_id, id)
);

-- 4. Debts Table
CREATE TABLE IF NOT EXISTS debts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    lender_name TEXT NOT NULL,
    borrower_name TEXT NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    due_date DATE,
    note TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'repaid')) DEFAULT 'active',
    importance_level TEXT NOT NULL CHECK (importance_level IN ('low', 'medium', 'high')) DEFAULT 'high',
    call_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_call_debt UNIQUE (call_id, id)
);

-- 5. Goals Table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    goal_name TEXT NOT NULL,
    target_amount NUMERIC(15, 2) NOT NULL,
    current_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    target_date DATE NOT NULL,
    importance_level TEXT NOT NULL CHECK (importance_level IN ('low', 'medium', 'high')) DEFAULT 'high',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    monthly_limit NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_family_category UNIQUE (family_id, category)
);

-- 7. Recurring Expenses Table
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    frequency TEXT NOT NULL CHECK (frequency IN ('weekly', 'monthly', 'yearly')) DEFAULT 'monthly',
    next_due_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Insights Table (supporting the Background Insight Engine)
CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('overspending', 'delayed_goal', 'debt_risk', 'savings_nudge', 'weekly_summary')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 9. Memory Events Table (stores key updates for pre-call context injection)
CREATE TABLE IF NOT EXISTS memory_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- e.g., 'budget_created', 'debt_repaid', 'goal_approaching'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 10. Confirmation Requests Table (for reviewable Low/Medium confidence items)
CREATE TABLE IF NOT EXISTS confirmation_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK (item_type IN ('expense', 'debt')),
    raw_value JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'rejected')) DEFAULT 'pending',
    confidence_score NUMERIC(4, 3) NOT NULL,
    uncertainty_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 11. Call Logs Table
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id TEXT UNIQUE NOT NULL, -- Bolna Execution ID
    family_id UUID REFERENCES families(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL,
    transcript JSONB DEFAULT '[]'::jsonb,
    extracted_json JSONB DEFAULT '{}'::jsonb,
    confidence NUMERIC(4, 3) DEFAULT 1.000,
    status TEXT NOT NULL CHECK (status IN ('completed', 'failed', 'needs_review')) DEFAULT 'completed',
    recording_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indices for faster querying
CREATE INDEX IF NOT EXISTS idx_members_family ON members(family_id);
CREATE INDEX IF NOT EXISTS idx_expenses_family ON expenses(family_id);
CREATE INDEX IF NOT EXISTS idx_expenses_call_id ON expenses(call_id);
CREATE INDEX IF NOT EXISTS idx_debts_family ON debts(family_id);
CREATE INDEX IF NOT EXISTS idx_goals_family ON goals(family_id);
CREATE INDEX IF NOT EXISTS idx_budgets_family ON budgets(family_id);
CREATE INDEX IF NOT EXISTS idx_recurring_family ON recurring_expenses(family_id);
CREATE INDEX IF NOT EXISTS idx_insights_family ON insights(family_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_call_id ON call_logs(call_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE families ENABLE ROW LEVEL SECURITY;
ALTER TABLE members ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE debts ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE confirmation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;

-- Create default policies for development.
-- (In a real application, policies would tie to supabase authenticated users)
CREATE POLICY select_all_families ON families FOR SELECT USING (true);
CREATE POLICY all_members ON members FOR ALL USING (true);
CREATE POLICY all_expenses ON expenses FOR ALL USING (true);
CREATE POLICY all_debts ON debts FOR ALL USING (true);
CREATE POLICY all_goals ON goals FOR ALL USING (true);
CREATE POLICY all_budgets ON budgets FOR ALL USING (true);
CREATE POLICY all_recurring ON recurring_expenses FOR ALL USING (true);
CREATE POLICY all_insights ON insights FOR ALL USING (true);
CREATE POLICY all_memory_events ON memory_events FOR ALL USING (true);
CREATE POLICY all_confirmations ON confirmation_requests FOR ALL USING (true);
CREATE POLICY all_call_logs ON call_logs FOR ALL USING (true);

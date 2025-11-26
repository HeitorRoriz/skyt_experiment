-- SKYT Database Schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/jxzhtejuswyeyerzzmto/sql

-- ============================================
-- 1. PROFILES (extends auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  company TEXT,
  role TEXT,
  use_case TEXT,
  tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'developer', 'team', 'enterprise')),
  runs_this_month INTEGER DEFAULT 0,
  runs_limit INTEGER DEFAULT 100,  -- Free tier: 100 runs/month
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, email, full_name, company, role, use_case)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'name',
    NEW.raw_user_meta_data->>'company',
    NEW.raw_user_meta_data->>'role',
    NEW.raw_user_meta_data->>'use_case'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================
-- 2. CONTRACTS (user-owned contracts)
-- ============================================
CREATE TABLE IF NOT EXISTS contracts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  contract_id TEXT NOT NULL,  -- e.g., 'fibonacci_basic'
  version TEXT DEFAULT '1.0.0',
  name TEXT NOT NULL,
  description TEXT,
  prompt TEXT NOT NULL,
  constraints JSONB DEFAULT '{}',
  oracle_requirements JSONB DEFAULT '{}',
  variable_naming JSONB DEFAULT '{}',
  restriction_preset TEXT,  -- e.g., 'nasa_power_of_10'
  is_template BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(user_id, contract_id)
);

-- Index for faster lookups
CREATE INDEX idx_contracts_user_id ON contracts(user_id);
CREATE INDEX idx_contracts_contract_id ON contracts(contract_id);

-- ============================================
-- 3. JOBS (pipeline executions)
-- ============================================
CREATE TYPE job_status AS ENUM (
  'queued',
  'loading_contract',
  'generating_outputs',
  'canonicalizing',
  'computing_metrics',
  'completed',
  'failed',
  'cancelled'
);

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
  
  -- Job configuration
  num_runs INTEGER NOT NULL DEFAULT 10,
  temperature DECIMAL(3,2) NOT NULL DEFAULT 0.3,
  model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
  
  -- Status tracking
  status job_status DEFAULT 'queued',
  phase TEXT,
  progress_percent INTEGER DEFAULT 0,
  current_run INTEGER DEFAULT 0,
  
  -- Timing
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_ms INTEGER,
  
  -- Error handling
  error_message TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- ============================================
-- 4. JOB_OUTPUTS (individual LLM outputs)
-- ============================================
CREATE TABLE IF NOT EXISTS job_outputs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  run_number INTEGER NOT NULL,
  
  -- Raw output
  raw_code TEXT NOT NULL,
  raw_hash TEXT,
  
  -- After canonicalization
  canonical_code TEXT,
  canonical_hash TEXT,
  
  -- Distance from canon
  distance_pre DECIMAL(6,4),
  distance_post DECIMAL(6,4),
  
  -- Oracle results
  oracle_passed BOOLEAN,
  oracle_details JSONB,
  
  -- Transformation applied
  transformations_applied JSONB DEFAULT '[]',
  
  -- LLM call metrics
  tokens_prompt INTEGER,
  tokens_completion INTEGER,
  latency_ms INTEGER,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX idx_job_outputs_job_id ON job_outputs(job_id);

-- ============================================
-- 5. JOB_METRICS (aggregated metrics per job)
-- ============================================
CREATE TABLE IF NOT EXISTS job_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID UNIQUE NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  
  -- Core repeatability metrics
  r_raw DECIMAL(5,4),           -- Byte-identical before processing
  r_anchor_pre DECIMAL(5,4),    -- Match canon before repair
  r_anchor_post DECIMAL(5,4),   -- Match canon after repair
  delta_rescue DECIMAL(5,4),    -- Improvement from repair
  r_behavioral DECIMAL(5,4),    -- Pass oracle tests
  r_structural DECIMAL(5,4),    -- Structural compliance
  
  -- Distributional metrics
  mean_distance_pre DECIMAL(6,4),
  mean_distance_post DECIMAL(6,4),
  std_distance_pre DECIMAL(6,4),
  std_distance_post DECIMAL(6,4),
  
  -- Transformation stats
  outputs_transformed INTEGER DEFAULT 0,
  transformation_success_rate DECIMAL(5,4),
  
  -- Token usage
  total_tokens INTEGER,
  total_cost_usd DECIMAL(10,6),
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 6. CANON_ANCHORS (canonical references)
-- ============================================
CREATE TABLE IF NOT EXISTS canon_anchors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
  
  canonical_code TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  
  -- Properties of canonical form
  properties JSONB DEFAULT '{}',
  
  -- Source info
  source_job_id UUID REFERENCES jobs(id),
  source_run_number INTEGER,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(contract_id)  -- One canon per contract
);

-- ============================================
-- 7. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE canon_anchors ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only see/edit their own profile
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

-- Contracts: Users can CRUD their own contracts
CREATE POLICY "Users can view own contracts"
  ON contracts FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own contracts"
  ON contracts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own contracts"
  ON contracts FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own contracts"
  ON contracts FOR DELETE
  USING (auth.uid() = user_id);

-- Jobs: Users can view/create their own jobs
CREATE POLICY "Users can view own jobs"
  ON jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
  ON jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs"
  ON jobs FOR UPDATE
  USING (auth.uid() = user_id);

-- Job outputs: View if user owns the job
CREATE POLICY "Users can view outputs of own jobs"
  ON job_outputs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM jobs WHERE jobs.id = job_outputs.job_id AND jobs.user_id = auth.uid()
    )
  );

-- Job metrics: View if user owns the job
CREATE POLICY "Users can view metrics of own jobs"
  ON job_metrics FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM jobs WHERE jobs.id = job_metrics.job_id AND jobs.user_id = auth.uid()
    )
  );

-- Canon anchors: View if user owns the contract
CREATE POLICY "Users can view own canon anchors"
  ON canon_anchors FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM contracts WHERE contracts.id = canon_anchors.contract_id AND contracts.user_id = auth.uid()
    )
  );

-- ============================================
-- 8. HELPER FUNCTIONS
-- ============================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_contracts_updated_at
  BEFORE UPDATE ON contracts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Increment user's monthly runs
CREATE OR REPLACE FUNCTION increment_user_runs(p_user_id UUID, p_count INTEGER DEFAULT 1)
RETURNS VOID AS $$
BEGIN
  UPDATE profiles
  SET runs_this_month = runs_this_month + p_count
  WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if user has runs remaining
CREATE OR REPLACE FUNCTION check_runs_remaining(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  v_runs_this_month INTEGER;
  v_runs_limit INTEGER;
BEGIN
  SELECT runs_this_month, runs_limit INTO v_runs_this_month, v_runs_limit
  FROM profiles WHERE id = p_user_id;
  
  RETURN v_runs_this_month < v_runs_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- DONE! Schema ready for SKYT SaaS
-- ============================================

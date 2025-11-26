import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://jxzhtejuswyeyerzzmto.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4emh0ZWp1c3d5ZXllcnp6bXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxNTExMDQsImV4cCI6MjA3OTcyNzEwNH0.pHvCRdLIbL1UoeonupQskMmfdmY68wV18ZuIeXkrejg'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

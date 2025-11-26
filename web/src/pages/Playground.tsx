import { useState, useEffect } from 'react'
import { Play, FileCode, Shield, BarChart3, Loader2, CheckCircle, XCircle, LogIn, LogOut, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { 
  getContracts, 
  getRestrictionPresets, 
  submitJob, 
  getJob,
  login,
  logout,
  getAuthToken,
} from '../services/api'
import type { Contract, RestrictionPreset, Job } from '../services/api'

function Playground() {
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(!!getAuthToken())
  const [email, setEmail] = useState('demo@skyt.works')
  const [password, setPassword] = useState('demo123')
  const [authError, setAuthError] = useState('')
  
  // Data state
  const [contracts, setContracts] = useState<Contract[]>([])
  const [restrictions, setRestrictions] = useState<RestrictionPreset[]>([])
  const [loading, setLoading] = useState(true)
  
  // Form state
  const [selectedContract, setSelectedContract] = useState('')
  const [numRuns, setNumRuns] = useState(5)
  const [temperature, setTemperature] = useState(0.3)
  const [selectedRestrictions, setSelectedRestrictions] = useState<string[]>([])
  
  // Job state
  const [currentJob, setCurrentJob] = useState<Job | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Load data
  useEffect(() => {
    async function loadData() {
      try {
        const [contractsData, restrictionsData] = await Promise.all([
          getContracts(),
          getRestrictionPresets()
        ])
        setContracts(contractsData)
        setRestrictions(restrictionsData)
        if (contractsData.length > 0) {
          setSelectedContract(contractsData[0].id)
        }
      } catch (err) {
        console.error('Failed to load data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Handle login
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setAuthError('')
    try {
      await login(email, password)
      setIsLoggedIn(true)
    } catch (err) {
      setAuthError('Invalid credentials')
    }
  }

  // Handle logout
  function handleLogout() {
    logout()
    setIsLoggedIn(false)
    setCurrentJob(null)
  }

  // Submit job
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isLoggedIn) {
      setError('Please log in first')
      return
    }
    
    setIsSubmitting(true)
    setError('')
    setCurrentJob(null)
    
    try {
      const result = await submitJob({
        contract_id: selectedContract,
        num_runs: numRuns,
        temperature,
        model: 'gpt-4o-mini',
        restriction_ids: selectedRestrictions
      })
      
      // Poll for job completion
      let job: Job
      do {
        await new Promise(r => setTimeout(r, 1000))
        job = await getJob(result.job_id)
        setCurrentJob(job)
      } while (job.status === 'queued' || job.status === 'running')
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit job')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">Back</span>
            </Link>
            <div className="flex items-center gap-3">
              <img src="/images/sky-logo-2.png" alt="SKYT Logo" className="h-10 w-auto" />
              <div>
                <h1 className="text-xl font-bold">SKYT Playground</h1>
                <p className="text-xs text-muted-foreground">Software Repeatability as a Service</p>
              </div>
            </div>
          </div>
          
          {isLoggedIn ? (
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-muted hover:bg-accent rounded-lg text-sm transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          ) : (
            <form onSubmit={handleLogin} className="flex items-center gap-2">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="px-3 py-2 bg-card border border-border rounded-lg text-sm w-40"
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="px-3 py-2 bg-card border border-border rounded-lg text-sm w-32"
              />
              <button 
                type="submit"
                className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg text-sm transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Login
              </button>
              {authError && <span className="text-destructive text-sm">{authError}</span>}
            </form>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Playground Form */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Play className="w-5 h-5 text-primary" />
              Playground
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Contract Selection */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                  <FileCode className="w-4 h-4" />
                  Contract
                </label>
                <select
                  value={selectedContract}
                  onChange={e => setSelectedContract(e.target.value)}
                  className="w-full px-4 py-3 bg-muted border border-border rounded-lg"
                >
                  {contracts.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.id} - {c.task_intent}
                    </option>
                  ))}
                </select>
              </div>

              {/* Parameters */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Number of Runs
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={numRuns}
                    onChange={e => setNumRuns(parseInt(e.target.value))}
                    className="w-full px-4 py-3 bg-muted border border-border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Temperature
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={2}
                    step={0.1}
                    value={temperature}
                    onChange={e => setTemperature(parseFloat(e.target.value))}
                    className="w-full px-4 py-3 bg-muted border border-border rounded-lg"
                  />
                </div>
              </div>

              {/* Restrictions */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Restriction Sets (Optional)
                </label>
                <div className="space-y-2">
                  {restrictions.map(r => (
                    <label key={r.id} className="flex items-center gap-3 p-3 bg-muted rounded-lg cursor-pointer hover:bg-accent transition-colors">
                      <input
                        type="checkbox"
                        checked={selectedRestrictions.includes(r.id)}
                        onChange={e => {
                          if (e.target.checked) {
                            setSelectedRestrictions([...selectedRestrictions, r.id])
                          } else {
                            setSelectedRestrictions(selectedRestrictions.filter(id => id !== r.id))
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <div>
                        <div className="font-medium">{r.name}</div>
                        <div className="text-xs text-muted-foreground">{r.rule_count} rules • {r.authority}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isSubmitting || !isLoggedIn}
                className="w-full py-3 bg-primary hover:bg-primary/90 disabled:bg-muted disabled:cursor-not-allowed text-primary-foreground rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Run Experiment
                  </>
                )}
              </button>

              {error && (
                <div className="p-3 bg-destructive/10 border border-destructive/50 rounded-lg text-destructive text-sm">
                  {error}
                </div>
              )}
            </form>
          </div>

          {/* Results */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              Results
            </h2>

            {!currentJob ? (
              <div className="text-center text-muted-foreground py-12">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Run an experiment to see results</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Status */}
                <div className="flex items-center gap-3">
                  {currentJob.status === 'completed' ? (
                    <CheckCircle className="w-6 h-6 text-primary" />
                  ) : currentJob.status === 'failed' ? (
                    <XCircle className="w-6 h-6 text-destructive" />
                  ) : (
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  )}
                  <div>
                    <div className="font-medium capitalize">{currentJob.status}</div>
                    <div className="text-sm text-muted-foreground">Job ID: {currentJob.job_id.slice(0, 8)}...</div>
                  </div>
                </div>

                {/* Metrics */}
                {currentJob.metrics && (
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard 
                      label="R_raw" 
                      value={currentJob.metrics.R_raw} 
                      description="Raw repeatability"
                    />
                    <MetricCard 
                      label="R_anchor (pre)" 
                      value={currentJob.metrics.R_anchor_pre} 
                      description="Before canonicalization"
                    />
                    <MetricCard 
                      label="R_anchor (post)" 
                      value={currentJob.metrics.R_anchor_post} 
                      description="After canonicalization"
                    />
                    <MetricCard 
                      label="Δ_rescue" 
                      value={currentJob.metrics.Delta_rescue} 
                      description="Improvement from repair"
                      highlight
                    />
                    <MetricCard 
                      label="R_behavioral" 
                      value={currentJob.metrics.R_behavioral} 
                      description="Oracle pass rate"
                    />
                    <MetricCard 
                      label="R_structural" 
                      value={currentJob.metrics.R_structural} 
                      description="Structural compliance"
                    />
                  </div>
                )}

                {/* Job Info */}
                <div className="text-sm text-muted-foreground pt-4 border-t border-border">
                  <div>Contract: <span className="text-foreground">{currentJob.contract_id}</span></div>
                  <div>Runs: <span className="text-foreground">{currentJob.num_runs}</span></div>
                  <div>Temperature: <span className="text-foreground">{currentJob.temperature}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function MetricCard({ 
  label, 
  value, 
  description, 
  highlight = false 
}: { 
  label: string
  value: number
  description: string
  highlight?: boolean
}) {
  const percentage = Math.round(value * 100)
  
  return (
    <div className={`p-4 rounded-lg ${highlight ? 'bg-primary/10 border border-primary/50' : 'bg-muted'}`}>
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className={`text-2xl font-bold ${highlight ? 'text-primary' : 'text-foreground'}`}>
        {percentage}%
      </div>
      <div className="text-xs text-muted-foreground">{description}</div>
    </div>
  )
}

export default Playground

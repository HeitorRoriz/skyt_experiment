import { useState } from "react"
import { Code, Shield, CheckCircle, Zap, ChevronRight, ArrowRight } from "lucide-react"
import { Button } from "../components/ui/Button"
import { Card } from "../components/ui/Card"
import { Link } from "react-router-dom"

export default function LandingPage() {
  const [activeCode, setActiveCode] = useState(0)
  const [contactForm, setContactForm] = useState({ name: '', email: '', company: '', message: '' })
  const [contactStatus, setContactStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

  async function handleContactSubmit(e: React.FormEvent) {
    e.preventDefault()
    setContactStatus('sending')
    
    try {
      const response = await fetch('https://formspree.io/f/xldyrbde', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ ...contactForm, _subject: 'Sales Inquiry from SKYT Website' })
      })
      
      if (response.ok) {
        setContactStatus('sent')
        setContactForm({ name: '', email: '', company: '', message: '' })
      } else {
        throw new Error('Failed')
      }
    } catch {
      setContactStatus('error')
    }
  }

  const codeExamples = [
    { label: "Run 1", code: "def fib(n):\n  if n <= 1: return n\n  return fib(n-1) + fib(n-2)", status: "variant" },
    {
      label: "Run 2",
      code: "def fibonacci(n):\n  a, b = 0, 1\n  for _ in range(n):\n    a, b = b, a+b\n  return a",
      status: "variant",
    },
    {
      label: "Run 3",
      code: "def fib(n):\n  if n == 0: return 0\n  if n == 1: return 1\n  return fib(n-1) + fib(n-2)",
      status: "variant",
    },
    {
      label: "Canonical",
      code: "def fibonacci(n):\n  a, b = 0, 1\n  for _ in range(n):\n    a, b = b, a+b\n  return a",
      status: "canonical",
    },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-end">
            <nav className="hidden md:flex items-center gap-6">
              <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                How It Works
              </a>
              <a href="#use-cases" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Use Cases
              </a>
              <a
                href="#documentation"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Documentation
              </a>
              <Link to="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </Link>
              <Link to="/login">
                <Button size="sm">
                  Sign In
                </Button>
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-8 pb-24 md:pt-12 md:pb-32">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left: Headline and CTAs */}
            <div className="space-y-8">
              <div className="flex justify-center mb-6">
                <img src="/images/sky-logo-2.png" alt="SKYT Logo" className="h-80 w-auto" />
              </div>
              <div className="space-y-4">
                <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight text-balance text-center">
                  Same Prompt. Same Code. Every Time.
                </h1>
                <p className="text-xl text-muted-foreground leading-relaxed text-pretty text-center">
                  Skyt turns your best AI-generated code into a shared, locked-in standard. Every engineer, every
                  prompt, every run — the same trusted implementation.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/pricing">
                  <Button size="lg" className="w-full sm:w-auto">
                    Get Early Access
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <a href="#documentation">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto">
                    Read the Docs
                  </Button>
                </a>
              </div>
            </div>

            {/* Right: Animated Code Comparison */}
            <div className="relative">
              <Card className="p-6 space-y-4">
                {codeExamples.map((example, index) => (
                  <div
                    key={index}
                    className={`transition-all duration-500 ${
                      activeCode === index ? "opacity-100 scale-100" : "opacity-40 scale-95"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted-foreground">{example.label}</span>
                      {example.status === "canonical" && (
                        <div className="flex items-center gap-1 text-xs font-medium text-primary">
                          <CheckCircle className="h-4 w-4" />
                          Canonical
                        </div>
                      )}
                    </div>
                    <pre className="bg-accent/50 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                      <code>{example.code}</code>
                    </pre>
                  </div>
                ))}
                <div className="flex items-center justify-center gap-2 pt-2">
                  {codeExamples.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setActiveCode(index)}
                      className={`h-2 rounded-full transition-all ${
                        activeCode === index ? "w-8 bg-primary" : "w-2 bg-muted"
                      }`}
                      aria-label={`Show code example ${index + 1}`}
                    />
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">The Problem with AI Code Generation</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Non-deterministic outputs make AI-generated code unsuitable for production systems
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Code className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Inconsistent Outputs</h3>
              <p className="text-muted-foreground leading-relaxed">
                Same prompt generates different code every time, making version control and testing nearly impossible.
              </p>
            </Card>
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Untestable</h3>
              <p className="text-muted-foreground leading-relaxed">
                Can't write reliable tests for non-deterministic outputs that change on every generation.
              </p>
            </Card>
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Unauditable</h3>
              <p className="text-muted-foreground leading-relaxed">
                No compliance trail for safety-critical systems that require certification and audit logs.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="how-it-works" className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">How Skyt Keeps Your Code Consistent</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Three simple steps to lock in your AI-generated standards
            </p>
            <ul className="flex flex-col md:flex-row justify-center gap-6 mt-8 text-muted-foreground">
              <li className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
                <span>Normalize AI output into canonical functions</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
                <span>Enforce consistency across teams</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
                <span>Track changes and diff suggestions</span>
              </li>
            </ul>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="relative">
              <Card className="p-8 space-y-4 h-full">
                <div className="h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold">
                  1
                </div>
                <h3 className="text-2xl font-semibold">Capture Your Best Implementation</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Point Skyt at the code you actually want as the "source of truth".
                </p>
              </Card>
              <ArrowRight className="hidden md:block absolute -right-4 top-1/2 -translate-y-1/2 h-8 w-8 text-muted-foreground" />
            </div>
            <div className="relative">
              <Card className="p-8 space-y-4 h-full">
                <div className="h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold">
                  2
                </div>
                <h3 className="text-2xl font-semibold">Map Prompts to a Canonical Version</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Skyt normalizes raw LLM output into your approved implementation.
                </p>
              </Card>
              <ArrowRight className="hidden md:block absolute -right-4 top-1/2 -translate-y-1/2 h-8 w-8 text-muted-foreground" />
            </div>
            <div>
              <Card className="p-8 space-y-4 h-full">
                <div className="h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold">
                  3
                </div>
                <h3 className="text-2xl font-semibold">Enforce and Evolve Standards</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Track changes, review diffs, and roll out updates to the whole team.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Section */}
      <section className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Real Results</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Proven improvements in code repeatability and compliance
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-5xl mx-auto">
            <Card className="p-8 text-center space-y-2">
              <div className="text-5xl font-bold text-primary">80%</div>
              <div className="text-sm text-muted-foreground">Repeatability improvement (Δ_rescue)</div>
            </Card>
            <Card className="p-8 text-center space-y-2">
              <div className="text-5xl font-bold text-primary">100%</div>
              <div className="text-sm text-muted-foreground">Behavioral correctness maintained</div>
            </Card>
            <Card className="p-8 text-center space-y-2">
              <div className="text-5xl font-bold text-primary">5</div>
              <div className="text-sm text-muted-foreground">Certification presets (NASA, MISRA, DO-178C)</div>
            </Card>
            <Card className="p-8 text-center space-y-2">
              <div className="text-5xl font-bold text-primary">7</div>
              <div className="text-sm text-muted-foreground">Algorithm families supported</div>
            </Card>
          </div>
        </div>
      </section>

      {/* Industry Standards Section */}
      <section id="standards" className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Pre-Configured Industry Standards</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Ship with compliance built-in. Skyt comes with ready-to-use restriction presets for safety-critical industries.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 max-w-6xl mx-auto">
            <Card className="p-6 text-center hover:border-primary/50 transition-colors">
              <div className="text-3xl mb-3">🚀</div>
              <h3 className="font-semibold mb-1">NASA JPL</h3>
              <p className="text-sm text-muted-foreground">Power of Ten Rules for safety-critical C code</p>
            </Card>
            <Card className="p-6 text-center hover:border-primary/50 transition-colors">
              <div className="text-3xl mb-3">🚗</div>
              <h3 className="font-semibold mb-1">MISRA C/C++</h3>
              <p className="text-sm text-muted-foreground">Automotive industry coding guidelines</p>
            </Card>
            <Card className="p-6 text-center hover:border-primary/50 transition-colors">
              <div className="text-3xl mb-3">✈️</div>
              <h3 className="font-semibold mb-1">DO-178C</h3>
              <p className="text-sm text-muted-foreground">Aviation software certification standard</p>
            </Card>
            <Card className="p-6 text-center hover:border-primary/50 transition-colors">
              <div className="text-3xl mb-3">⚙️</div>
              <h3 className="font-semibold mb-1">AUTOSAR</h3>
              <p className="text-sm text-muted-foreground">Automotive open system architecture</p>
            </Card>
            <Card className="p-6 text-center hover:border-primary/50 transition-colors">
              <div className="text-3xl mb-3">🏥</div>
              <h3 className="font-semibold mb-1">IEC 62304</h3>
              <p className="text-sm text-muted-foreground">Medical device software lifecycle</p>
            </Card>
          </div>
          <p className="text-center text-muted-foreground mt-8">
            Custom presets available for enterprise teams
          </p>
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Built for AI-First Engineering Teams</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Keep velocity while standardizing how AI writes code
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Code className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Backend & Platform Teams</h3>
              <p className="text-muted-foreground leading-relaxed">
                Guarantee consistent service patterns and error handling across all AI-generated code.
              </p>
            </Card>
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Internal Tools & DevEx</h3>
              <p className="text-muted-foreground leading-relaxed">
                Turn internal prompt recipes into enforceable standards that everyone follows.
              </p>
            </Card>
            <Card className="p-8 space-y-4 hover:border-primary/50 transition-colors">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">Tech Leads & CTOs</h3>
              <p className="text-muted-foreground leading-relaxed">
                Keep velocity while standardizing how AI writes code across your entire organization.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Documentation Section */}
      <section id="documentation" className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Documentation at a Glance</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Skyt ships with lightweight docs so your team can get consistent AI code in minutes, not weeks of
              onboarding.
            </p>
          </div>
          <div className="max-w-3xl mx-auto space-y-6">
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <li className="flex items-center gap-3 text-lg">
                <CheckCircle className="h-6 w-6 text-primary flex-shrink-0" />
                <span>Quickstart</span>
              </li>
              <li className="flex items-center gap-3 text-lg">
                <CheckCircle className="h-6 w-6 text-primary flex-shrink-0" />
                <span>Integration guides</span>
              </li>
              <li className="flex items-center gap-3 text-lg">
                <CheckCircle className="h-6 w-6 text-primary flex-shrink-0" />
                <span>Governance & review</span>
              </li>
              <li className="flex items-center gap-3 text-lg">
                <CheckCircle className="h-6 w-6 text-primary flex-shrink-0" />
                <span>API reference</span>
              </li>
            </ul>
            <div className="text-center pt-6">
              <Button size="lg" variant="outline" disabled className="opacity-50">
                Open Docs (Coming Soon)
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <Card className="bg-primary text-primary-foreground border-0 max-w-4xl mx-auto">
            <div className="p-12 md:p-16 text-center space-y-8">
              <h2 className="text-3xl md:text-4xl font-bold text-balance">
                Ready to make AI code generation production-ready?
              </h2>
              <p className="text-lg text-primary-foreground/80 max-w-2xl mx-auto">
                Join leading aerospace, automotive, and medical device companies using Skyt for mission-critical
                systems.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/signup">
                  <Button size="lg" className="bg-background text-foreground hover:bg-background/90">
                    Start Free Trial
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <a href="#contact">
                  <Button
                    size="lg"
                    variant="outline"
                    className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10"
                  >
                    Talk to Sales
                  </Button>
                </a>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 bg-accent/30">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">Talk to Sales</h2>
              <p className="text-lg text-muted-foreground">
                Have questions about enterprise features, custom integrations, or volume pricing? We'd love to hear from you.
              </p>
            </div>
            <Card className="p-8">
              {contactStatus === 'sent' ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-16 h-16 text-primary mx-auto mb-4" />
                  <h3 className="text-2xl font-bold mb-2">Message Sent!</h3>
                  <p className="text-muted-foreground">We'll get back to you within 24 hours.</p>
                </div>
              ) : (
                <form onSubmit={handleContactSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="contact-name" className="block text-sm font-medium mb-2">Name</label>
                      <input
                        id="contact-name"
                        type="text"
                        required
                        placeholder="Your name"
                        value={contactForm.name}
                        onChange={(e) => setContactForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div>
                      <label htmlFor="contact-email" className="block text-sm font-medium mb-2">Email</label>
                      <input
                        id="contact-email"
                        type="email"
                        required
                        placeholder="you@company.com"
                        value={contactForm.email}
                        onChange={(e) => setContactForm(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="contact-company" className="block text-sm font-medium mb-2">Company</label>
                    <input
                      id="contact-company"
                      type="text"
                      placeholder="Company name"
                      value={contactForm.company}
                      onChange={(e) => setContactForm(prev => ({ ...prev, company: e.target.value }))}
                      className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label htmlFor="contact-message" className="block text-sm font-medium mb-2">Message</label>
                    <textarea
                      id="contact-message"
                      rows={4}
                      required
                      placeholder="Tell us about your needs..."
                      value={contactForm.message}
                      onChange={(e) => setContactForm(prev => ({ ...prev, message: e.target.value }))}
                      className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    />
                  </div>
                  {contactStatus === 'error' && (
                    <p className="text-destructive text-sm text-center">Something went wrong. Please try again.</p>
                  )}
                  <Button type="submit" size="lg" className="w-full" disabled={contactStatus === 'sending'}>
                    {contactStatus === 'sending' ? 'Sending...' : (
                      <>
                        Send Message
                        <ChevronRight className="ml-2 h-5 w-5" />
                      </>
                    )}
                  </Button>
                </form>
              )}
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div className="space-y-4 text-center">
              <div className="flex items-center justify-center">
                <img src="/images/sky-logo-2.png" alt="SKYT Logo" className="h-20 w-auto" />
              </div>
              <p className="text-sm text-muted-foreground">Prompt. Verify. Deploy.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    GitHub
                  </a>
                </li>
                <li>
                  <Link to="/playground" className="hover:text-foreground transition-colors">
                    Playground
                  </Link>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    API
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <Link to="/pricing" className="hover:text-foreground transition-colors">
                    Pricing
                  </Link>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Contact
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-border text-center text-sm text-muted-foreground">
            <p>&copy; 2025 SKYT. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

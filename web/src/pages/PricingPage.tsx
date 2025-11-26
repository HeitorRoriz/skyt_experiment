import { CheckCircle, ChevronRight } from "lucide-react"
import { Button } from "../components/ui/Button"
import { Card } from "../components/ui/Card"
import { Link } from "react-router-dom"

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/">
              <img src="/images/sky-logo-2.png" alt="SKYT Logo" className="h-20 w-auto" />
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link
                to="/#how-it-works"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                How It Works
              </Link>
              <Link
                to="/#use-cases"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Use Cases
              </Link>
              <Link
                to="/#documentation"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Documentation
              </Link>
              <Link to="/pricing" className="text-sm text-foreground font-medium">
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

      {/* Pricing Content */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-bold">Pricing</h1>
              <p className="text-xl text-muted-foreground leading-relaxed">
                Skyt is in private beta with a simple seat-based model. We're working closely with a small group of
                teams to shape the product.
              </p>
            </div>

            <Card className="p-12 space-y-8 max-w-2xl mx-auto">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold">Private Beta</h2>
                <p className="text-lg text-muted-foreground">Custom pricing for early design partners</p>
              </div>

              <ul className="space-y-4 text-left">
                <li className="flex items-start gap-3">
                  <CheckCircle className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-lg">Unlimited canonical functions during beta</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-lg">Hands-on onboarding for your team</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-lg">Direct input into roadmap and features</span>
                </li>
              </ul>

              <Link to="/login" className="block">
                <Button
                  size="lg"
                  className="w-full h-12 text-base"
                >
                  Request Access
                  <ChevronRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </Card>
          </div>
        </div>
      </section>
    </div>
  )
}

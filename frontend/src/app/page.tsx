import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="font-bold text-xl">finLine</div>
          <nav className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Login
            </Link>
            <Link
              href="/login?signup=true"
              className="text-sm bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1">
        <section className="py-24 sm:py-32">
          <div className="container mx-auto px-4 text-center">
            <h1 className="text-4xl sm:text-6xl font-bold tracking-tight fade-in">
              LBO Modeling,{" "}
              <span className="text-primary">Simplified</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto fade-in">
              Build leveraged buyout models in minutes. Upload your financials,
              configure your deal, and get IRR and MOIC instantly.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4 fade-in">
              <Link
                href="/login?signup=true"
                className="bg-primary text-primary-foreground px-6 py-3 rounded-md font-medium hover:bg-primary/90"
              >
                Start Building Now
              </Link>
              <Link
                href="#features"
                className="text-foreground px-6 py-3 rounded-md font-medium hover:bg-secondary"
              >
                Learn More
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-24 bg-secondary">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">
              Everything You Need
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              <FeatureCard
                title="Simple Input"
                description="Just provide your EBITDA and key financials. No complex P&L formatting required."
              />
              <FeatureCard
                title="Flexible Debt"
                description="Multiple tranches with PIK, amortization schedules, and floating rates."
              />
              <FeatureCard
                title="Chat Assistant"
                description="Update your model with natural language. 'Set CAPEX to 5% of revenue.'"
              />
              <FeatureCard
                title="Instant Analysis"
                description="IRR, MOIC, debt schedules, and cash flows calculated in seconds."
              />
              <FeatureCard
                title="Multiple Scenarios"
                description="Base, upside, and downside cases. Compare outcomes side by side."
              />
              <FeatureCard
                title="Excel Export"
                description="Download your model in a clean Excel format for presentations."
              />
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          finLine - LBO Financial Modeling
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}

import Link from 'next/link';
import { getAIServices, getAIStats } from '@/lib/ai-db';
import AIServicesTable from './AIServicesTable';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function AIServicesPage() {
  try {
    const services = await getAIServices();
    const stats = await getAIStats();

    return (
      <div className="min-h-screen bg-cream">
        <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
          <div className="container mx-auto px-4">
            <Breadcrumbs
              items={[
                { label: 'AI Services', href: undefined },
              ]}
            />
            <h1 className="font-serif text-3xl font-medium text-white">AI Services in FedRAMP</h1>
            <p className="text-charcoal-300 mt-2">
              FedRAMP-authorized AI, Generative AI, and LLM services
            </p>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          {/* Statistics Dashboard */}
          <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
            <h2 className="font-serif text-xl font-medium text-charcoal mb-4">AI Services Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-600">
                <div className="text-2xl font-semibold text-charcoal">{stats.total_ai_services}</div>
                <div className="text-sm text-charcoal-500">Total AI Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-purple">
                <div className="text-2xl font-semibold text-charcoal">{stats.count_ai}</div>
                <div className="text-sm text-charcoal-500">AI/ML Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-orange">
                <div className="text-2xl font-semibold text-charcoal">{stats.count_genai}</div>
                <div className="text-sm text-charcoal-500">Generative AI</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-400">
                <div className="text-2xl font-semibold text-charcoal">{stats.count_llm}</div>
                <div className="text-sm text-charcoal-500">LLM Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
                <div className="text-2xl font-semibold text-charcoal">{stats.products_with_ai}</div>
                <div className="text-sm text-charcoal-500">Products</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
                <div className="text-2xl font-semibold text-charcoal">{stats.providers_with_ai}</div>
                <div className="text-sm text-charcoal-500">Providers</div>
              </div>
            </div>
          </div>

          {/* Info Panel */}
          <div className="bg-cream-200 border border-charcoal-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-charcoal mb-2">About This Analysis</h3>
            <p className="text-sm text-charcoal-600 mb-2">
              All 615 FedRAMP products were analyzed using Claude Haiku 4.5 to identify services related to
              Artificial Intelligence, Generative AI, and Large Language Models.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
                AI/ML: Machine Learning, AI platforms
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
                GenAI: Generative AI services
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
                LLM: Large Language Model services
              </span>
            </div>
          </div>

          {/* Link to Agency AI Usage */}
          <Link
            href="/agency-ai-usage"
            className="block bg-white border-2 border-charcoal-300 rounded-lg p-6 mb-6 hover:border-ifp-purple hover:shadow-md transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-serif text-2xl font-medium text-charcoal mb-2">Federal Agency AI Usage</h2>
                <p className="text-charcoal-500">
                  See how federal agencies are adopting AI internally with staff chatbots and coding assistants
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-charcoal-400 mb-1">34 agencies tracked</div>
                <div className="text-sm font-semibold text-ifp-purple">View Agency Usage →</div>
              </div>
            </div>
          </Link>

          {/* Services Table */}
          {services.length > 0 ? (
            <AIServicesTable services={services} />
          ) : (
            <div className="bg-white rounded-lg border border-charcoal-200 p-12 text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h2 className="font-serif text-2xl font-medium text-charcoal mb-2">
                Analysis In Progress
              </h2>
              <p className="text-charcoal-500 mb-4">
                The AI service analysis is currently running. This may take 15-30 minutes.
              </p>
              <p className="text-sm text-charcoal-400">
                Refresh this page once the analysis is complete to see results.
              </p>
            </div>
          )}
        </main>

        <footer className="bg-charcoal-900 text-cream py-6 mt-12 border-t-4 border-ifp-purple">
          <div className="container mx-auto px-4 text-center text-sm">
            <p>
              AI analysis powered by Anthropic Claude Haiku 4.5
            </p>
            <p className="mt-2 text-charcoal-400">
              Data source: <a href="https://marketplace.fedramp.gov/" className="text-charcoal-300 hover:text-cream underline">FedRAMP Marketplace</a>
            </p>
          </div>
        </footer>
      </div>
    );
  } catch (error) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="bg-white rounded-lg border border-charcoal-200 p-8 max-w-md text-center">
          <div className="text-6xl mb-4">⏳</div>
          <h2 className="font-serif text-2xl font-medium text-charcoal mb-2">
            Analysis In Progress
          </h2>
          <p className="text-charcoal-500 mb-4">
            The AI service analysis hasn't completed yet. Please wait a few minutes and refresh the page.
          </p>
          <Link href="/" className="text-ifp-purple hover:text-ifp-purple-dark font-medium underline">
            ← Return to Home
          </Link>
        </div>
      </div>
    );
  }
}

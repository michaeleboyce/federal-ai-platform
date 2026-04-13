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
      <div className="min-h-screen bg-gov-slate-50">
        <header className="bg-gov-navy-900 text-white py-6 border-b-4 border-gov-navy-700">
          <div className="container mx-auto px-4">
            <Breadcrumbs
              items={[
                { label: 'AI Services', href: undefined },
              ]}
            />
            <h1 className="text-3xl font-bold">AI Services in FedRAMP</h1>
            <p className="text-gov-navy-100 mt-2">
              FedRAMP-authorized AI, Generative AI, and LLM services
            </p>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          {/* Statistics Dashboard */}
          <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
            <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">AI Services Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-600">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.total_ai_services}</div>
                <div className="text-sm text-gov-slate-600">Total AI Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-ai-blue">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.count_ai}</div>
                <div className="text-sm text-gov-slate-600">AI/ML Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-ai-teal">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.count_genai}</div>
                <div className="text-sm text-gov-slate-600">Generative AI</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-ai-indigo">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.count_llm}</div>
                <div className="text-sm text-gov-slate-600">LLM Services</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.products_with_ai}</div>
                <div className="text-sm text-gov-slate-600">Products</div>
              </div>
              <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
                <div className="text-2xl font-bold text-gov-navy-900">{stats.providers_with_ai}</div>
                <div className="text-sm text-gov-slate-600">Providers</div>
              </div>
            </div>
          </div>

          {/* Info Panel */}
          <div className="bg-gov-navy-50 border border-gov-navy-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-gov-navy-900 mb-2">About This Analysis</h3>
            <p className="text-sm text-gov-slate-700 mb-2">
              All 615 FedRAMP products were analyzed using Claude Haiku 4.5 to identify services related to
              Artificial Intelligence, Generative AI, and Large Language Models.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
                AI/ML: Machine Learning, AI platforms
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-teal-light text-ai-teal-dark border border-ai-teal">
                GenAI: Generative AI services
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
                LLM: Large Language Model services
              </span>
            </div>
          </div>

          {/* Link to Agency AI Usage */}
          <Link
            href="/agency-ai-usage"
            className="block bg-white border-2 border-gov-navy-800 rounded-lg p-6 mb-6 hover:border-gov-navy-700 hover:shadow-md transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gov-navy-900 mb-2">Federal Agency AI Usage</h2>
                <p className="text-gov-slate-600">
                  See how federal agencies are adopting AI internally with staff chatbots and coding assistants
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-gov-slate-500 mb-1">34 agencies tracked</div>
                <div className="text-sm font-semibold text-gov-navy-700">View Agency Usage →</div>
              </div>
            </div>
          </Link>

          {/* Services Table */}
          {services.length > 0 ? (
            <AIServicesTable services={services} />
          ) : (
            <div className="bg-white rounded-lg border border-gov-slate-200 p-12 text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h2 className="text-2xl font-semibold text-gov-navy-900 mb-2">
                Analysis In Progress
              </h2>
              <p className="text-gov-slate-600 mb-4">
                The AI service analysis is currently running. This may take 15-30 minutes.
              </p>
              <p className="text-sm text-gov-slate-500">
                Refresh this page once the analysis is complete to see results.
              </p>
            </div>
          )}
        </main>

        <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
          <div className="container mx-auto px-4 text-center text-sm">
            <p>
              AI analysis powered by Anthropic Claude Haiku 4.5
            </p>
            <p className="mt-2 text-gov-slate-400">
              Data source: <a href="https://marketplace.fedramp.gov/" className="text-gov-navy-200 hover:text-white underline">FedRAMP Marketplace</a>
            </p>
          </div>
        </footer>
      </div>
    );
  } catch (error) {
    return (
      <div className="min-h-screen bg-gov-slate-50 flex items-center justify-center">
        <div className="bg-white rounded-lg border border-gov-slate-200 p-8 max-w-md text-center">
          <div className="text-6xl mb-4">⏳</div>
          <h2 className="text-2xl font-semibold text-gov-navy-900 mb-2">
            Analysis In Progress
          </h2>
          <p className="text-gov-slate-600 mb-4">
            The AI service analysis hasn't completed yet. Please wait a few minutes and refresh the page.
          </p>
          <Link href="/" className="text-gov-navy-700 hover:text-gov-navy-900 font-medium underline">
            ← Return to Home
          </Link>
        </div>
      </div>
    );
  }
}

import Link from 'next/link';
import { getUseCases, getUseCaseStats, getDomainStats, getUniqueValues } from '@/lib/use-case-db';
import UseCaseTable from './UseCaseTable';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function UseCasesPage() {
  const useCases = await getUseCases();
  const stats = await getUseCaseStats();
  const domainStats = await getDomainStats();

  // Get unique values for filters
  const domains = await getUniqueValues('domain_category');
  const agencies = await getUniqueValues('agency');
  const stages = await getUniqueValues('stage_of_development');

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'AI Use Cases', href: undefined },
            ]}
          />
          <h1 className="font-serif text-3xl font-medium text-white">Federal AI Use Case Inventory</h1>
          <p className="text-charcoal-300 mt-2">
            {stats.total_use_cases} AI implementations across {stats.total_agencies} federal agencies
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Description */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-8">
          <p className="text-charcoal-600 text-lg leading-relaxed">
            This comprehensive inventory tracks <strong>specific AI use cases</strong> deployed across the federal government.
            From document intelligence and customer support to law enforcement and healthcare, explore how agencies are
            implementing AI/ML, generative AI, LLMs, chatbots, and more.
          </p>
        </div>

        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
          <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Use Case Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-600">
              <div className="text-3xl font-semibold text-charcoal">{stats.total_use_cases}</div>
              <div className="text-sm text-charcoal-500">Total Use Cases</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-orange">
              <div className="text-3xl font-semibold text-charcoal">{stats.genai_count}</div>
              <div className="text-sm text-charcoal-500">GenAI</div>
              <div className="text-xs text-charcoal-400 mt-1">
                {((stats.genai_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-400">
              <div className="text-3xl font-semibold text-charcoal">{stats.llm_count}</div>
              <div className="text-sm text-charcoal-500">With LLMs</div>
              <div className="text-xs text-charcoal-400 mt-1">
                {((stats.llm_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ifp-purple">
              <div className="text-3xl font-semibold text-charcoal">{stats.chatbot_count}</div>
              <div className="text-sm text-charcoal-500">Chatbots</div>
              <div className="text-xs text-charcoal-400 mt-1">
                {((stats.chatbot_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-300">
              <div className="text-3xl font-semibold text-charcoal">{stats.classic_ml_count}</div>
              <div className="text-sm text-charcoal-500">Classic ML</div>
              <div className="text-xs text-charcoal-400 mt-1">
                {((stats.classic_ml_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-3xl font-semibold text-charcoal">{stats.coding_assistant_count}</div>
              <div className="text-sm text-charcoal-500">Coding Tools</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-info">
              <div className="text-3xl font-semibold text-charcoal">{stats.implemented_count}</div>
              <div className="text-sm text-charcoal-500">Implemented</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
              <div className="text-3xl font-semibold text-charcoal">{stats.in_development_count}</div>
              <div className="text-sm text-charcoal-500">In Development</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-error">
              <div className="text-3xl font-semibold text-charcoal">{stats.rights_impacting_count}</div>
              <div className="text-sm text-charcoal-500">Rights-Impacting</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-charcoal-700">
              <div className="text-3xl font-semibold text-charcoal">{stats.total_agencies}</div>
              <div className="text-sm text-charcoal-500">Agencies</div>
            </div>
          </div>
        </div>

        {/* Domain Distribution */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
          <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Use Cases by Domain</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {domainStats.slice(0, 12).map((domain) => (
              <Link
                key={domain.domain_category}
                href={`/use-cases?domain=${encodeURIComponent(domain.domain_category)}`}
                className="flex items-center justify-between p-4 bg-cream rounded-lg border border-charcoal-200 hover:border-ifp-purple hover:bg-white transition-all"
              >
                <div>
                  <div className="font-semibold text-charcoal">{domain.domain_category}</div>
                  <div className="text-xs text-charcoal-500 mt-1">
                    {domain.genai_count > 0 && `${domain.genai_count} GenAI`}
                  </div>
                </div>
                <div className="text-2xl font-semibold text-charcoal-600">{domain.count}</div>
              </Link>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-cream-200 border border-charcoal-200 rounded-lg p-6 mb-6">
          <h3 className="font-serif text-lg font-medium text-charcoal mb-4">Related Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/ai-services"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-ifp-purple-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ifp-purple-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">FedRAMP AI Services</div>
                <div className="text-xs text-charcoal-500">Available cloud services</div>
              </div>
            </Link>

            <Link
              href="/agency-ai-usage"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-ifp-orange-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ifp-orange-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">Agency AI Adoption</div>
                <div className="text-xs text-charcoal-500">Internal staff tools</div>
              </div>
            </Link>

            <Link
              href="/"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-charcoal-200 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-charcoal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">Dashboard Home</div>
                <div className="text-xs text-charcoal-500">Overview & stats</div>
              </div>
            </Link>
          </div>
        </div>

        {/* Use Cases Table */}
        <UseCaseTable
          useCases={useCases}
          domains={domains}
          agencies={agencies}
          stages={stages}
        />
      </main>

      <footer className="bg-charcoal-900 text-cream py-6 mt-12 border-t-4 border-ifp-purple">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source: Federal AI use case inventory submissions as of {new Date().toLocaleDateString()}
          </p>
          <p className="mt-2 text-charcoal-400">
            Classified and analyzed using AI • Updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

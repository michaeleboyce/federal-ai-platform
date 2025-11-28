import Link from 'next/link';
import { getUseCases, getUseCaseStats, getDomainStats, getUniqueValues } from '@/lib/use-case-db';
import { getUseCasesWithIncidentScores } from '@/lib/incident-db';
import UseCaseTable from './UseCaseTable';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function UseCasesPage() {
  const [useCases, stats, domainStats, domains, agencies, stages, incidentScoreMap] = await Promise.all([
    getUseCases(),
    getUseCaseStats(),
    getDomainStats(),
    getUniqueValues('domain_category'),
    getUniqueValues('agency'),
    getUniqueValues('stage_of_development'),
    getUseCasesWithIncidentScores(),
  ]);

  // Convert Map to Record for JSON serialization
  const incidentScores: Record<number, { maxScore: number; matchCount: number }> = {};
  for (const [key, value] of incidentScoreMap.entries()) {
    incidentScores[key] = value;
  }

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-gov-navy-900 text-white py-6 border-b-4 border-gov-navy-700">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'AI Use Cases', href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold">Federal AI Use Case Inventory</h1>
          <p className="text-gov-navy-100 mt-2">
            {stats.total_use_cases} AI implementations across {stats.total_agencies} federal agencies
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Description */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-8">
          <p className="text-gov-slate-700 text-lg leading-relaxed">
            This comprehensive inventory tracks <strong>specific AI use cases</strong> deployed across the federal government.
            From document intelligence and customer support to law enforcement and healthcare, explore how agencies are
            implementing AI/ML, generative AI, LLMs, chatbots, and more.
          </p>
        </div>

        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Use Case Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-600">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.total_use_cases}</div>
              <div className="text-sm text-gov-slate-600">Total Use Cases</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-teal">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.genai_count}</div>
              <div className="text-sm text-gov-slate-600">GenAI</div>
              <div className="text-xs text-gov-slate-500 mt-1">
                {((stats.genai_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-indigo">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.llm_count}</div>
              <div className="text-sm text-gov-slate-600">With LLMs</div>
              <div className="text-xs text-gov-slate-500 mt-1">
                {((stats.llm_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-blue">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.chatbot_count}</div>
              <div className="text-sm text-gov-slate-600">Chatbots</div>
              <div className="text-xs text-gov-slate-500 mt-1">
                {((stats.chatbot_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-slate-400">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.classic_ml_count}</div>
              <div className="text-sm text-gov-slate-600">Classic ML</div>
              <div className="text-xs text-gov-slate-500 mt-1">
                {((stats.classic_ml_count / stats.total_use_cases) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.coding_assistant_count}</div>
              <div className="text-sm text-gov-slate-600">Coding Tools</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-info">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.implemented_count}</div>
              <div className="text-sm text-gov-slate-600">Implemented</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.in_development_count}</div>
              <div className="text-sm text-gov-slate-600">In Development</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-error">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.rights_impacting_count}</div>
              <div className="text-sm text-gov-slate-600">Rights-Impacting</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-800">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.total_agencies}</div>
              <div className="text-sm text-gov-slate-600">Agencies</div>
            </div>
          </div>
        </div>

        {/* Domain Distribution */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Use Cases by Domain</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {domainStats.slice(0, 12).map((domain) => (
              <Link
                key={domain.domain_category}
                href={`/use-cases?domain=${encodeURIComponent(domain.domain_category)}`}
                className="flex items-center justify-between p-4 bg-gov-slate-50 rounded-lg border border-gov-slate-200 hover:border-gov-navy-600 hover:bg-white transition-all"
              >
                <div>
                  <div className="font-semibold text-gov-navy-900">{domain.domain_category}</div>
                  <div className="text-xs text-gov-slate-600 mt-1">
                    {domain.genai_count > 0 && `${domain.genai_count} GenAI`}
                  </div>
                </div>
                <div className="text-2xl font-bold text-gov-navy-700">{domain.count}</div>
              </Link>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-gov-navy-50 border border-gov-navy-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gov-navy-900 mb-4">Related Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/ai-services"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-ai-blue-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ai-blue-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">FedRAMP AI Services</div>
                <div className="text-xs text-gov-slate-600">Available cloud services</div>
              </div>
            </Link>

            <Link
              href="/agency-ai-usage"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-ai-teal-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ai-teal-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">Agency AI Adoption</div>
                <div className="text-xs text-gov-slate-600">Internal staff tools</div>
              </div>
            </Link>

            <Link
              href="/"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-gov-slate-200 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-gov-navy-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">Dashboard Home</div>
                <div className="text-xs text-gov-slate-600">Overview & stats</div>
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
          incidentScores={incidentScores}
        />
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source: Federal AI use case inventory submissions as of {new Date().toLocaleDateString()}
          </p>
          <p className="mt-2 text-gov-slate-400">
            Classified and analyzed using AI • Updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

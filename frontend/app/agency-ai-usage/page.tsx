import Link from 'next/link';
import { getAgencies, getAgencyStats } from '@/lib/agency-db';
import AgencyAITable from './AgencyAITable';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function AgencyAIUsagePage() {
  const agenciesData = await getAgencies('staff_llm');
  const statsData = await getAgencyStats();

  // Provide default values if data is undefined
  const agencies = agenciesData || [];
  const stats = statsData || {
    total_agencies: 0,
    agencies_with_llm: 0,
    agencies_with_coding: 0,
    agencies_custom_solution: 0,
    agencies_commercial_solution: 0,
    total_matches: 0,
    high_confidence_matches: 0
  };

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-gov-navy-900 text-white py-6 border-b-4 border-gov-navy-700">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Agency AI Usage', href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold">Federal Agency AI Usage</h1>
          <p className="text-gov-navy-100 mt-2">
            How federal agencies are adopting AI internally - staff chatbots, coding assistants, and specialized tools
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Agency AI Adoption Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-600">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.total_agencies}</div>
              <div className="text-sm text-gov-slate-600">Agencies Total</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-blue">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.agencies_with_llm}</div>
              <div className="text-sm text-gov-slate-600">With Staff LLM</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-teal">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.agencies_with_coding}</div>
              <div className="text-sm text-gov-slate-600">With Coding Assistant</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-indigo">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.agencies_custom_solution}</div>
              <div className="text-sm text-gov-slate-600">Custom Solutions</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.agencies_commercial_solution}</div>
              <div className="text-sm text-gov-slate-600">Commercial Solutions</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
              <div className="text-2xl font-bold text-gov-navy-900">{stats.total_matches}</div>
              <div className="text-sm text-gov-slate-600">FedRAMP Matches</div>
            </div>
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-gov-navy-50 border border-gov-navy-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-gov-navy-900 mb-2">About This Data</h3>
          <p className="text-sm text-gov-slate-700 mb-2">
            This dashboard tracks how federal agencies are adopting AI technologies internally, including:
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
              Staff LLM Chatbots (e.g., StateChat, NIPRGPT)
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-teal-light text-ai-teal-dark border border-ai-teal">
              AI Coding Assistants (e.g., GitHub Copilot)
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
              Custom vs Commercial Solutions
            </span>
          </div>
          <p className="text-xs text-gov-slate-600 mt-3">
            Data compiled from public agency announcements, reports, and AI inventories. Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>

        {/* Link to FedRAMP AI Services */}
        <Link
          href="/ai-services"
          className="block bg-white border-2 border-gov-navy-800 rounded-lg p-6 mb-6 hover:border-gov-navy-700 hover:shadow-md transition-all"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gov-navy-900 mb-2">FedRAMP AI Services</h2>
              <p className="text-gov-slate-600">
                View the FedRAMP-authorized AI services that agencies can use
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gov-slate-500 mb-1">{stats.high_confidence_matches} high-confidence matches</div>
              <div className="text-sm font-semibold text-gov-navy-700">View AI Services →</div>
            </div>
          </div>
        </Link>

        {/* Agencies Table */}
        <AgencyAITable agencies={agencies} />
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data compiled from public sources including agency AI inventories, press releases, and government reports
          </p>
          <p className="mt-2 text-gov-slate-400">
            FedRAMP data source: <a href="https://marketplace.fedramp.gov/" className="text-gov-navy-200 hover:text-white underline">FedRAMP Marketplace</a>
          </p>
        </div>
      </footer>
    </div>
  );
}

import Link from 'next/link';
import { getIncidents, getIncidentStats, getIncidentsByYear, getTopEntities } from '@/lib/incident-db';
import IncidentTable from './IncidentTable';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export default async function IncidentsPage() {
  const incidents = await getIncidents();
  const stats = await getIncidentStats();
  const yearStats = await getIncidentsByYear();
  const topEntities = await getTopEntities(12);

  const years = yearStats.map(y => y.year).filter(y => y !== 'Unknown');

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-status-error-dark text-white py-6 border-b-4 border-red-900">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'AI Incidents', href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold">AI Incident Database</h1>
          <p className="text-red-100 mt-2">
            {stats.totalIncidents} documented AI incidents involving {stats.totalEntities} entities
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Description */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-8">
          <p className="text-gov-slate-700 text-lg leading-relaxed">
            This database tracks <strong>real-world AI incidents</strong> from the{' '}
            <a href="https://incidentdatabase.ai" target="_blank" rel="noopener noreferrer" className="text-gov-navy-700 underline">
              AI Incident Database
            </a>. Incidents are linked to FedRAMP products and federal AI use cases to help identify potential risks and patterns.
          </p>
        </div>

        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Incident Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-status-error">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.totalIncidents}</div>
              <div className="text-sm text-gov-slate-600">Total Incidents</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-indigo">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.llmIncidents}</div>
              <div className="text-sm text-gov-slate-600">LLM/Chatbot</div>
              <div className="text-xs text-gov-slate-500 mt-1">
                {((stats.llmIncidents / stats.totalIncidents) * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-warning">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.dataLeakIncidents}</div>
              <div className="text-sm text-gov-slate-600">Data Leaks</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-800">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.cyberAttackIncidents}</div>
              <div className="text-sm text-gov-slate-600">Cyber Attacks</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-slate-400">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.totalEntities}</div>
              <div className="text-sm text-gov-slate-600">Entities</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.productsLinked}</div>
              <div className="text-sm text-gov-slate-600">Products Linked</div>
            </div>

            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-teal">
              <div className="text-3xl font-bold text-gov-navy-900">{stats.useCasesLinked}</div>
              <div className="text-sm text-gov-slate-600">Use Cases Linked</div>
            </div>
          </div>
        </div>

        {/* Timeline by Year */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Incidents by Year</h2>
          <div className="flex flex-wrap gap-3">
            {yearStats.slice(0, 15).map((item) => (
              <div
                key={item.year}
                className="flex items-center gap-2 px-4 py-2 bg-gov-slate-50 rounded-lg border border-gov-slate-200"
              >
                <span className="font-semibold text-gov-navy-900">{item.year}</span>
                <span className="px-2 py-0.5 bg-status-error-light text-status-error-dark rounded text-sm font-medium">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Entities */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Top Involved Entities</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {topEntities.map((entity) => (
              <div
                key={entity.entityId}
                className="flex items-center justify-between p-3 bg-gov-slate-50 rounded-lg border border-gov-slate-200"
              >
                <span className="font-medium text-gov-navy-900 truncate">{entity.name}</span>
                <span className="ml-2 px-2 py-0.5 bg-gov-navy-100 text-gov-navy-800 rounded text-sm font-semibold">
                  {entity.incidentCount}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-status-error-light border border-status-error rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-status-error-dark mb-4">Related Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/use-cases"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-ai-teal-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ai-teal-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">Federal AI Use Cases</div>
                <div className="text-xs text-gov-slate-600">See linked use cases</div>
              </div>
            </Link>

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
                <div className="text-xs text-gov-slate-600">Authorized products</div>
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

        {/* Incidents Table */}
        <IncidentTable incidents={incidents} years={years} />
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source:{' '}
            <a href="https://incidentdatabase.ai" target="_blank" rel="noopener noreferrer" className="underline">
              AI Incident Database
            </a>
          </p>
          <p className="mt-2 text-gov-slate-400">
            Cross-referenced with FedRAMP products and federal AI use cases
          </p>
        </div>
      </footer>
    </div>
  );
}

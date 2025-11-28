import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getAgencyBySlug, getAgencyMatches } from '@/lib/agency-db';
import Breadcrumbs from '@/components/Breadcrumbs';

export default async function AgencyDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const agency = await getAgencyBySlug(slug);

  if (!agency) {
    notFound();
  }

  const matches = await getAgencyMatches(agency.id);

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-gov-navy-900 text-white py-6 border-b-4 border-gov-navy-700">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Agency AI Usage', href: '/agency-ai-usage' },
              { label: agency.agency_name, href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold">{agency.agency_name}</h1>
          <p className="text-gov-navy-100 mt-1">Internal AI Adoption Details</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Overview Card */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gov-navy-900 mb-4">AI Adoption Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">Staff LLM Chatbot</h3>
              {agency.has_staff_llm?.includes('Yes') ? (
                <div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-success-light text-status-success-dark border border-status-success">
                    {agency.has_staff_llm}
                  </span>
                  {agency.llm_name && (
                    <p className="text-gov-navy-900 mt-2">Tool: <span className="font-semibold">{agency.llm_name}</span></p>
                  )}
                </div>
              ) : (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300">
                  {agency.has_staff_llm || 'No public announcement'}
                </span>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">AI Coding Assistant</h3>
              {agency.has_coding_assistant?.includes('Yes') || agency.has_coding_assistant?.includes('Allowed') ? (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
                  {agency.has_coding_assistant}
                </span>
              ) : (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300">
                  {agency.has_coding_assistant || 'No public announcement'}
                </span>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">Deployment Scope</h3>
              <p className="text-gov-navy-900">{agency.scope || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">Solution Type</h3>
              <p className="text-gov-navy-900">{agency.solution_type || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">Non-Public Data Allowed</h3>
              <p className="text-gov-navy-900">{agency.non_public_allowed || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gov-slate-600 mb-2">Other AI Present</h3>
              <p className="text-gov-navy-900">{agency.other_ai_present || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Implementation Notes */}
        {agency.notes && (
          <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
            <h2 className="text-2xl font-semibold text-gov-navy-900 mb-4">Implementation Details</h2>
            <p className="text-gov-slate-700 leading-relaxed">{agency.notes}</p>
          </div>
        )}

        {/* FedRAMP Service Matches */}
        {matches.length > 0 && (
          <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
            <h2 className="text-2xl font-semibold text-gov-navy-900 mb-4">
              Related FedRAMP Services ({matches.length})
            </h2>
            <p className="text-gov-slate-600 mb-4">
              Based on the agency's solution type, these FedRAMP-authorized services likely support their AI deployment:
            </p>
            <div className="space-y-3">
              {matches.map((match, index) => (
                <Link
                  key={index}
                  href={`/product/${match.product_id}`}
                  className="block p-4 bg-gov-slate-50 rounded-md border border-gov-slate-200 hover:bg-gov-slate-100 hover:border-gov-navy-600 transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-semibold text-gov-navy-900">{match.provider_name}</span>
                        <span className="text-gov-slate-400">—</span>
                        <span className="text-gov-navy-900">{match.product_name}</span>
                      </div>
                      <p className="text-sm text-gov-slate-600">{match.match_reason}</p>
                    </div>
                    <div className="ml-4">
                      {match.confidence === 'high' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
                          High Confidence
                        </span>
                      )}
                      {match.confidence === 'medium' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-warning-light text-status-warning-dark border border-status-warning">
                          Medium Confidence
                        </span>
                      )}
                      {match.confidence === 'low' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300">
                          Low Confidence
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Sources */}
        {agency.sources && (
          <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
            <h2 className="text-2xl font-semibold text-gov-navy-900 mb-4">Sources & References</h2>
            <div className="space-y-2">
              {agency.sources.split(';').map((source, index) => {
                const trimmedSource = source.trim();
                if (!trimmedSource) return null;

                return (
                  <div key={index}>
                    <a
                      href={trimmedSource}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gov-navy-700 hover:text-gov-navy-900 underline break-all"
                    >
                      {trimmedSource}
                    </a>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-gov-slate-500 mt-4">
              Data compiled from public agency announcements, reports, and AI inventories
            </p>
          </div>
        )}
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source: Public agency announcements and reports
          </p>
          <p className="mt-2 text-gov-slate-400">
            Last updated: {new Date(agency.analyzed_at).toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

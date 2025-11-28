import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  getIncidentById,
  getIncidentEntities,
  getIncidentRelatedProducts,
  getIncidentRelatedUseCases,
  getIncidents,
} from '@/lib/incident-db';
import Breadcrumbs from '@/components/Breadcrumbs';
import CollapsibleRelatedItems from '@/components/CollapsibleRelatedItems';

export const dynamic = 'force-dynamic';

export async function generateStaticParams() {
  const incidents = await getIncidents();
  return incidents.slice(0, 100).map((incident) => ({
    id: incident.incidentId.toString(),
  }));
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function IncidentDetailPage({ params }: PageProps) {
  const { id } = await params;
  const incidentId = parseInt(id, 10);

  if (isNaN(incidentId)) {
    notFound();
  }

  const incident = await getIncidentById(incidentId);

  if (!incident) {
    notFound();
  }

  const entities = await getIncidentEntities(incidentId);

  // Get related products and use cases using hybrid matching (semantic + text)
  const relatedProducts = await getIncidentRelatedProducts(incidentId, 10);
  const relatedUseCases = await getIncidentRelatedUseCases(incidentId, 10);

  // Group entities by role
  const developers = entities.filter(e => e.role === 'developer');
  const deployers = entities.filter(e => e.role === 'deployer');
  const harmed = entities.filter(e => e.role === 'harmed');

  // Security badges
  const getSecurityBadges = () => {
    const badges = [];
    const security = incident.security;

    if (security?.llmOrChatbotInvolved) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
          LLM/Chatbot
        </span>
      );
    }

    if (security?.securityDataLeakPresence === 'confirmed') {
      badges.push(
        <span key="leak" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-error-light text-status-error-dark border border-status-error">
          Data Leak (Confirmed)
        </span>
      );
    } else if (security?.securityDataLeakPresence === 'suspected') {
      badges.push(
        <span key="leak-susp" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-warning-light text-status-warning-dark border border-status-warning">
          Data Leak (Suspected)
        </span>
      );
    }

    if (security?.cyberAttackFlag === 'confirmed_attack') {
      badges.push(
        <span key="attack" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gov-navy-100 text-gov-navy-800 border border-gov-navy-600">
          Cyber Attack (Confirmed)
        </span>
      );
    } else if (security?.cyberAttackFlag === 'suspected_attack') {
      badges.push(
        <span key="attack-susp" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gov-slate-100 text-gov-slate-700 border border-gov-slate-400">
          Cyber Attack (Suspected)
        </span>
      );
    }

    if (security?.regulatedContextFlag) {
      badges.push(
        <span key="regulated" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-info-light text-status-info-dark border border-status-info">
          Regulated Context
        </span>
      );
    }

    return badges;
  };

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-status-error-dark text-white py-6 border-b-4 border-red-900">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Incidents', href: '/incidents' },
              { label: `Incident ${incidentId}`, href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold mb-3">{incident.title}</h1>
          <div className="flex flex-wrap gap-2 mb-3">
            {getSecurityBadges()}
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className="font-semibold">{incident.date || 'Date unknown'}</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{incident.reportCount || 0} reports</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
              <span>ID: {incidentId}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {incident.description && (
              <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
                <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Description</h2>
                <p className="text-gov-slate-700 leading-relaxed whitespace-pre-wrap">
                  {incident.description}
                </p>
              </div>
            )}

            {/* Entities Involved */}
            <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
              <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Entities Involved</h2>
              <div className="space-y-4">
                {developers.length > 0 && (
                  <div>
                    <div className="text-sm font-semibold text-gov-slate-600 mb-2">DEVELOPERS</div>
                    <div className="flex flex-wrap gap-2">
                      {developers.map((entity, index) => (
                        <span
                          key={`developer-${entity.entityId}-${index}`}
                          className="inline-flex items-center px-3 py-1.5 bg-ai-blue-light text-ai-blue-dark rounded-md text-sm font-medium"
                        >
                          {entity.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {deployers.length > 0 && (
                  <div>
                    <div className="text-sm font-semibold text-gov-slate-600 mb-2">DEPLOYERS</div>
                    <div className="flex flex-wrap gap-2">
                      {deployers.map((entity, index) => (
                        <span
                          key={`deployer-${entity.entityId}-${index}`}
                          className="inline-flex items-center px-3 py-1.5 bg-ai-teal-light text-ai-teal-dark rounded-md text-sm font-medium"
                        >
                          {entity.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {harmed.length > 0 && (
                  <div>
                    <div className="text-sm font-semibold text-gov-slate-600 mb-2">HARMED PARTIES</div>
                    <div className="flex flex-wrap gap-2">
                      {harmed.map((entity, index) => (
                        <span
                          key={`harmed-${entity.entityId}-${index}`}
                          className="inline-flex items-center px-3 py-1.5 bg-status-error-light text-status-error-dark rounded-md text-sm font-medium"
                        >
                          {entity.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {entities.length === 0 && (
                  <p className="text-gov-slate-500">No entities documented for this incident.</p>
                )}
              </div>
            </div>

            {/* Security Details */}
            {incident.security && (
              <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
                <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Security Analysis</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {incident.security.securityEnvironmentType && (
                    <div>
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">Environment Type</div>
                      <div className="text-gov-slate-700">{incident.security.securityEnvironmentType}</div>
                    </div>
                  )}

                  {incident.security.deploymentStatus && (
                    <div>
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">Deployment Status</div>
                      <div className="text-gov-slate-700">{incident.security.deploymentStatus}</div>
                    </div>
                  )}

                  {incident.security.userBaseSizeBucket && (
                    <div>
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">User Base</div>
                      <div className="text-gov-slate-700">{incident.security.userBaseSizeBucket}</div>
                    </div>
                  )}

                  {incident.security.recordsExposedBucket && (
                    <div>
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">Records Exposed</div>
                      <div className="text-gov-slate-700">{incident.security.recordsExposedBucket}</div>
                    </div>
                  )}

                  {(incident.security.securityDataTypes as string[])?.length > 0 && (
                    <div className="md:col-span-2">
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">Data Types Involved</div>
                      <div className="flex flex-wrap gap-2">
                        {(incident.security.securityDataTypes as string[]).map((type, idx) => (
                          <span key={idx} className="px-2 py-1 bg-gov-slate-100 text-gov-slate-700 rounded text-sm">
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {(incident.security.downstreamConsequences as string[])?.length > 0 && (
                    <div className="md:col-span-2">
                      <div className="text-sm font-semibold text-gov-slate-600 mb-1">Downstream Consequences</div>
                      <div className="flex flex-wrap gap-2">
                        {(incident.security.downstreamConsequences as string[]).map((consequence, idx) => (
                          <span key={idx} className="px-2 py-1 bg-status-error-light text-status-error-dark rounded text-sm">
                            {consequence}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Relationships */}
          <div className="space-y-6">
            {/* Related FedRAMP Products */}
            <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
              <h3 className="text-lg font-semibold text-gov-navy-900 mb-3">
                Related FedRAMP Products
                <span className="ml-2 text-sm font-normal text-gov-slate-500">
                  ({relatedProducts.length})
                </span>
              </h3>
              <CollapsibleRelatedItems
                items={relatedProducts}
                type="product"
                emptyMessage="No related FedRAMP products found."
              />
            </div>

            {/* Related Use Cases */}
            <div className="bg-white rounded-lg border border-gov-slate-200 p-6">
              <h3 className="text-lg font-semibold text-gov-navy-900 mb-3">
                Related Federal AI Use Cases
                <span className="ml-2 text-sm font-normal text-gov-slate-500">
                  ({relatedUseCases.length})
                </span>
              </h3>
              <CollapsibleRelatedItems
                items={relatedUseCases}
                type="useCase"
                emptyMessage="No related federal AI use cases found."
              />
            </div>

            {/* External Link */}
            <div className="bg-status-error-light rounded-lg border border-status-error p-6">
              <h3 className="text-sm font-semibold text-status-error-dark mb-3">EXTERNAL RESOURCES</h3>
              <a
                href={`https://incidentdatabase.ai/cite/${incidentId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-status-error-dark hover:underline"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                View on AI Incident Database
              </a>
            </div>

            {/* Quick Links */}
            <div className="bg-gov-navy-50 rounded-lg border border-gov-navy-200 p-6">
              <h3 className="text-sm font-semibold text-gov-navy-900 mb-3">QUICK LINKS</h3>
              <div className="space-y-2">
                <Link
                  href="/incidents"
                  className="block text-sm text-gov-navy-700 hover:text-gov-navy-900 hover:underline"
                >
                  ← Back to All Incidents
                </Link>
                <Link
                  href="/use-cases"
                  className="block text-sm text-gov-navy-700 hover:text-gov-navy-900 hover:underline"
                >
                  View Federal AI Use Cases
                </Link>
                <Link
                  href="/ai-services"
                  className="block text-sm text-gov-navy-700 hover:text-gov-navy-900 hover:underline"
                >
                  View FedRAMP AI Services
                </Link>
                <Link
                  href="/"
                  className="block text-sm text-gov-navy-700 hover:text-gov-navy-900 hover:underline"
                >
                  Dashboard Home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source:{' '}
            <a href="https://incidentdatabase.ai" target="_blank" rel="noopener noreferrer" className="underline">
              AI Incident Database
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

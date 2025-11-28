import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getUseCaseBySlug, getUseCases, getUseCaseFedRAMPMatches } from '@/lib/use-case-db';
import { getUseCaseRelatedIncidents } from '@/lib/incident-db';
import Breadcrumbs from '@/components/Breadcrumbs';

export const dynamic = 'force-dynamic';

export async function generateStaticParams() {
  // Generate static params for all use cases
  const useCases = await getUseCases();
  return useCases.map((uc) => ({
    slug: uc.slug,
  }));
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function UseCaseDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const useCase = await getUseCaseBySlug(slug);

  if (!useCase) {
    notFound();
  }

  // Get related use cases from same agency
  const relatedCases = (await getUseCases({ agency: useCase.agency }))
    .filter(uc => uc.id !== useCase.id)
    .slice(0, 5);

  // Get FedRAMP matches (if any)
  const fedRAMPMatches = await getUseCaseFedRAMPMatches(useCase.id);

  // Get related AI incidents using hybrid matching
  const relatedIncidents = await getUseCaseRelatedIncidents(useCase.id, 10);

  // Parse providers (Drizzle auto-parses jsonb fields)
  const providers: string[] = useCase.providersDetected || [];

  // Get AI type badges
  const getAITypeBadges = () => {
    const badges = [];

    if (useCase.genaiFlag) {
      badges.push(
        <span key="genai" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
          GenAI
        </span>
      );
    }
    if (useCase.hasLlm) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
          LLM
        </span>
      );
    }
    if (useCase.hasChatbot) {
      badges.push(
        <span key="chatbot" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
          Chatbot
        </span>
      );
    }
    if (useCase.generalPurposeChatbot) {
      badges.push(
        <span key="gp-chat" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
          General Purpose Chatbot
        </span>
      );
    }
    if (useCase.domainChatbot) {
      badges.push(
        <span key="domain-chat" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
          Domain-Specific Chatbot
        </span>
      );
    }
    if (useCase.hasClassicMl) {
      badges.push(
        <span key="ml" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-charcoal-200 text-charcoal-700 border border-charcoal-400">
          Classic ML
        </span>
      );
    }
    if (useCase.hasCodingAssistant || useCase.hasCodingAgent) {
      badges.push(
        <span key="coding" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-success-light text-status-success-dark border border-status-success">
          Coding Assistant
        </span>
      );
    }
    if (useCase.hasRpa) {
      badges.push(
        <span key="rpa" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-warning-light text-status-warning-dark border border-status-warning">
          RPA
        </span>
      );
    }

    return badges.length > 0 ? badges : [
      <span key="other" className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-charcoal-100 text-charcoal-600 border border-charcoal-300">
        Other AI
      </span>
    ];
  };

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Use Cases', href: '/use-cases' },
              { label: useCase.useCaseName, href: undefined },
            ]}
          />
          <h1 className="font-serif text-3xl font-medium text-white mb-3">{useCase.useCaseName}</h1>
          <div className="flex flex-wrap gap-2 mb-3">
            {getAITypeBadges()}
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span className="font-semibold">{useCase.agency}</span>
              {useCase.agencyAbbreviation && (
                <span className="text-charcoal-300">({useCase.agencyAbbreviation})</span>
              )}
            </div>
            {useCase.bureau && (
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>{useCase.bureau}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overview */}
            <div className="bg-white rounded-lg border border-charcoal-200 p-6">
              <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Overview</h2>
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-semibold text-charcoal-500 mb-1">CLASSIFICATION</div>
                  <div className="flex flex-wrap gap-3">
                    {useCase.domainCategory && (
                      <div className="text-sm">
                        <span className="font-medium">Domain:</span>{' '}
                        <span className="px-2 py-1 bg-charcoal-100 text-charcoal-700 rounded">{useCase.domainCategory}</span>
                      </div>
                    )}
                    {useCase.useCaseTopicArea && (
                      <div className="text-sm">
                        <span className="font-medium">Topic:</span>{' '}
                        <span className="px-2 py-1 bg-charcoal-100 text-charcoal-600 rounded">{useCase.useCaseTopicArea}</span>
                      </div>
                    )}
                    {useCase.stageOfDevelopment && (
                      <div className="text-sm">
                        <span className="font-medium">Stage:</span>{' '}
                        <span className="px-2 py-1 bg-status-info-light text-status-info-dark rounded">{useCase.stageOfDevelopment}</span>
                      </div>
                    )}
                  </div>
                </div>

                {useCase.isRightsSafetyImpacting && (
                  <div>
                    <div className="text-sm font-semibold text-charcoal-500 mb-1">IMPACT CLASSIFICATION</div>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      useCase.isRightsSafetyImpacting.includes('Rights') || useCase.isRightsSafetyImpacting.includes('Both')
                        ? 'bg-status-error-light text-status-error-dark border border-status-error'
                        : 'bg-charcoal-100 text-charcoal-700 border border-charcoal-300'
                    }`}>
                      {useCase.isRightsSafetyImpacting}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Purpose & Benefits */}
            {useCase.intendedPurpose && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Purpose & Expected Benefits</h2>
                <p className="text-charcoal-600 leading-relaxed whitespace-pre-wrap">{useCase.intendedPurpose}</p>
              </div>
            )}

            {/* Outputs */}
            {useCase.outputs && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">AI System Outputs</h2>
                <p className="text-charcoal-600 leading-relaxed whitespace-pre-wrap">{useCase.outputs}</p>
              </div>
            )}

            {/* Technical Details */}
            {useCase.details && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Technical Details</h2>
                <div className="space-y-4">
                  {useCase.details.developmentApproach && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Development Approach</div>
                      <div className="text-charcoal-600">{useCase.details.developmentApproach}</div>
                    </div>
                  )}

                  {useCase.details.hasCustomCode && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Custom Code</div>
                      <div className="text-charcoal-600">{useCase.details.hasCustomCode}</div>
                    </div>
                  )}

                  {useCase.details.hasAto && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Authority to Operate (ATO)</div>
                      <div className="text-charcoal-600">{useCase.details.hasAto}</div>
                      {useCase.details.systemName && (
                        <div className="text-sm text-charcoal-500 mt-1">System: {useCase.details.systemName}</div>
                      )}
                    </div>
                  )}

                  {useCase.details.codeLink && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Open Source Code</div>
                      <a
                        href={useCase.details.codeLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-ifp-purple hover:text-ifp-purple-dark underline"
                      >
                        {useCase.details.codeLink}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Timeline */}
            {(useCase.dateInitiated || useCase.dateImplemented || useCase.dateRetired) && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Timeline</h2>
                <div className="space-y-3">
                  {useCase.dateInitiated && (
                    <div className="flex items-center gap-3">
                      <div className="w-24 text-sm font-semibold text-charcoal-500">Initiated</div>
                      <div className="text-charcoal-600">{useCase.dateInitiated}</div>
                    </div>
                  )}
                  {useCase.dateImplemented && (
                    <div className="flex items-center gap-3">
                      <div className="w-24 text-sm font-semibold text-charcoal-500">Implemented</div>
                      <div className="text-charcoal-600">{useCase.dateImplemented}</div>
                    </div>
                  )}
                  {useCase.dateRetired && (
                    <div className="flex items-center gap-3">
                      <div className="w-24 text-sm font-semibold text-charcoal-500">Retired</div>
                      <div className="text-charcoal-600">{useCase.dateRetired}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Privacy & Compliance */}
            {useCase.details && (useCase.details.involvesPii || useCase.details.privacyAssessed || useCase.details.impactAssessment) && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">Privacy & Compliance</h2>
                <div className="space-y-3">
                  {useCase.details.involvesPii && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Involves PII</div>
                      <div className="text-charcoal-600">{useCase.details.involvesPii}</div>
                    </div>
                  )}
                  {useCase.details.privacyAssessed && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">Privacy Assessment</div>
                      <div className="text-charcoal-600">{useCase.details.privacyAssessed}</div>
                    </div>
                  )}
                  {useCase.details.impactAssessment && (
                    <div>
                      <div className="text-sm font-semibold text-charcoal-500 mb-1">AI Impact Assessment</div>
                      <div className="text-charcoal-600">{useCase.details.impactAssessment}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Related AI Incidents */}
            {relatedIncidents.length > 0 && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h2 className="font-serif text-xl font-medium text-charcoal mb-4">
                  Related AI Incidents ({relatedIncidents.length})
                </h2>
                <p className="text-charcoal-500 mb-4 text-sm">
                  AI incidents that may be relevant to this use case based on semantic similarity and entity matching.
                </p>
                <div className="space-y-3">
                  {relatedIncidents.map((incident) => (
                    <Link
                      key={incident.incidentId}
                      href={`/incidents/${incident.incidentId}`}
                      className="block p-4 bg-cream hover:bg-cream-200 rounded-lg border border-charcoal-200 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-charcoal text-sm line-clamp-2">
                            {incident.title}
                          </h3>
                          {incident.date && (
                            <p className="text-xs text-charcoal-400 mt-1">{incident.date}</p>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-1 flex-shrink-0">
                          {/* Match quality indicator */}
                          <span
                            className={`text-xs font-medium px-2 py-0.5 rounded ${
                              incident.similarityScore >= 0.8
                                ? 'bg-status-success-light text-status-success-dark border border-status-success'
                                : incident.similarityScore >= 0.7
                                ? 'bg-status-warning-light text-status-warning-dark border border-status-warning'
                                : 'bg-charcoal-100 text-charcoal-600 border border-charcoal-300'
                            }`}
                          >
                            {Math.round(incident.similarityScore * 100)}% match
                          </span>
                          {/* Risk indicators */}
                          <div className="flex gap-1">
                            {incident.hasDataLeak && (
                              <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded" title="Data Leak">
                                Leak
                              </span>
                            )}
                            {incident.hasCyberAttack && (
                              <span className="text-xs px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded" title="Cyber Attack">
                                Attack
                              </span>
                            )}
                            {incident.hasLlm && (
                              <span className="text-xs px-1.5 py-0.5 bg-ifp-purple-light text-ifp-purple-dark rounded" title="LLM/Chatbot">
                                LLM
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Providers */}
            {providers.length > 0 && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h3 className="font-serif text-lg font-medium text-charcoal mb-3">Providers Mentioned</h3>
                <div className="flex flex-wrap gap-2">
                  {providers.map((provider) => (
                    <Link
                      key={provider}
                      href={`/ai-services?provider=${encodeURIComponent(provider)}`}
                      className="inline-flex items-center px-3 py-1.5 bg-cream hover:bg-cream-200 text-charcoal text-sm rounded-md border border-charcoal-200 transition-colors"
                    >
                      {provider}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* FedRAMP Matches */}
            {fedRAMPMatches.length > 0 && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h3 className="font-serif text-lg font-medium text-charcoal mb-3">Linked FedRAMP Services</h3>
                <div className="space-y-2">
                  {fedRAMPMatches.map((match, idx) => (
                    <Link
                      key={idx}
                      href={`/product/${match.productId}`}
                      className="block p-3 bg-cream hover:bg-cream-200 rounded-md border border-charcoal-200 transition-colors"
                    >
                      <div className="font-medium text-charcoal text-sm">{match.productName}</div>
                      <div className="text-xs text-charcoal-500 mt-1">{match.providerName}</div>
                      <div className="text-xs text-charcoal-400 mt-1">
                        Confidence: <span className={`font-semibold ${
                          match.confidence === 'high' ? 'text-status-success-dark' :
                          match.confidence === 'medium' ? 'text-status-warning-dark' :
                          'text-charcoal-600'
                        }`}>{match.confidence}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Related Use Cases */}
            {relatedCases.length > 0 && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-6">
                <h3 className="font-serif text-lg font-medium text-charcoal mb-3">Other Use Cases from {useCase.agencyAbbreviation || useCase.agency}</h3>
                <div className="space-y-2">
                  {relatedCases.map((related) => (
                    <Link
                      key={related.id}
                      href={`/use-cases/${related.slug}`}
                      className="block p-3 bg-cream hover:bg-cream-200 rounded-md border border-charcoal-200 transition-colors"
                    >
                      <div className="font-medium text-charcoal text-sm line-clamp-2">{related.useCaseName}</div>
                      {related.domainCategory && (
                        <div className="text-xs text-charcoal-500 mt-1">{related.domainCategory}</div>
                      )}
                    </Link>
                  ))}
                </div>
                <Link
                  href={`/use-cases?agency=${encodeURIComponent(useCase.agency)}`}
                  className="block mt-3 text-sm text-ifp-purple hover:text-ifp-purple-dark font-medium"
                >
                  View all from this agency →
                </Link>
              </div>
            )}

            {/* Quick Links */}
            <div className="bg-cream-200 rounded-lg border border-charcoal-200 p-6">
              <h3 className="text-sm font-semibold text-charcoal mb-3">QUICK LINKS</h3>
              <div className="space-y-2">
                <Link
                  href="/use-cases"
                  className="block text-sm text-ifp-purple hover:text-ifp-purple-dark hover:underline"
                >
                  ← Back to All Use Cases
                </Link>
                <Link
                  href={`/use-cases?domain=${encodeURIComponent(useCase.domainCategory || '')}`}
                  className="block text-sm text-ifp-purple hover:text-ifp-purple-dark hover:underline"
                >
                  View {useCase.domainCategory} Use Cases
                </Link>
                <Link
                  href="/ai-services"
                  className="block text-sm text-ifp-purple hover:text-ifp-purple-dark hover:underline"
                >
                  View FedRAMP AI Services
                </Link>
                <Link
                  href="/"
                  className="block text-sm text-ifp-purple hover:text-ifp-purple-dark hover:underline"
                >
                  Dashboard Home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-charcoal-900 text-cream py-6 mt-12 border-t-4 border-ifp-purple">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Federal AI Use Case Inventory • Last analyzed: {new Date(useCase.analyzedAt).toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

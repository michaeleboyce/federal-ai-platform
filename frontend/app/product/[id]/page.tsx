import Link from 'next/link';
import fs from 'fs';
import path from 'path';
import { notFound } from 'next/navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import { getProductRelatedIncidents, type SemanticIncidentMatch } from '@/lib/incident-db';

interface Product {
  id: string;
  name: string;
  csp: string;
  cso: string;
  service_offering: string;
  status: string;
  service_model: string[];
  deployment_model: string[];
  impact_level: string[];
  service_desc: string;
  all_others: string[];
  service_last_90: string[];
  independent_assessor: string;
  auth_date: string;
  annual_assessment: string;
  sales_email: string;
  security_email: string;
  website: string;
  uei: string;
  small_business: boolean;
  business_function: string[];
}

async function getProduct(id: string): Promise<Product | null> {
  const jsonPath = path.join(process.cwd(), '..', 'data', 'fedramp_products.json');
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  const products: Product[] = data.data.Products;

  return products.find((p) => p.id === id) || null;
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);

  if (!product) {
    notFound();
  }

  // Get related incidents using hybrid matching
  const relatedIncidents = await getProductRelatedIncidents(id, 10);

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Products', href: '/products' },
              { label: product.cso, href: undefined },
            ]}
          />
          <h1 className="font-serif text-3xl font-medium text-white">{product.cso}</h1>
          <p className="text-charcoal-300 mt-1">{product.csp}</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Overview Card */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
          <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">FedRAMP ID</h3>
              <p className="text-lg text-charcoal">{product.id}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Status</h3>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-status-success-light text-status-success-dark border border-status-success">
                {product.status || 'N/A'}
              </span>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Service Model</h3>
              <p className="text-lg text-charcoal">
                {Array.isArray(product.service_model)
                  ? product.service_model.join(', ')
                  : product.service_model || 'N/A'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Deployment Model</h3>
              <p className="text-lg text-charcoal">
                {Array.isArray(product.deployment_model)
                  ? product.deployment_model.join(', ')
                  : product.deployment_model || 'N/A'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Impact Level</h3>
              <p className="text-lg text-charcoal">
                {Array.isArray(product.impact_level)
                  ? product.impact_level.join(', ')
                  : product.impact_level || 'N/A'}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Independent Assessor</h3>
              <p className="text-lg text-charcoal">{product.independent_assessor || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Description */}
        {product.service_desc && (
          <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
            <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">Service Description</h2>
            <p className="text-charcoal-600 leading-relaxed">{product.service_desc}</p>
          </div>
        )}

        {/* All Services - This is the key section showing Amazon Bedrock etc. */}
        {product.all_others && product.all_others.length > 0 && (
          <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
            <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">
              Authorized Services ({product.all_others.length})
            </h2>
            <p className="text-charcoal-500 mb-4">
              All services included in this FedRAMP authorization:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {product.all_others.map((service, index) => (
                <div
                  key={index}
                  className="flex items-center space-x-2 px-3 py-2 bg-cream rounded-md hover:bg-cream-200 transition-colors border border-charcoal-200"
                >
                  <svg
                    className="w-4 h-4 text-charcoal-600 flex-shrink-0"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <span className="text-sm text-charcoal">{service.trim()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recently Added Services */}
        {product.service_last_90 && product.service_last_90.length > 0 && product.service_last_90[0] !== '' && (
          <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
            <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">
              Recently Added Services (Last 90 Days)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {product.service_last_90.map((service, index) => (
                <div
                  key={index}
                  className="flex items-center space-x-2 px-3 py-2 bg-status-success-light rounded-md border border-status-success"
                >
                  <svg
                    className="w-4 h-4 text-status-success-dark flex-shrink-0"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M12 4v16m8-8H4"></path>
                  </svg>
                  <span className="text-sm text-charcoal">{service.trim()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Contact Information */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
          <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">Contact Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {product.sales_email && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Sales Email</h3>
                <a
                  href={`mailto:${product.sales_email}`}
                  className="text-ifp-purple hover:text-ifp-purple-dark underline"
                >
                  {product.sales_email}
                </a>
              </div>
            )}
            {product.security_email && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Security Email</h3>
                <a
                  href={`mailto:${product.security_email}`}
                  className="text-ifp-purple hover:text-ifp-purple-dark underline"
                >
                  {product.security_email}
                </a>
              </div>
            )}
            {product.website && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Website</h3>
                <a
                  href={product.website.startsWith('http') ? product.website : `https://${product.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-ifp-purple hover:text-ifp-purple-dark underline"
                >
                  {product.website}
                </a>
              </div>
            )}
            {product.uei && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">UEI Number</h3>
                <p className="text-charcoal">{product.uei}</p>
              </div>
            )}
          </div>
        </div>

        {/* Related AI Incidents */}
        {relatedIncidents.length > 0 && (
          <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
            <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">
              Related AI Incidents ({relatedIncidents.length})
            </h2>
            <p className="text-charcoal-500 mb-4 text-sm">
              AI incidents that may be relevant to this service based on semantic similarity and entity matching.
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

        {/* Authorization Details */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6">
          <h2 className="font-serif text-2xl font-medium text-charcoal mb-4">Authorization Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {product.auth_date && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Authorization Date</h3>
                <p className="text-charcoal">{product.auth_date}</p>
              </div>
            )}
            {product.annual_assessment && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Annual Assessment</h3>
                <p className="text-charcoal">{product.annual_assessment}</p>
              </div>
            )}
            {product.small_business !== undefined && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Small Business</h3>
                <p className="text-charcoal">{product.small_business ? 'Yes' : 'No'}</p>
              </div>
            )}
            {product.business_function && product.business_function.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-charcoal-500 mb-2">Business Functions</h3>
                <p className="text-charcoal">
                  {Array.isArray(product.business_function)
                    ? product.business_function.join(', ')
                    : product.business_function}
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-charcoal-900 text-cream py-6 mt-12 border-t-4 border-ifp-purple">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source:{' '}
            <a
              href="https://marketplace.fedramp.gov/"
              className="text-charcoal-300 hover:text-cream underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              FedRAMP Marketplace
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

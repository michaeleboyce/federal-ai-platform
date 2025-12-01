import Link from 'next/link';
import { getAIStats } from '@/lib/ai-db';
import { getAgencyStats } from '@/lib/agency-db';
import { getUseCaseStats } from '@/lib/use-case-db';
import { getIncidentStats } from '@/lib/incident-db';
import { getHierarchyStats } from '@/lib/hierarchy-db';
import { getAllProductsWithServiceCounts } from '@/lib/db';

interface Product {
  id: string;
  csp: string;
  cso: string;
  status: string;
  all_others: string[];
  auth_date: string;
}

async function getProducts() {
  const dbProducts = await getAllProductsWithServiceCounts();
  return dbProducts.map(p => ({
    id: p.fedrampId,
    csp: p.cloudServiceProvider || '',
    cso: p.cloudServiceOffering || '',
    status: p.status || '',
    all_others: p.aiServices || [],
    auth_date: p.fedrampAuthorizationDate || '',
  })) as Product[];
}

export default async function Home() {
  const products = await getProducts();
  const aiStatsData = await getAIStats();
  const agencyStatsData = await getAgencyStats();
  const useCaseStatsData = await getUseCaseStats();
  const incidentStatsData = await getIncidentStats();
  const hierarchyStatsData = await getHierarchyStats();

  // Provide default values if stats are undefined
  const aiStats = aiStatsData || {
    total_ai_services: 0,
    count_ai: 0,
    count_genai: 0,
    count_llm: 0,
    products_with_ai: 0,
    providers_with_ai: 0
  };

  const agencyStats = agencyStatsData || {
    total_agencies: 0,
    agencies_with_llm: 0,
    agencies_with_coding: 0,
    agencies_custom_solution: 0,
    agencies_commercial_solution: 0,
    high_confidence_matches: 0
  };

  const useCaseStats = useCaseStatsData || {
    total_use_cases: 0,
    genai_count: 0,
    chatbot_count: 0,
    classic_ml_count: 0,
    unique_agencies: 0,
    total_agencies: 0
  };

  const incidentStats = incidentStatsData || {
    totalIncidents: 0,
    llmIncidents: 0,
    dataLeakIncidents: 0,
    cyberAttackIncidents: 0,
    totalEntities: 0,
    productsLinked: 0,
    useCasesLinked: 0
  };

  const hierarchyStats = hierarchyStatsData || {
    totalOrganizations: 0,
    cfoActAgencies: 0,
    cabinetDepartments: 0,
    independentAgencies: 0,
    subAgencies: 0,
    offices: 0,
    maxDepth: 0
  };

  // Calculate general stats
  const activeProducts = products.filter((p) => p.status === 'FedRAMP Authorized').length;
  const totalServices = products.reduce((acc, p) => acc + (p.all_others?.length || 0), 0);
  const uniqueProviders = new Set(products.map((p) => p.csp)).size;

  // Recent AI services (last 90 days)
  const ninetyDaysAgo = new Date();
  ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
  const recentAI = products.filter((p) => {
    const authDate = new Date(p.auth_date);
    return authDate > ninetyDaysAgo && p.all_others && p.all_others.length > 0;
  }).length;

  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-charcoal-800 py-10 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <h1 className="font-serif text-4xl md:text-5xl font-medium text-white mb-2">AI in Federal Government</h1>
          <p className="text-charcoal-300 text-lg">
            Tracking AI adoption across federal agencies and FedRAMP-authorized services
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Description */}
        <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-8">
          <p className="text-charcoal-600 text-lg leading-relaxed">
            This dashboard provides comprehensive insights into how AI is being deployed in the federal government—through
            <strong> FedRAMP-authorized cloud services</strong>, <strong>internal agency tools</strong>, and <strong>actual use case implementations</strong>.
            Explore {useCaseStats.total_use_cases.toLocaleString()} AI use cases, AI/ML services, generative AI tools, and see which agencies are leading AI adoption.
          </p>
        </div>

        {/* Main Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Card 1: FedRAMP AI Services */}
          <Link
            href="/ai-services"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">FedRAMP AI Services</h2>
              <svg className="w-6 h-6 text-ifp-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Total AI Services</span>
                <span className="text-3xl font-bold text-charcoal">{aiStats.total_ai_services}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
                  AI/ML: {aiStats.count_ai}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
                  GenAI: {aiStats.count_genai}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
                  LLM: {aiStats.count_llm}
                </span>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              {aiStats.products_with_ai} products from {aiStats.providers_with_ai} providers
            </p>
          </Link>

          {/* Card 2: Federal Agency AI Adoption */}
          <Link
            href="/agency-ai-usage"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">Agency AI Adoption</h2>
              <svg className="w-6 h-6 text-ifp-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Agencies Tracked</span>
                <span className="text-3xl font-bold text-charcoal">{agencyStats.total_agencies}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 bg-ifp-purple-light rounded">
                  <div className="text-xl font-bold text-ifp-purple-dark">{agencyStats.agencies_with_llm}</div>
                  <div className="text-xs text-charcoal-500">Staff LLMs</div>
                </div>
                <div className="text-center p-2 bg-ifp-orange-light rounded">
                  <div className="text-xl font-bold text-ifp-orange-dark">{agencyStats.agencies_with_coding}</div>
                  <div className="text-xs text-charcoal-500">Coding Tools</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              {agencyStats.high_confidence_matches} high-confidence FedRAMP matches
            </p>
          </Link>

          {/* Card 3: AI Use Cases */}
          <Link
            href="/use-cases"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">AI Use Cases</h2>
              <svg className="w-6 h-6 text-charcoal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Total Implementations</span>
                <span className="text-3xl font-bold text-charcoal">{useCaseStats.total_use_cases}</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-ifp-orange-light rounded">
                  <div className="text-xl font-bold text-ifp-orange-dark">{useCaseStats.genai_count}</div>
                  <div className="text-xs text-charcoal-500">GenAI</div>
                </div>
                <div className="text-center p-2 bg-ifp-purple-light rounded">
                  <div className="text-xl font-bold text-ifp-purple-dark">{useCaseStats.chatbot_count}</div>
                  <div className="text-xs text-charcoal-500">Chatbot</div>
                </div>
                <div className="text-center p-2 bg-charcoal-200 rounded">
                  <div className="text-xl font-bold text-charcoal-700">{useCaseStats.classic_ml_count}</div>
                  <div className="text-xs text-charcoal-500">Classic ML</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              Across {useCaseStats.total_agencies} federal agencies
            </p>
          </Link>

          {/* Card 4: AI Incidents */}
          <Link
            href="/incidents"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">AI Incidents</h2>
              <svg className="w-6 h-6 text-status-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Documented Incidents</span>
                <span className="text-3xl font-bold text-charcoal">{incidentStats.totalIncidents.toLocaleString()}</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-amber-50 rounded border border-amber-200">
                  <div className="text-xl font-bold text-amber-700">{incidentStats.llmIncidents}</div>
                  <div className="text-xs text-charcoal-500">LLM</div>
                </div>
                <div className="text-center p-2 bg-red-50 rounded border border-red-200">
                  <div className="text-xl font-bold text-red-700">{incidentStats.dataLeakIncidents}</div>
                  <div className="text-xs text-charcoal-500">Data Leak</div>
                </div>
                <div className="text-center p-2 bg-orange-50 rounded border border-orange-200">
                  <div className="text-xl font-bold text-orange-700">{incidentStats.cyberAttackIncidents}</div>
                  <div className="text-xs text-charcoal-500">Cyber</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              {incidentStats.productsLinked} linked products, {incidentStats.useCasesLinked} linked use cases
            </p>
          </Link>

          {/* Card 5: Products with AI */}
          <Link
            href="/ai-services"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">AI-Enabled Products</h2>
              <svg className="w-6 h-6 text-status-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">FedRAMP Products</span>
                <span className="text-3xl font-bold text-charcoal">{aiStats.products_with_ai}</span>
              </div>
              <div className="text-sm text-charcoal-500">
                From {aiStats.providers_with_ai} different cloud providers
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              Including AWS Bedrock, Azure OpenAI, Google Vertex AI, and more
            </p>
          </Link>

          {/* Card 6: Recent AI Authorizations */}
          <Link
            href="/ai-services?sort=auth_date&dir=desc"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">Recent Activity</h2>
              <svg className="w-6 h-6 text-ifp-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Last 90 Days</span>
                <span className="text-3xl font-bold text-charcoal">{recentAI}</span>
              </div>
              <div className="text-sm text-charcoal-500">
                New products and services authorized
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              View recently authorized AI services and updates
            </p>
          </Link>

          {/* Card 7: Agency Hierarchy */}
          <Link
            href="/agencies"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">Agency Hierarchy</h2>
              <svg className="w-6 h-6 text-ifp-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Organizations</span>
                <span className="text-3xl font-bold text-charcoal">{hierarchyStats.totalOrganizations}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 bg-ifp-purple-light rounded">
                  <div className="text-xl font-bold text-ifp-purple-dark">{hierarchyStats.cfoActAgencies}</div>
                  <div className="text-xs text-charcoal-500">CFO Act</div>
                </div>
                <div className="text-center p-2 bg-charcoal-200 rounded">
                  <div className="text-xl font-bold text-charcoal-700">{hierarchyStats.subAgencies}</div>
                  <div className="text-xs text-charcoal-500">Sub-agencies</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              Explore the federal government organizational structure
            </p>
          </Link>

          {/* Card 8: All FedRAMP Products */}
          <Link
            href="/products"
            className="bg-white border border-charcoal-200 rounded-lg p-6 hover:border-ifp-purple hover:shadow-md transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="font-serif text-2xl font-medium text-charcoal">All Products</h2>
              <svg className="w-6 h-6 text-charcoal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-charcoal-500">Total Products</span>
                <span className="text-3xl font-bold text-charcoal">{products.length}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-charcoal-500">Active: </span>
                  <span className="font-semibold">{activeProducts}</span>
                </div>
                <div>
                  <span className="text-charcoal-500">Providers: </span>
                  <span className="font-semibold">{uniqueProviders}</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-charcoal-500">
              Browse all {totalServices.toLocaleString()} FedRAMP-authorized services
            </p>
          </Link>
        </div>

        {/* Quick Links */}
        <div className="bg-charcoal-50 border border-charcoal-200 rounded-lg p-6">
          <h3 className="font-serif text-lg font-medium text-charcoal mb-4">Quick Navigation</h3>
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
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
                <div className="font-semibold text-charcoal">AI Services</div>
                <div className="text-xs text-charcoal-500">FedRAMP AI catalog</div>
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
                <div className="font-semibold text-charcoal">Agency Usage</div>
                <div className="text-xs text-charcoal-500">Internal AI adoption</div>
              </div>
            </Link>

            <Link
              href="/use-cases"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-charcoal-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-charcoal-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">Use Cases</div>
                <div className="text-xs text-charcoal-500">AI implementations</div>
              </div>
            </Link>

            <Link
              href="/incidents"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">Incidents</div>
                <div className="text-xs text-charcoal-500">AI incident database</div>
              </div>
            </Link>

            <Link
              href="/agencies"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-ifp-purple-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ifp-purple-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">Agencies</div>
                <div className="text-xs text-charcoal-500">Org hierarchy</div>
              </div>
            </Link>

            <Link
              href="/products"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-charcoal-200 hover:border-ifp-purple transition-colors"
            >
              <div className="w-10 h-10 bg-charcoal-200 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-charcoal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-charcoal">All Products</div>
                <div className="text-xs text-charcoal-500">Complete catalog</div>
              </div>
            </Link>
          </div>
        </div>
      </main>

      <footer className="bg-charcoal-900 text-cream py-8 mt-16 border-t-4 border-ifp-purple">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data sources:{' '}
            <a
              href="https://marketplace.fedramp.gov/"
              className="text-charcoal-300 hover:text-cream underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              FedRAMP Marketplace
            </a>
            {' '}• Public agency announcements and AI inventories
          </p>
          <p className="mt-2 text-charcoal-400">
            AI analysis powered by Anthropic Claude • Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

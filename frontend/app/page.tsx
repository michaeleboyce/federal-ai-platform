import fs from 'fs';
import path from 'path';
import Link from 'next/link';
import { getAIStats } from '@/lib/ai-db';
import { getAgencyStats } from '@/lib/agency-db';
import { getUseCaseStats } from '@/lib/use-case-db';

interface Product {
  id: string;
  csp: string;
  cso: string;
  status: string;
  all_others: string[];
  auth_date: string;
}

async function getProducts() {
  const jsonPath = path.join(process.cwd(), '..', 'data', 'fedramp_products.json');
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  return data.data.Products as Product[];
}

export default async function Home() {
  const products = await getProducts();
  const aiStats = getAIStats();
  const agencyStats = getAgencyStats();
  const useCaseStats = getUseCaseStats();

  // Calculate general stats
  const activeProducts = products.filter((p) => p.status === 'Active').length;
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
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-gov-navy-900 text-white py-8 border-b-4 border-gov-navy-700">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-2">AI in Federal Government</h1>
          <p className="text-gov-navy-100 text-lg">
            Tracking AI adoption across federal agencies and FedRAMP-authorized services
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Description */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-8">
          <p className="text-gov-slate-700 text-lg leading-relaxed">
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
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">FedRAMP AI Services</h2>
              <svg className="w-6 h-6 text-ai-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">Total AI Services</span>
                <span className="text-3xl font-bold text-gov-navy-900">{aiStats.total_ai_services}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
                  AI/ML: {aiStats.count_ai}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-teal-light text-ai-teal-dark border border-ai-teal">
                  GenAI: {aiStats.count_genai}
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
                  LLM: {aiStats.count_llm}
                </span>
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              {aiStats.products_with_ai} products from {aiStats.providers_with_ai} providers
            </p>
          </Link>

          {/* Card 2: Federal Agency AI Adoption */}
          <Link
            href="/agency-ai-usage"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">Agency AI Adoption</h2>
              <svg className="w-6 h-6 text-ai-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">Agencies Tracked</span>
                <span className="text-3xl font-bold text-gov-navy-900">{agencyStats.total_agencies}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 bg-ai-blue-light rounded">
                  <div className="text-xl font-bold text-ai-blue-dark">{agencyStats.agencies_with_llm}</div>
                  <div className="text-xs text-gov-slate-600">Staff LLMs</div>
                </div>
                <div className="text-center p-2 bg-ai-teal-light rounded">
                  <div className="text-xl font-bold text-ai-teal-dark">{agencyStats.agencies_with_coding}</div>
                  <div className="text-xs text-gov-slate-600">Coding Tools</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              {agencyStats.high_confidence_matches} high-confidence FedRAMP matches
            </p>
          </Link>

          {/* Card 3: AI Use Cases */}
          <Link
            href="/use-cases"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">AI Use Cases</h2>
              <svg className="w-6 h-6 text-ai-indigo" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">Total Implementations</span>
                <span className="text-3xl font-bold text-gov-navy-900">{useCaseStats.total_use_cases}</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-ai-teal-light rounded">
                  <div className="text-xl font-bold text-ai-teal-dark">{useCaseStats.genai_count}</div>
                  <div className="text-xs text-gov-slate-600">GenAI</div>
                </div>
                <div className="text-center p-2 bg-ai-blue-light rounded">
                  <div className="text-xl font-bold text-ai-blue-dark">{useCaseStats.chatbot_count}</div>
                  <div className="text-xs text-gov-slate-600">Chatbot</div>
                </div>
                <div className="text-center p-2 bg-gov-slate-200 rounded">
                  <div className="text-xl font-bold text-gov-slate-700">{useCaseStats.classic_ml_count}</div>
                  <div className="text-xs text-gov-slate-600">Classic ML</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              Across {useCaseStats.total_agencies} federal agencies
            </p>
          </Link>

          {/* Card 4: Products with AI */}
          <Link
            href="/ai-services"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">AI-Enabled Products</h2>
              <svg className="w-6 h-6 text-status-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">FedRAMP Products</span>
                <span className="text-3xl font-bold text-gov-navy-900">{aiStats.products_with_ai}</span>
              </div>
              <div className="text-sm text-gov-slate-600">
                From {aiStats.providers_with_ai} different cloud providers
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              Including AWS Bedrock, Azure OpenAI, Google Vertex AI, and more
            </p>
          </Link>

          {/* Card 4: Recent AI Authorizations */}
          <Link
            href="/ai-services?sort=auth_date&dir=desc"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">Recent Activity</h2>
              <svg className="w-6 h-6 text-status-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">Last 90 Days</span>
                <span className="text-3xl font-bold text-gov-navy-900">{recentAI}</span>
              </div>
              <div className="text-sm text-gov-slate-600">
                New products and services authorized
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              View recently authorized AI services and updates
            </p>
          </Link>

          {/* Card 5: Solution Types */}
          <Link
            href="/agency-ai-usage"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">Solution Approaches</h2>
              <svg className="w-6 h-6 text-ai-indigo" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center p-2 bg-ai-indigo-light rounded">
                  <div className="text-xl font-bold text-ai-indigo-dark">{agencyStats.agencies_custom_solution}</div>
                  <div className="text-xs text-gov-slate-600">Custom</div>
                </div>
                <div className="text-center p-2 bg-status-success-light rounded">
                  <div className="text-xl font-bold text-status-success-dark">{agencyStats.agencies_commercial_solution}</div>
                  <div className="text-xs text-gov-slate-600">Commercial</div>
                </div>
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              Mix of custom-built and commercial AI solutions
            </p>
          </Link>

          {/* Card 6: All FedRAMP Products */}
          <Link
            href="/products"
            className="bg-white border-2 border-gov-slate-200 rounded-lg p-6 hover:border-gov-navy-700 hover:shadow-lg transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gov-navy-900">All Products</h2>
              <svg className="w-6 h-6 text-gov-navy-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gov-slate-600">Total Products</span>
                <span className="text-3xl font-bold text-gov-navy-900">{products.length}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gov-slate-600">Active: </span>
                  <span className="font-semibold">{activeProducts}</span>
                </div>
                <div>
                  <span className="text-gov-slate-600">Providers: </span>
                  <span className="font-semibold">{uniqueProviders}</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-gov-slate-600">
              Browse all {totalServices.toLocaleString()} FedRAMP-authorized services
            </p>
          </Link>
        </div>

        {/* Quick Links */}
        <div className="bg-gov-navy-50 border border-gov-navy-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gov-navy-900 mb-4">Quick Navigation</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
                <div className="font-semibold text-gov-navy-900">AI Services</div>
                <div className="text-xs text-gov-slate-600">FedRAMP AI catalog</div>
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
                <div className="font-semibold text-gov-navy-900">Agency Usage</div>
                <div className="text-xs text-gov-slate-600">Internal AI adoption</div>
              </div>
            </Link>

            <Link
              href="/use-cases"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-ai-indigo-light rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-ai-indigo-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">Use Cases</div>
                <div className="text-xs text-gov-slate-600">AI implementations</div>
              </div>
            </Link>

            <Link
              href="/products"
              className="flex items-center space-x-3 p-3 bg-white rounded-md border border-gov-slate-200 hover:border-gov-navy-600 transition-colors"
            >
              <div className="w-10 h-10 bg-gov-slate-200 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-gov-navy-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold text-gov-navy-900">All Products</div>
                <div className="text-xs text-gov-slate-600">Complete catalog</div>
              </div>
            </Link>
          </div>
        </div>
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data sources:{' '}
            <a
              href="https://marketplace.fedramp.gov/"
              className="text-gov-navy-200 hover:text-white underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              FedRAMP Marketplace
            </a>
            {' '}• Public agency announcements and AI inventories
          </p>
          <p className="mt-2 text-gov-slate-400">
            AI analysis powered by Anthropic Claude • Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

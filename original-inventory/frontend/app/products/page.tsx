import Link from 'next/link';
import ProductTable from '@/components/ProductTable';
import Breadcrumbs from '@/components/Breadcrumbs';
import { getAllProducts, getStats } from '@/lib/db';

export const dynamic = 'force-dynamic';

interface Product {
  id: string;
  name: string;
  csp: string;
  cso: string;
  service_offering: string;
  status: string;
  service_model: string[];
  impact_level: string[];
  service_desc: string;
  all_others: string[];
  auth_date: string;
}

async function getProducts() {
  const dbProducts = await getAllProducts();
  // Transform to match expected format
  return dbProducts.map(p => ({
    id: p.fedrampId,
    name: p.cloudServiceOffering || '',
    csp: p.cloudServiceProvider || '',
    cso: p.cloudServiceOffering || '',
    service_offering: p.cloudServiceOffering || '',
    status: p.status || '',
    service_model: p.serviceModel ? [p.serviceModel] : [],
    impact_level: [],
    service_desc: p.serviceDescription || '',
    all_others: [],
    auth_date: p.fedrampAuthorizationDate || '',
  })) as Product[];
}

export default async function ProductsPage() {
  const products = await getProducts();

  // Calculate stats
  const activeProducts = products.filter((p) => p.status === 'Active').length;
  const totalServices = products.reduce((acc, p) => acc + (p.all_others?.length || 0), 0);
  const uniqueProviders = new Set(products.map((p) => p.csp)).size;

  return (
    <div className="min-h-screen bg-gov-slate-50">
      <header className="bg-gov-navy-900 text-white py-6 border-b-4 border-gov-navy-700">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Products', href: undefined },
            ]}
          />
          <h1 className="text-3xl font-bold">All FedRAMP Products</h1>
          <p className="text-gov-navy-100 mt-2">
            Browse, search, and filter all {products.length} FedRAMP authorized cloud services
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Statistics Dashboard */}
        <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gov-navy-900 mb-4">Quick Stats</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border-l-4 border-gov-navy-600">
              <div className="text-2xl font-bold text-gov-navy-900">{products.length}</div>
              <div className="text-sm text-gov-slate-600">Total Products</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-blue">
              <div className="text-2xl font-bold text-gov-navy-900">{uniqueProviders}</div>
              <div className="text-sm text-gov-slate-600">Providers</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-status-success">
              <div className="text-2xl font-bold text-gov-navy-900">{activeProducts}</div>
              <div className="text-sm text-gov-slate-600">Active</div>
            </div>
            <div className="bg-white p-4 rounded-lg border-l-4 border-ai-teal">
              <div className="text-2xl font-bold text-gov-navy-900">{totalServices.toLocaleString()}</div>
              <div className="text-sm text-gov-slate-600">Total Services</div>
            </div>
          </div>
        </div>

        {/* Search Tips */}
        <div className="bg-gov-navy-50 border border-gov-navy-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-gov-navy-900 mb-2">Search Tips</h3>
          <ul className="text-sm text-gov-slate-700 space-y-1">
            <li>• Search by provider name: <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Amazon</code>, <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Microsoft</code>, <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Google</code></li>
            <li>• Search by service name: <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Bedrock</code>, <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Lambda</code>, <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">S3</code></li>
            <li>• Search by offering: <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">GovCloud</code>, <code className="bg-gov-navy-100 px-2 py-0.5 rounded text-gov-navy-800 font-mono text-xs">Azure</code></li>
            <li>• Click column headers to sort by that field</li>
          </ul>
        </div>

        {/* Interactive Product Table */}
        <ProductTable products={products} />
      </main>

      <footer className="bg-gov-navy-950 text-white py-6 mt-12 border-t-4 border-gov-navy-700">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>
            Data source:{' '}
            <a
              href="https://marketplace.fedramp.gov/"
              className="text-gov-navy-200 hover:text-white underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              FedRAMP Marketplace
            </a>
          </p>
          <p className="mt-2 text-gov-slate-400">
            Official JSON API provided by GSA • Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}

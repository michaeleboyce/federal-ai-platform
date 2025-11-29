import Link from 'next/link';
import { Landmark, Building2, Building, ChevronRight, ExternalLink } from 'lucide-react';
import { getFullHierarchy, getHierarchyStats, getCfoActAgencies } from '@/lib/hierarchy-db';
import { AgencyHierarchyTree } from '@/components/hierarchy/AgencyHierarchyTree';
import Breadcrumbs from '@/components/Breadcrumbs';

export const metadata = {
  title: 'Federal Agency Hierarchy | Federal AI Platform',
  description: 'Explore the organizational hierarchy of federal agencies, including CFO Act agencies, cabinet departments, and their sub-agencies.',
};

export default async function AgenciesPage() {
  const [hierarchy, stats, cfoAgencies] = await Promise.all([
    getFullHierarchy(),
    getHierarchyStats(),
    getCfoActAgencies(),
  ]);

  // Separate cabinet departments and independent agencies
  const cabinetDepartments = cfoAgencies.filter((a) => a.isCabinetDepartment);
  const independentAgencies = cfoAgencies.filter((a) => !a.isCabinetDepartment);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Breadcrumbs
            items={[
              { label: 'Federal AI Platform', href: '/' },
              { label: 'Federal Agencies' },
            ]}
          />
          <div className="mt-4">
            <h1 className="text-2xl font-bold text-slate-900">
              Federal Agency Hierarchy
            </h1>
            <p className="mt-2 text-slate-600">
              Explore the organizational structure of the U.S. federal government, including the 24 CFO Act agencies
              and their sub-agencies.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-slate-900">{stats.totalOrganizations}</div>
            <div className="text-sm text-slate-500">Total Organizations</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-ai-indigo">{stats.cfoActAgencies}</div>
            <div className="text-sm text-slate-500">CFO Act Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-ai-blue">{stats.cabinetDepartments}</div>
            <div className="text-sm text-slate-500">Cabinet Departments</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-emerald-600">{stats.independentAgencies}</div>
            <div className="text-sm text-slate-500">Independent Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-slate-700">{stats.subAgencies}</div>
            <div className="text-sm text-slate-500">Sub-Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-2xl font-bold text-slate-500">{stats.maxDepth + 1}</div>
            <div className="text-sm text-slate-500">Hierarchy Levels</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Quick Links */}
          <div className="lg:col-span-1 space-y-6">
            {/* CFO Act Agencies */}
            <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
                <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Landmark className="w-4 h-4 text-ai-indigo" />
                  CFO Act Agencies
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  24 major agencies subject to the Chief Financial Officers Act of 1990
                </p>
              </div>

              {/* Cabinet Departments */}
              <div className="px-4 py-3 border-b border-slate-100">
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                  Cabinet Departments ({cabinetDepartments.length})
                </h3>
                <div className="space-y-1">
                  {cabinetDepartments.map((dept) => (
                    <Link
                      key={dept.id}
                      href={`/agencies/${dept.slug}`}
                      className="flex items-center justify-between py-1 px-2 -mx-2 rounded hover:bg-slate-50 group"
                    >
                      <span className="text-sm">
                        <span className="font-medium text-slate-900">{dept.abbreviation}</span>
                        <span className="text-slate-400 mx-1.5">-</span>
                        <span className="text-slate-600">{dept.name}</span>
                      </span>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
                    </Link>
                  ))}
                </div>
              </div>

              {/* Independent Agencies */}
              <div className="px-4 py-3">
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                  Independent Agencies ({independentAgencies.length})
                </h3>
                <div className="space-y-1">
                  {independentAgencies.map((agency) => (
                    <Link
                      key={agency.id}
                      href={`/agencies/${agency.slug}`}
                      className="flex items-center justify-between py-1 px-2 -mx-2 rounded hover:bg-slate-50 group"
                    >
                      <span className="text-sm">
                        <span className="font-medium text-slate-900">{agency.abbreviation}</span>
                        <span className="text-slate-400 mx-1.5">-</span>
                        <span className="text-slate-600">{agency.name}</span>
                      </span>
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500" />
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            {/* Data Sources */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-medium text-slate-900 mb-2">Data Sources</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="https://sam.gov/hierarchy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-ai-blue hover:text-ai-blue-dark"
                  >
                    SAM.gov Federal Hierarchy
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.usa.gov/agency-index"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-ai-blue hover:text-ai-blue-dark"
                  >
                    USA.gov Agency Index
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.cfo.gov"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-ai-blue hover:text-ai-blue-dark"
                  >
                    CFO.gov
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Main Content - Full Hierarchy Tree */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
                <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Building className="w-4 h-4 text-slate-500" />
                  Full Organization Hierarchy
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Click on any organization to view details. Expand departments to see sub-agencies.
                </p>
              </div>
              <div className="p-4">
                <AgencyHierarchyTree
                  organizations={hierarchy}
                  linkMode="detail"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

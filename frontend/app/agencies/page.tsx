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
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          <Breadcrumbs
            items={[
              { label: 'Federal Agencies', href: undefined },
            ]}
          />
          <h1 className="font-serif text-3xl font-medium text-white">
            Federal Agency Hierarchy
          </h1>
          <p className="text-charcoal-300 mt-2">
            Explore the organizational structure of the U.S. federal government, including the 24 CFO Act agencies
            and their sub-agencies.
          </p>
        </div>
      </header>

      {/* Stats Row */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-charcoal">{stats.totalOrganizations}</div>
            <div className="text-sm text-charcoal-500">Total Organizations</div>
          </div>
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-ifp-purple">{stats.cfoActAgencies}</div>
            <div className="text-sm text-charcoal-500">CFO Act Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-charcoal">{stats.cabinetDepartments}</div>
            <div className="text-sm text-charcoal-500">Cabinet Departments</div>
          </div>
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-status-success">{stats.independentAgencies}</div>
            <div className="text-sm text-charcoal-500">Independent Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-charcoal-600">{stats.subAgencies}</div>
            <div className="text-sm text-charcoal-500">Sub-Agencies</div>
          </div>
          <div className="bg-white rounded-lg border border-charcoal-200 p-4">
            <div className="text-2xl font-bold text-ifp-orange">{stats.maxDepth + 1}</div>
            <div className="text-sm text-charcoal-500">Hierarchy Levels</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Quick Links */}
          <div className="lg:col-span-1 space-y-6">
            {/* CFO Act Agencies */}
            <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-charcoal-100 bg-cream">
                <h2 className="font-serif font-medium text-charcoal flex items-center gap-2">
                  <Landmark className="w-4 h-4 text-ifp-purple" />
                  CFO Act Agencies
                </h2>
                <p className="text-xs text-charcoal-500 mt-1">
                  24 major agencies subject to the Chief Financial Officers Act of 1990
                </p>
              </div>

              {/* Cabinet Departments */}
              <div className="px-4 py-3 border-b border-charcoal-100">
                <h3 className="text-xs font-medium text-charcoal-500 uppercase tracking-wide mb-2">
                  Cabinet Departments ({cabinetDepartments.length})
                </h3>
                <div className="space-y-1">
                  {cabinetDepartments.map((dept) => (
                    <Link
                      key={dept.id}
                      href={`/agencies/${dept.slug}`}
                      className="flex items-center justify-between py-1 px-2 -mx-2 rounded hover:bg-cream group"
                    >
                      <span className="text-sm">
                        <span className="font-medium text-charcoal">{dept.abbreviation}</span>
                        <span className="text-charcoal-400 mx-1.5">-</span>
                        <span className="text-charcoal-600">{dept.name}</span>
                      </span>
                      <ChevronRight className="w-4 h-4 text-charcoal-300 group-hover:text-ifp-purple" />
                    </Link>
                  ))}
                </div>
              </div>

              {/* Independent Agencies */}
              <div className="px-4 py-3">
                <h3 className="text-xs font-medium text-charcoal-500 uppercase tracking-wide mb-2">
                  Independent Agencies ({independentAgencies.length})
                </h3>
                <div className="space-y-1">
                  {independentAgencies.map((agency) => (
                    <Link
                      key={agency.id}
                      href={`/agencies/${agency.slug}`}
                      className="flex items-center justify-between py-1 px-2 -mx-2 rounded hover:bg-cream group"
                    >
                      <span className="text-sm">
                        <span className="font-medium text-charcoal">{agency.abbreviation}</span>
                        <span className="text-charcoal-400 mx-1.5">-</span>
                        <span className="text-charcoal-600">{agency.name}</span>
                      </span>
                      <ChevronRight className="w-4 h-4 text-charcoal-300 group-hover:text-ifp-purple" />
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            {/* Data Sources */}
            <div className="bg-white rounded-lg border border-charcoal-200 p-4">
              <h3 className="font-medium text-charcoal mb-2">Data Sources</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="https://sam.gov/hierarchy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-ifp-purple hover:text-ifp-purple-dark"
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
                    className="flex items-center gap-1 text-ifp-purple hover:text-ifp-purple-dark"
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
                    className="flex items-center gap-1 text-ifp-purple hover:text-ifp-purple-dark"
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
            <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-charcoal-100 bg-cream">
                <h2 className="font-serif font-medium text-charcoal flex items-center gap-2">
                  <Building className="w-4 h-4 text-charcoal-500" />
                  Full Organization Hierarchy
                </h2>
                <p className="text-xs text-charcoal-500 mt-1">
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

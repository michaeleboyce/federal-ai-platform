import { notFound } from 'next/navigation';
import Link from 'next/link';
import {
  Landmark,
  Building2,
  Building,
  Globe,
  ExternalLink,
} from 'lucide-react';
import {
  getOrganizationBySlug,
  getOrganizationBreadcrumbs,
  getChildren,
  getParent,
  getDescendants,
} from '@/lib/hierarchy-db';
import { getOrganizationAIAuthorizations } from '@/lib/product-authorizations-db';
import { getUseCasesByOrganization } from '@/lib/use-case-db';
import { getProfileByOrganizationId } from '@/lib/agency-tools-db';
import { getIncidentsByAgencyName } from '@/lib/incident-db';
import { HierarchyBreadcrumbs } from '@/components/hierarchy/HierarchyBreadcrumbs';
import AgencyTabs from './AgencyTabs';
import type { OrgLevel } from '@/lib/db/schema';

// Icon mapping for organization levels
const levelIcons: Record<OrgLevel, typeof Building2> = {
  department: Landmark,
  independent: Building2,
  sub_agency: Building,
  office: Building,
  component: Building,
};

const levelLabels: Record<OrgLevel, string> = {
  department: 'Cabinet Department',
  independent: 'Independent Agency',
  sub_agency: 'Sub-Agency / Bureau',
  office: 'Office',
  component: 'Component',
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const org = await getOrganizationBySlug(slug);

  if (!org) {
    return {
      title: 'Agency Not Found | Federal AI Platform',
    };
  }

  return {
    title: `${org.abbreviation || org.name} | Federal Agency | Federal AI Platform`,
    description: org.description || `Information about ${org.name}`,
  };
}

export default async function AgencyDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const org = await getOrganizationBySlug(slug);

  if (!org) {
    notFound();
  }

  // Fetch related data in parallel
  const [breadcrumbs, children, parent, descendants, aiServices, useCases, agencyTools, incidents] = await Promise.all([
    getOrganizationBreadcrumbs(org.id),
    getChildren(org.id),
    getParent(org.id),
    getDescendants(org.id),
    getOrganizationAIAuthorizations(org.id),
    getUseCasesByOrganization(org.id, org.name, org.abbreviation),
    getProfileByOrganizationId(org.id),
    getIncidentsByAgencyName(org.name, org.abbreviation),
  ]);

  const Icon = levelIcons[org.level as OrgLevel] || Building;
  const levelLabel = levelLabels[org.level as OrgLevel] || 'Organization';

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-charcoal-800 py-6 border-b-4 border-ifp-purple">
        <div className="container mx-auto px-4">
          {/* Hierarchy Breadcrumbs */}
          <HierarchyBreadcrumbs
            breadcrumbs={breadcrumbs}
            showHome={true}
            homeHref="/agencies"
            homeLabel="All Agencies"
          />

          {/* Agency Header */}
          <div className="mt-4 flex items-start gap-4">
            <div
              className={`
                flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center
                ${
                  org.level === 'department'
                    ? 'bg-ifp-purple-light'
                    : org.level === 'independent'
                    ? 'bg-ifp-orange-light'
                    : 'bg-charcoal-600'
                }
              `}
            >
              <Icon
                className={`w-6 h-6 ${
                  org.level === 'department'
                    ? 'text-ifp-purple-dark'
                    : org.level === 'independent'
                    ? 'text-ifp-orange-dark'
                    : 'text-charcoal-300'
                }`}
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                {org.abbreviation && (
                  <span className="text-2xl font-serif font-medium text-white">
                    {org.abbreviation}
                  </span>
                )}
                <span className="text-lg text-charcoal-300">{org.name}</span>
              </div>
              <div className="mt-2 flex items-center gap-3">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-charcoal-600 text-charcoal-200">
                  {levelLabel}
                </span>
                {org.isCfoActAgency && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
                    CFO Act Agency
                  </span>
                )}
                {org.isCabinetDepartment && org.level !== 'department' && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
                    Cabinet Department
                  </span>
                )}
              </div>
              {org.description && (
                <p className="mt-3 text-charcoal-300">{org.description}</p>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Organization Details */}
            <div className="bg-white rounded-lg border border-charcoal-200 p-4">
              <h2 className="font-serif font-medium text-charcoal mb-4">
                Organization Details
              </h2>
              <dl className="space-y-3">
                {org.website && (
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      Website
                    </dt>
                    <dd className="mt-0.5">
                      <a
                        href={org.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-ifp-purple hover:text-ifp-purple-dark text-sm"
                      >
                        <Globe className="w-4 h-4" />
                        {org.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </dd>
                  </div>
                )}
                {parent && (
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      Parent Organization
                    </dt>
                    <dd className="mt-0.5">
                      <Link
                        href={`/agencies/${parent.slug}`}
                        className="text-ifp-purple hover:text-ifp-purple-dark text-sm"
                      >
                        {parent.abbreviation || parent.name}
                      </Link>
                    </dd>
                  </div>
                )}
                {org.cgacCode && (
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      CGAC Code
                    </dt>
                    <dd className="mt-0.5 text-sm text-charcoal font-mono">
                      {org.cgacCode}
                    </dd>
                  </div>
                )}
                {org.agencyCode && (
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      Agency Code
                    </dt>
                    <dd className="mt-0.5 text-sm text-charcoal font-mono">
                      {org.agencyCode}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Statistics */}
            {descendants.length > 0 && (
              <div className="bg-white rounded-lg border border-charcoal-200 p-4">
                <h2 className="font-serif font-medium text-charcoal mb-4">Statistics</h2>
                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      Direct Sub-Orgs
                    </dt>
                    <dd className="mt-0.5 text-2xl font-bold text-charcoal">
                      {children.length}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-charcoal-500 uppercase tracking-wide">
                      Total Descendants
                    </dt>
                    <dd className="mt-0.5 text-2xl font-bold text-charcoal">
                      {descendants.length}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>

          {/* Right Column - Tabbed Content */}
          <div className="lg:col-span-2">
            <AgencyTabs
              aiTools={agencyTools}
              aiServices={aiServices}
              useCases={useCases}
              incidents={incidents}
              children={children}
              orgName={org.name}
              orgAbbreviation={org.abbreviation}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

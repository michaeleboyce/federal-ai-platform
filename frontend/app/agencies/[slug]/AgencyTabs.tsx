'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Bot,
  FileText,
  AlertTriangle,
  Building,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import type { UseCase } from '@/lib/use-case-db';
import type { AgencyProfileWithTools } from '@/lib/agency-tools-db';
import type { FederalOrganization, OrgLevel, ProductType } from '@/lib/db/schema';

// Incident type (simplified)
interface Incident {
  incidentId: number;
  title: string;
  description: string | null;
  date: string | null;
}

// Authorization type (from product-authorizations-db)
interface AIService {
  fedrampId: string;
  cloudServiceProvider: string | null;
  cloudServiceOffering: string | null;
  atoIssuanceDate: string | null;
}

interface AgencyTabsProps {
  aiTools: AgencyProfileWithTools | null;
  aiServices: AIService[];
  useCases: UseCase[];
  incidents: Incident[];
  children: FederalOrganization[];
  orgName: string;
  orgAbbreviation?: string | null;
}

type TabId = 'ai-tools' | 'use-cases' | 'incidents' | 'sub-orgs';

const levelIcons: Record<OrgLevel, typeof Building> = {
  department: Building,
  independent: Building,
  sub_agency: Building,
  office: Building,
  component: Building,
};

export default function AgencyTabs({
  aiTools,
  aiServices,
  useCases,
  incidents,
  children,
  orgName,
  orgAbbreviation,
}: AgencyTabsProps) {
  const toolCount = (aiTools?.tools?.length || 0) + aiServices.length;
  const [activeTab, setActiveTab] = useState<TabId>(
    toolCount > 0 ? 'ai-tools' : useCases.length > 0 ? 'use-cases' : 'sub-orgs'
  );

  const tabs: Array<{ id: TabId; label: string; count: number; Icon: typeof Bot }> = [
    { id: 'ai-tools', label: 'AI Tools', count: toolCount, Icon: Bot },
    { id: 'use-cases', label: 'Use Cases', count: useCases.length, Icon: FileText },
    { id: 'incidents', label: 'Incidents', count: incidents.length, Icon: AlertTriangle },
    { id: 'sub-orgs', label: 'Sub-Orgs', count: children.length, Icon: Building },
  ];

  return (
    <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
      {/* Tab Bar */}
      <div className="flex border-b border-charcoal-200 bg-cream overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'border-ifp-purple text-ifp-purple bg-white'
                : 'border-transparent text-charcoal-500 hover:text-charcoal hover:bg-cream-light'
            }`}
          >
            <tab.Icon className="w-4 h-4" />
            {tab.label}
            <span
              className={`px-1.5 py-0.5 text-xs rounded-full ${
                activeTab === tab.id
                  ? 'bg-ifp-purple-light text-ifp-purple'
                  : 'bg-charcoal-100 text-charcoal-600'
              }`}
            >
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'ai-tools' && (
          <AIToolsContent aiTools={aiTools} aiServices={aiServices} orgName={orgName} />
        )}
        {activeTab === 'use-cases' && (
          <UseCasesContent useCases={useCases} orgName={orgName} />
        )}
        {activeTab === 'incidents' && (
          <IncidentsContent incidents={incidents} />
        )}
        {activeTab === 'sub-orgs' && (
          <SubOrgsContent children={children} orgName={orgName} orgAbbreviation={orgAbbreviation} />
        )}
      </div>
    </div>
  );
}

// ========================================
// AI TOOLS CONTENT
// ========================================

function AIToolsContent({
  aiTools,
  aiServices,
  orgName,
}: {
  aiTools: AgencyProfileWithTools | null;
  aiServices: AIService[];
  orgName: string;
}) {
  if (!aiTools?.tools?.length && !aiServices.length) {
    return (
      <div className="text-center py-8">
        <Bot className="w-12 h-12 text-charcoal-300 mx-auto" />
        <h3 className="mt-4 text-lg font-serif font-medium text-charcoal">No AI Tools Found</h3>
        <p className="mt-2 text-charcoal-500">
          No public AI tools or authorized AI services have been identified for {orgName}.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Internal AI Tools */}
      {aiTools && aiTools.tools.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-charcoal-500 uppercase tracking-wide mb-3">
            Internal AI Tools ({aiTools.tools.length})
          </h3>
          <div className="space-y-2">
            {aiTools.tools.map((tool) => (
              <div
                key={tool.id}
                className="flex items-center gap-3 p-3 bg-cream rounded-lg"
              >
                <div className="flex-1">
                  <span className="font-medium text-charcoal">{tool.productName}</span>
                </div>
                <ProductTypeBadge type={tool.productType} />
                {tool.isPilotOrLimited && (
                  <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                    Pilot
                  </span>
                )}
                {tool.availableToAllStaff === 'yes' && (
                  <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                    All Staff
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Authorized AI Services (FedRAMP) */}
      {aiServices.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-charcoal-500 uppercase tracking-wide mb-3">
            Authorized AI Services ({aiServices.length})
          </h3>
          <div className="space-y-2">
            {aiServices.slice(0, 10).map((service) => (
              <Link
                key={service.fedrampId}
                href={`/product/${service.fedrampId}`}
                className="flex items-center gap-3 p-3 bg-cream rounded-lg hover:bg-cream-light transition-colors"
              >
                <div className="flex-1">
                  <span className="font-medium text-charcoal">
                    {service.cloudServiceOffering}
                  </span>
                  <span className="text-charcoal-500 ml-2">
                    by {service.cloudServiceProvider}
                  </span>
                </div>
                {service.atoIssuanceDate && (
                  <span className="text-xs text-charcoal-400">
                    ATO: {service.atoIssuanceDate}
                  </span>
                )}
                <ChevronRight className="w-4 h-4 text-charcoal-400" />
              </Link>
            ))}
            {aiServices.length > 10 && (
              <Link
                href={`/products?agency=${encodeURIComponent(orgName)}`}
                className="block text-center py-2 text-sm text-ifp-purple hover:underline"
              >
                View all {aiServices.length} authorized services →
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ========================================
// USE CASES CONTENT
// ========================================

function UseCasesContent({
  useCases,
  orgName,
}: {
  useCases: UseCase[];
  orgName: string;
}) {
  if (useCases.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="w-12 h-12 text-charcoal-300 mx-auto" />
        <h3 className="mt-4 text-lg font-serif font-medium text-charcoal">No Use Cases Found</h3>
        <p className="mt-2 text-charcoal-500">
          No AI use cases have been reported for {orgName}.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {useCases.slice(0, 10).map((useCase) => (
        <Link
          key={useCase.id}
          href={`/use-cases/${useCase.slug}`}
          className="block p-4 bg-cream rounded-lg hover:bg-cream-light transition-colors"
        >
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <h4 className="font-medium text-charcoal">{useCase.useCaseName}</h4>
              {useCase.bureau && (
                <p className="text-sm text-charcoal-500 mt-0.5">{useCase.bureau}</p>
              )}
              {useCase.intendedPurpose && (
                <p className="text-sm text-charcoal-600 mt-2 line-clamp-2">
                  {useCase.intendedPurpose}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-2">
                {useCase.domainCategory && (
                  <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-600 rounded-full">
                    {useCase.domainCategory}
                  </span>
                )}
                {useCase.stageOfDevelopment && (
                  <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                    {useCase.stageOfDevelopment}
                  </span>
                )}
                {useCase.hasGenai && (
                  <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                    GenAI
                  </span>
                )}
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-charcoal-400 flex-shrink-0" />
          </div>
        </Link>
      ))}
      {useCases.length > 10 && (
        <Link
          href={`/use-cases?agency=${encodeURIComponent(orgName)}`}
          className="block text-center py-2 text-sm text-ifp-purple hover:underline"
        >
          View all {useCases.length} use cases →
        </Link>
      )}
    </div>
  );
}

// ========================================
// INCIDENTS CONTENT
// ========================================

function IncidentsContent({ incidents }: { incidents: Incident[] }) {
  if (incidents.length === 0) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="w-12 h-12 text-charcoal-300 mx-auto" />
        <h3 className="mt-4 text-lg font-serif font-medium text-charcoal">No Incidents Found</h3>
        <p className="mt-2 text-charcoal-500">
          No AI-related incidents have been linked to this agency.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {incidents.map((incident) => (
        <Link
          key={incident.incidentId}
          href={`/incidents/${incident.incidentId}`}
          className="block p-4 bg-cream rounded-lg hover:bg-cream-light transition-colors"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-ifp-orange flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-charcoal">{incident.title}</h4>
              {incident.date && (
                <p className="text-sm text-charcoal-500 mt-0.5">{incident.date}</p>
              )}
              {incident.description && (
                <p className="text-sm text-charcoal-600 mt-2 line-clamp-2">
                  {incident.description}
                </p>
              )}
            </div>
            <ChevronRight className="w-5 h-5 text-charcoal-400 flex-shrink-0" />
          </div>
        </Link>
      ))}
    </div>
  );
}

// ========================================
// SUB-ORGS CONTENT
// ========================================

function SubOrgsContent({
  children,
  orgName,
  orgAbbreviation,
}: {
  children: FederalOrganization[];
  orgName: string;
  orgAbbreviation?: string | null;
}) {
  if (children.length === 0) {
    return (
      <div className="text-center py-8">
        <Building className="w-12 h-12 text-charcoal-300 mx-auto" />
        <h3 className="mt-4 text-lg font-serif font-medium text-charcoal">No Sub-Organizations</h3>
        <p className="mt-2 text-charcoal-500">
          {orgAbbreviation || orgName} does not have any direct sub-organizations in our database.
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-charcoal-100 -mx-4">
      {children.map((child) => {
        const ChildIcon = levelIcons[child.level as OrgLevel] || Building;
        return (
          <Link
            key={child.id}
            href={`/agencies/${child.slug}`}
            className="flex items-center gap-4 p-4 hover:bg-cream transition-colors"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-charcoal-100 flex items-center justify-center">
              <ChildIcon className="w-5 h-5 text-charcoal-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {child.abbreviation && (
                  <span className="font-semibold text-charcoal">{child.abbreviation}</span>
                )}
                <span className="text-charcoal-600 truncate">{child.name}</span>
              </div>
              {child.description && (
                <p className="text-sm text-charcoal-500 truncate mt-0.5">{child.description}</p>
              )}
            </div>
            <ChevronRight className="w-5 h-5 text-charcoal-300 flex-shrink-0" />
          </Link>
        );
      })}
    </div>
  );
}

// ========================================
// PRODUCT TYPE BADGE
// ========================================

function ProductTypeBadge({ type }: { type: ProductType }) {
  const config: Record<ProductType, { label: string; bg: string; text: string }> = {
    staff_chatbot: { label: 'Chatbot', bg: 'bg-ifp-purple-light', text: 'text-ifp-purple' },
    coding_assistant: { label: 'Coding', bg: 'bg-ifp-orange-light', text: 'text-ifp-orange' },
    document_automation: { label: 'Doc Auto', bg: 'bg-green-100', text: 'text-green-700' },
    none_identified: { label: 'Other', bg: 'bg-charcoal-100', text: 'text-charcoal-500' },
  };

  const { label, bg, text } = config[type] || config.none_identified;

  return (
    <span className={`px-2 py-0.5 text-xs ${bg} ${text} rounded-full font-medium`}>
      {label}
    </span>
  );
}

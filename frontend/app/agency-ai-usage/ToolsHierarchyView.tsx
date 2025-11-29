'use client';

import { useState, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import type { AgencyProfileWithTools, ToolStats } from '@/lib/agency-tools-db';
import type { ProductType, AgencyAiTool } from '@/lib/db/schema';
import ToolsFilterBar from './ToolsFilterBar';

interface ToolsHierarchyViewProps {
  profiles: AgencyProfileWithTools[];
  stats: ToolStats;
}

interface DepartmentGroup {
  name: string;
  profiles: AgencyProfileWithTools[];
  aggregatedStats: {
    toolCount: number;
    chatbotCount: number;
    codingCount: number;
    docAutoCount: number;
  };
}

export default function ToolsHierarchyView({ profiles, stats }: ToolsHierarchyViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Initialize from URL params
  const initialType = (searchParams.get('type') as ProductType | 'all') || 'all';
  const initialExpanded = searchParams.get('expanded')?.split(',').filter(Boolean) || [];

  const [selectedType, setSelectedType] = useState<ProductType | 'all'>(initialType);
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set(initialExpanded));
  const [expandedAgencies, setExpandedAgencies] = useState<Set<number>>(new Set());

  // Filter profiles based on selected type
  const filteredProfiles = useMemo(() => {
    if (selectedType === 'all') return profiles;

    return profiles.map(profile => ({
      ...profile,
      tools: profile.tools.filter(t => t.productType === selectedType),
    })).filter(profile =>
      // Keep agencies with matching tools OR agencies with no tools if showing all
      profile.tools.length > 0 || profile.toolCount === 0
    );
  }, [profiles, selectedType]);

  // Group by department
  const departments = useMemo(() => {
    const deptMap = new Map<string, AgencyProfileWithTools[]>();

    for (const profile of filteredProfiles) {
      const deptName = profile.departmentLevelName || 'Other';
      const existing = deptMap.get(deptName) || [];
      existing.push(profile);
      deptMap.set(deptName, existing);
    }

    const result: DepartmentGroup[] = [];
    for (const [name, deptProfiles] of deptMap) {
      const aggregatedStats = {
        toolCount: deptProfiles.reduce((sum, p) => sum + p.tools.length, 0),
        chatbotCount: deptProfiles.filter(p =>
          p.tools.some(t => t.productType === 'staff_chatbot')
        ).length,
        codingCount: deptProfiles.filter(p =>
          p.tools.some(t => t.productType === 'coding_assistant')
        ).length,
        docAutoCount: deptProfiles.filter(p =>
          p.tools.some(t => t.productType === 'document_automation')
        ).length,
      };

      result.push({ name, profiles: deptProfiles, aggregatedStats });
    }

    // Sort by tool count desc
    result.sort((a, b) => b.aggregatedStats.toolCount - a.aggregatedStats.toolCount);

    return result;
  }, [filteredProfiles]);

  // Update URL when filter changes
  function handleTypeChange(type: ProductType | 'all') {
    setSelectedType(type);
    const params = new URLSearchParams(searchParams);
    if (type === 'all') {
      params.delete('type');
    } else {
      params.set('type', type);
    }
    router.replace(`/agency-ai-usage?${params.toString()}`, { scroll: false });
  }

  function toggleDept(name: string) {
    setExpandedDepts(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  function toggleAgency(id: number) {
    setExpandedAgencies(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
      <div className="p-6 border-b border-charcoal-200">
        <h2 className="font-serif text-xl font-medium text-charcoal mb-4">
          Generative AI Tools by Agency
        </h2>
        <ToolsFilterBar
          selectedType={selectedType}
          onTypeChange={handleTypeChange}
          stats={stats}
        />
      </div>

      <div className="divide-y divide-charcoal-100">
        {departments.map(dept => (
          <div key={dept.name}>
            {/* Department Header */}
            <button
              onClick={() => toggleDept(dept.name)}
              className="w-full flex items-center gap-3 p-4 hover:bg-cream text-left transition-colors"
            >
              <span className="text-charcoal-400">
                {expandedDepts.has(dept.name) ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
              </span>

              <div className="flex-1">
                <div className="font-semibold text-charcoal">{dept.name}</div>
                <div className="text-sm text-charcoal-500">
                  {dept.profiles.length} {dept.profiles.length === 1 ? 'agency' : 'agencies'}
                </div>
              </div>

              <div className="flex gap-2">
                {dept.aggregatedStats.chatbotCount > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                    {dept.aggregatedStats.chatbotCount} Chatbot{dept.aggregatedStats.chatbotCount !== 1 ? 's' : ''}
                  </span>
                )}
                {dept.aggregatedStats.codingCount > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                    {dept.aggregatedStats.codingCount} Coding
                  </span>
                )}
                {dept.aggregatedStats.docAutoCount > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                    {dept.aggregatedStats.docAutoCount} Doc Auto
                  </span>
                )}
                {dept.aggregatedStats.toolCount === 0 && (
                  <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-500 rounded-full">
                    No tools
                  </span>
                )}
              </div>
            </button>

            {/* Agencies in Department */}
            {expandedDepts.has(dept.name) && (
              <div className="bg-cream-light">
                {dept.profiles.map(profile => (
                  <div key={profile.id}>
                    {/* Agency Row */}
                    <button
                      onClick={() => toggleAgency(profile.id)}
                      className="w-full flex items-center gap-3 p-3 pl-10 hover:bg-cream text-left border-t border-charcoal-100 transition-colors"
                    >
                      <span className="text-charcoal-400">
                        {profile.tools.length > 0 ? (
                          expandedAgencies.has(profile.id) ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )
                        ) : (
                          <span className="w-4 h-4" />
                        )}
                      </span>

                      <div className="flex-1">
                        <span className="font-medium text-charcoal">
                          {profile.abbreviation && (
                            <span className="text-ifp-purple mr-2">{profile.abbreviation}</span>
                          )}
                          {profile.agencyName}
                        </span>
                      </div>

                      {profile.tools.length > 0 ? (
                        <span className="text-sm text-charcoal-500">
                          {profile.tools.length} tool{profile.tools.length !== 1 ? 's' : ''}
                        </span>
                      ) : (
                        <span className="text-sm text-charcoal-400 italic">
                          No public tool identified
                        </span>
                      )}
                    </button>

                    {/* Tools */}
                    {expandedAgencies.has(profile.id) && profile.tools.length > 0 && (
                      <div className="bg-white border-t border-charcoal-100">
                        {profile.tools.map(tool => (
                          <ToolRow key={tool.id} tool={tool} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {departments.length === 0 && (
        <div className="p-12 text-center text-charcoal-500">
          No agencies found matching the selected filter.
        </div>
      )}
    </div>
  );
}

// ========================================
// TOOL ROW
// ========================================

function ToolRow({ tool }: { tool: AgencyAiTool }) {
  const [showCitation, setShowCitation] = useState(false);

  return (
    <div className="p-3 pl-16 border-b border-charcoal-50 last:border-b-0">
      <div className="flex items-center gap-3">
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

        {tool.citationUrl && (
          <button
            onClick={() => setShowCitation(!showCitation)}
            className="text-charcoal-400 hover:text-ifp-purple"
            title="View source"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Citation Details */}
      {showCitation && (tool.citationChicago || tool.citationUrl) && (
        <div className="mt-3 p-3 bg-cream rounded-md text-sm">
          {tool.citationChicago && (
            <p className="text-charcoal-600 mb-2">{tool.citationChicago}</p>
          )}
          {tool.citationUrl && (
            <a
              href={tool.citationUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-ifp-purple hover:underline flex items-center gap-1"
            >
              View Source <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {tool.citationAccessedDate && (
            <p className="text-xs text-charcoal-400 mt-1">
              Accessed: {tool.citationAccessedDate}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ========================================
// BADGE
// ========================================

function ProductTypeBadge({ type }: { type: ProductType }) {
  const config: Record<ProductType, { label: string; bg: string; text: string }> = {
    staff_chatbot: { label: 'Chatbot', bg: 'bg-ifp-purple-light', text: 'text-ifp-purple' },
    coding_assistant: { label: 'Coding Assistant', bg: 'bg-ifp-orange-light', text: 'text-ifp-orange' },
    document_automation: { label: 'Doc Automation', bg: 'bg-green-100', text: 'text-green-700' },
    none_identified: { label: 'None', bg: 'bg-charcoal-100', text: 'text-charcoal-500' },
  };

  const { label, bg, text } = config[type] || config.none_identified;

  return (
    <span className={`px-2 py-0.5 text-xs ${bg} ${text} rounded-full font-medium`}>
      {label}
    </span>
  );
}

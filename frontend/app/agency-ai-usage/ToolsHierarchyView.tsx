'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChevronDown, ChevronRight, ExternalLink, List, Network, ChevronsUpDown, Download } from 'lucide-react';
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


type ViewMode = 'flat' | 'hierarchy';

export default function ToolsHierarchyView({ profiles, stats }: ToolsHierarchyViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Initialize from URL params
  const initialType = (searchParams.get('type') as ProductType | 'all') || 'all';
  const initialExpanded = searchParams.get('expanded')?.split(',').filter(Boolean) || [];
  const initialView = (searchParams.get('view') as ViewMode) || 'hierarchy';

  const [selectedType, setSelectedType] = useState<ProductType | 'all'>(initialType);
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set(initialExpanded));
  const [expandedAgencies, setExpandedAgencies] = useState<Set<number>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>(initialView);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setExportMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Helper function to download file
  function downloadFile(content: string, filename: string) {
    // Add BOM for Excel to recognize UTF-8 encoding
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8' });

    // Create a temporary anchor element
    const link = document.createElement('a');
    link.style.display = 'none';

    // Use the File API for better filename support
    const file = new File([blob], filename, { type: 'text/csv;charset=utf-8' });
    link.href = URL.createObjectURL(file);
    link.setAttribute('download', filename);

    document.body.appendChild(link);
    link.click();

    // Cleanup
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }, 100);
  }

  // Export Summary: One row per agency with aggregated tool info
  function exportSummary() {
    const headers = [
      'Agency Name',
      'Abbreviation',
      'Parent Agency',
      'Parent Abbreviation',
      'Has Chatbot',
      'Chatbot All Staff',
      'Chatbot Pilot',
      'Chatbot Source',
      'Chatbot Source URL',
      'Has Coding Assistant',
      'Coding All Staff',
      'Coding Pilot',
      'Coding Source',
      'Coding Source URL',
    ];

    const rows = profiles.map(profile => {
      const chatbots = profile.tools.filter(t => t.productType === 'staff_chatbot');
      const codingTools = profile.tools.filter(t => t.productType === 'coding_assistant');

      const hasChatbot = chatbots.length > 0;
      const hasCoding = codingTools.length > 0;

      // For chatbot fields
      const chatbotAllStaff = chatbots.length > 0
        ? (chatbots.some(t => t.availableToAllStaff === 'yes') ? 'Yes' :
           chatbots.some(t => t.availableToAllStaff === 'subset') ? 'Subset' : 'No')
        : '';
      const chatbotPilot = chatbots.some(t => t.isPilotOrLimited) ? 'Yes' : (hasChatbot ? 'No' : '');
      const chatbotSource = chatbots.length > 0 ? (chatbots[0].citationChicago || '') : '';
      const chatbotUrl = chatbots.length > 0 ? (chatbots[0].citationUrl || '') : '';

      // For coding assistant fields
      const codingAllStaff = codingTools.length > 0
        ? (codingTools.some(t => t.availableToAllStaff === 'yes') ? 'Yes' :
           codingTools.some(t => t.availableToAllStaff === 'subset') ? 'Subset' : 'No')
        : '';
      const codingPilot = codingTools.some(t => t.isPilotOrLimited) ? 'Yes' : (hasCoding ? 'No' : '');
      const codingSource = codingTools.length > 0 ? (codingTools[0].citationChicago || '') : '';
      const codingUrl = codingTools.length > 0 ? (codingTools[0].citationUrl || '') : '';

      return [
        profile.agencyName || '',
        profile.abbreviation || '',
        profile.departmentLevelName || '',
        profile.parentAbbreviation || '',
        hasChatbot ? 'Yes' : 'No',
        chatbotAllStaff,
        chatbotPilot,
        chatbotSource,
        chatbotUrl,
        hasCoding ? 'Yes' : 'No',
        codingAllStaff,
        codingPilot,
        codingSource,
        codingUrl,
      ];
    });

    // Build CSV content
    const escapeCell = (cell: string) => {
      if (cell.includes(',') || cell.includes('\n') || cell.includes('"')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    };

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCell).join(',')),
    ].join('\n');

    const today = new Date().toISOString().split('T')[0];
    downloadFile(csvContent, `Agency-AI-Adoption-Summary-${today}.csv`);
    setExportMenuOpen(false);
  }

  // Export Detailed: One row per tool
  function exportDetailed() {
    const headers = [
      'Agency Name',
      'Abbreviation',
      'Parent Agency',
      'Parent Abbreviation',
      'Tool Name',
      'Tool Type',
      'Available to All Staff',
      'Is Pilot',
      'Internal Data Allowed',
      'Source Citation',
      'Source URL',
      'Accessed Date',
    ];

    const rows: string[][] = [];

    for (const profile of profiles) {
      if (profile.tools.length === 0) {
        // Include agencies with no tools
        rows.push([
          profile.agencyName || '',
          profile.abbreviation || '',
          profile.departmentLevelName || '',
          profile.parentAbbreviation || '',
          '',
          'None Identified',
          '',
          '',
          '',
          '',
          '',
          '',
        ]);
      } else {
        for (const tool of profile.tools) {
          const typeLabel = tool.productType === 'staff_chatbot' ? 'Chatbot'
            : tool.productType === 'coding_assistant' ? 'Coding Assistant'
            : tool.productType === 'document_automation' ? 'Document Automation'
            : 'None Identified';

          rows.push([
            profile.agencyName || '',
            profile.abbreviation || '',
            profile.departmentLevelName || '',
            profile.parentAbbreviation || '',
            tool.productName || '',
            typeLabel,
            tool.availableToAllStaff === 'yes' ? 'Yes'
              : tool.availableToAllStaff === 'subset' ? 'Subset'
              : tool.availableToAllStaff === 'no' ? 'No' : '',
            tool.isPilotOrLimited ? 'Yes' : 'No',
            tool.internalOrSensitiveData || '',
            tool.citationChicago || '',
            tool.citationUrl || '',
            tool.citationAccessedDate || '',
          ]);
        }
      }
    }

    // Build CSV content
    const escapeCell = (cell: string) => {
      if (cell.includes(',') || cell.includes('\n') || cell.includes('"')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    };

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCell).join(',')),
    ].join('\n');

    const today = new Date().toISOString().split('T')[0];
    downloadFile(csvContent, `Agency-AI-Adoption-Detailed-${today}.csv`);
    setExportMenuOpen(false);
  }

  // Export Hierarchical: Organized by parent department with sub-agencies indented
  function exportHierarchical() {
    const headers = [
      'Department/Agency',
      'Sub-Agency',
      'Abbreviation',
      'Chatbot Status',
      'Chatbot Tool',
      'Chatbot Source URL',
      'Coding Assistant Status',
      'Coding Tool',
      'Coding Source URL',
    ];

    // Helper to determine tool status: Agency-Wide, Partial Rollout, Pilot, or empty
    const getToolStatus = (tools: AgencyAiTool[]) => {
      if (tools.length === 0) return '';

      // Check for pilot first
      const hasPilot = tools.some(t => t.isPilotOrLimited);
      const hasAgencyWide = tools.some(t => t.availableToAllStaff === 'yes');
      const hasPartial = tools.some(t => t.availableToAllStaff === 'subset');

      if (hasPilot && !hasAgencyWide && !hasPartial) {
        return 'Pilot';
      } else if (hasAgencyWide) {
        return 'Agency-Wide';
      } else if (hasPartial) {
        return 'Partial Rollout';
      } else if (hasPilot) {
        return 'Pilot';
      }
      return 'Yes'; // Has tool but status unclear
    };

    // Group profiles by their root department
    const deptMap = new Map<string, AgencyProfileWithTools[]>();

    for (const profile of profiles) {
      const deptName = profile.departmentLevelName || profile.agencyName || 'Other';
      const existing = deptMap.get(deptName) || [];
      existing.push(profile);
      deptMap.set(deptName, existing);
    }

    // Sort departments by name
    const sortedDepts = Array.from(deptMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));

    const rows: string[][] = [];

    for (const [deptName, deptProfiles] of sortedDepts) {
      // Find the department-level profile (no parent) and sub-agencies (have parent)
      const deptProfile = deptProfiles.find(p => !p.parentAbbreviation &&
        (p.departmentLevelName === deptName || p.agencyName === deptName));
      const subAgencies = deptProfiles.filter(p => p.parentAbbreviation);
      const standaloneAgencies = deptProfiles.filter(p => !p.parentAbbreviation && p !== deptProfile);

      // Helper to build tool data columns (compressed)
      const buildToolColumns = (profile: AgencyProfileWithTools) => {
        const chatbots = profile.tools.filter(t => t.productType === 'staff_chatbot');
        const codingTools = profile.tools.filter(t => t.productType === 'coding_assistant');

        return [
          getToolStatus(chatbots),
          chatbots.length > 0 ? (chatbots[0].productName || '') : '',
          chatbots.length > 0 ? (chatbots[0].citationUrl || '') : '',
          getToolStatus(codingTools),
          codingTools.length > 0 ? (codingTools[0].productName || '') : '',
          codingTools.length > 0 ? (codingTools[0].citationUrl || '') : '',
        ];
      };

      // Add department row first
      if (deptProfile) {
        rows.push([
          deptName,
          '', // Sub-agency column empty for department
          deptProfile.abbreviation || '',
          ...buildToolColumns(deptProfile),
        ]);
      } else {
        // Department header row without its own profile
        rows.push([
          deptName,
          '',
          '',
          '', '', '', '', '', '', // Empty tool columns
        ]);
      }

      // Add sub-agencies (indented - agency column blank, sub-agency filled)
      const allSubAgencies = [...standaloneAgencies, ...subAgencies];
      allSubAgencies.sort((a, b) => (a.agencyName || '').localeCompare(b.agencyName || ''));

      for (const subAgency of allSubAgencies) {
        rows.push([
          '', // Department column empty for sub-agencies
          subAgency.agencyName || '',
          subAgency.abbreviation || '',
          ...buildToolColumns(subAgency),
        ]);
      }
    }

    // Build CSV content
    const escapeCell = (cell: string) => {
      if (cell.includes(',') || cell.includes('\n') || cell.includes('"')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    };

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCell).join(',')),
    ].join('\n');

    const today = new Date().toISOString().split('T')[0];
    downloadFile(csvContent, `Agency-AI-Adoption-Hierarchical-${today}.csv`);
    setExportMenuOpen(false);
  }

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

  // Group by department (using root department for sub-agencies)
  const departments = useMemo(() => {
    // Build a lookup from abbreviation to profile for finding parents
    const profileByAbbr = new Map<string, AgencyProfileWithTools>();
    for (const profile of filteredProfiles) {
      if (profile.abbreviation) {
        profileByAbbr.set(profile.abbreviation, profile);
      }
    }

    // Find the root department for a profile (follow parent chain)
    const getRootDepartment = (profile: AgencyProfileWithTools): string => {
      // If no parent, use own department name
      if (!profile.parentAbbreviation) {
        return profile.departmentLevelName || profile.agencyName || 'Other';
      }
      // If parent exists in our data, use parent's department
      const parent = profileByAbbr.get(profile.parentAbbreviation);
      if (parent) {
        return getRootDepartment(parent);
      }
      // Parent not in our data, use own department
      return profile.departmentLevelName || profile.agencyName || 'Other';
    };

    const deptMap = new Map<string, AgencyProfileWithTools[]>();

    for (const profile of filteredProfiles) {
      const deptName = getRootDepartment(profile);
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

  // Group agencies within departments - simpler structure for hierarchy view
  // Identifies department-wide profile (if any) and sub-agencies
  const hierarchicalDepartments = useMemo(() => {
    return departments.map(dept => {
      // Find the department's own profile (no parent, and matches department name)
      const deptProfile = dept.profiles.find(p =>
        !p.parentAbbreviation &&
        (p.departmentLevelName === dept.name || p.agencyName === dept.name)
      );

      // Sub-agencies are all profiles that have a parent
      const subAgencies = dept.profiles.filter(p => p.parentAbbreviation);

      // Standalone agencies are those without a parent that aren't the department itself
      const standaloneAgencies = dept.profiles.filter(p =>
        !p.parentAbbreviation &&
        p !== deptProfile
      );

      // Combine sub-agencies and standalone agencies for display
      const allAgencies = [...standaloneAgencies, ...subAgencies];
      allAgencies.sort((a, b) => b.tools.length - a.tools.length);

      return {
        ...dept,
        deptProfile, // The department's own profile with tools (if any)
        subAgencies: allAgencies, // All child/standalone agencies
      };
    });
  }, [departments]);

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

  function expandAllDepts() {
    setExpandedDepts(new Set(departments.map(d => d.name)));
  }

  function collapseAllDepts() {
    setExpandedDepts(new Set());
  }

  function expandAllAgencies() {
    const allIds = filteredProfiles.filter(p => p.tools.length > 0).map(p => p.id);
    setExpandedAgencies(new Set(allIds));
  }

  function collapseAllAgencies() {
    setExpandedAgencies(new Set());
  }

  const allDeptsExpanded = departments.length > 0 && expandedDepts.size === departments.length;
  const allAgenciesExpanded = filteredProfiles.filter(p => p.tools.length > 0).length > 0 &&
    filteredProfiles.filter(p => p.tools.length > 0).every(p => expandedAgencies.has(p.id));

  function handleViewModeChange(mode: ViewMode) {
    setViewMode(mode);
    const params = new URLSearchParams(searchParams);
    if (mode === 'hierarchy') {
      params.delete('view');
    } else {
      params.set('view', mode);
    }
    router.replace(`/agency-ai-usage?${params.toString()}`, { scroll: false });
  }

  return (
    <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
      <div className="p-6 border-b border-charcoal-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif text-xl font-medium text-charcoal">
            Generative AI Tools by Agency
          </h2>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 bg-charcoal-100 rounded-lg p-1">
              <button
                onClick={() => handleViewModeChange('hierarchy')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'hierarchy'
                    ? 'bg-white text-charcoal shadow-sm'
                    : 'text-charcoal-500 hover:text-charcoal'
                }`}
                title="Group agencies by department"
              >
                <Network className="w-4 h-4" />
                By Department
              </button>
              <button
                onClick={() => handleViewModeChange('flat')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'flat'
                    ? 'bg-white text-charcoal shadow-sm'
                    : 'text-charcoal-500 hover:text-charcoal'
                }`}
                title="Show all agencies as a simple list"
              >
                <List className="w-4 h-4" />
                All Agencies
              </button>
            </div>
            <button
              onClick={() => {
                if (viewMode === 'hierarchy') {
                  allDeptsExpanded ? collapseAllDepts() : expandAllDepts();
                } else {
                  allAgenciesExpanded ? collapseAllAgencies() : expandAllAgencies();
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium text-charcoal-500 hover:text-charcoal hover:bg-charcoal-100 transition-colors"
              title={viewMode === 'hierarchy'
                ? (allDeptsExpanded ? 'Collapse all departments' : 'Expand all departments')
                : (allAgenciesExpanded ? 'Collapse all agencies' : 'Expand all agencies')
              }
            >
              <ChevronsUpDown className="w-4 h-4" />
              {viewMode === 'hierarchy'
                ? (allDeptsExpanded ? 'Collapse All' : 'Expand All')
                : (allAgenciesExpanded ? 'Collapse All' : 'Expand All')
              }
            </button>

            {/* Export Dropdown */}
            <div className="relative" ref={exportMenuRef}>
              <button
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium bg-ifp-purple text-white hover:bg-ifp-purple-dark transition-colors"
                title="Export data to Excel"
              >
                <Download className="w-4 h-4" />
                Export
                <ChevronDown className={`w-4 h-4 transition-transform ${exportMenuOpen ? 'rotate-180' : ''}`} />
              </button>
              {exportMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-charcoal-200 z-50">
                  <div className="py-1">
                    <button
                      onClick={exportSummary}
                      className="w-full text-left px-4 py-2 text-sm text-charcoal hover:bg-cream transition-colors"
                    >
                      <div className="font-medium">Summary Export</div>
                      <div className="text-xs text-charcoal-500">One row per agency</div>
                    </button>
                    <button
                      onClick={exportDetailed}
                      className="w-full text-left px-4 py-2 text-sm text-charcoal hover:bg-cream transition-colors"
                    >
                      <div className="font-medium">Detailed Export</div>
                      <div className="text-xs text-charcoal-500">One row per tool</div>
                    </button>
                    <button
                      onClick={exportHierarchical}
                      className="w-full text-left px-4 py-2 text-sm text-charcoal hover:bg-cream transition-colors"
                    >
                      <div className="font-medium">Hierarchical Export</div>
                      <div className="text-xs text-charcoal-500">By department with sub-agencies</div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <ToolsFilterBar
          selectedType={selectedType}
          onTypeChange={handleTypeChange}
          stats={stats}
        />
      </div>

      {/* By Department View */}
      {viewMode === 'hierarchy' && (
        <div className="divide-y divide-charcoal-100">
          {hierarchicalDepartments.map(dept => (
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

              {/* Expanded Department Content */}
              {expandedDepts.has(dept.name) && (
                <div className="bg-cream-light">
                  {/* Department-wide tools section */}
                  {dept.deptProfile && dept.deptProfile.tools.length > 0 && (
                    <div className="border-t border-charcoal-100">
                      <div className="px-10 py-2 bg-charcoal-50 text-xs text-charcoal-500 uppercase tracking-wide">
                        {dept.deptProfile.abbreviation || 'Department'}-wide tools ({dept.deptProfile.tools.length})
                      </div>
                      <div className="bg-white">
                        {dept.deptProfile.tools.map(tool => (
                          <ToolRow key={tool.id} tool={tool} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sub-agencies section */}
                  {dept.subAgencies.length > 0 && (
                    <>
                      <div className="border-t border-charcoal-100">
                        <div className="px-10 py-2 bg-charcoal-50 text-xs text-charcoal-500 uppercase tracking-wide">
                          {dept.deptProfile ? 'Sub-agencies' : 'Agencies'} ({dept.subAgencies.length})
                        </div>
                      </div>
                      {dept.subAgencies.map(profile => (
                        <div key={profile.id}>
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
                                <ToolRow key={tool.id} tool={tool} indent />
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* All Agencies View (Flat) */}
      {viewMode === 'flat' && (
        <div className="divide-y divide-charcoal-100">
          {filteredProfiles.map(profile => (
            <div key={profile.id}>
              <button
                onClick={() => toggleAgency(profile.id)}
                className="w-full flex items-center gap-3 p-4 hover:bg-cream text-left transition-colors"
              >
                <span className="text-charcoal-400">
                  {profile.tools.length > 0 ? (
                    expandedAgencies.has(profile.id) ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )
                  ) : (
                    <span className="w-5 h-5" />
                  )}
                </span>

                <div className="flex-1">
                  <span className="font-semibold text-charcoal">
                    {profile.abbreviation && (
                      <span className="text-ifp-purple mr-2">{profile.abbreviation}</span>
                    )}
                    {profile.agencyName}
                  </span>
                  {profile.departmentLevelName && profile.departmentLevelName !== profile.agencyName && (
                    <div className="text-sm text-charcoal-500">{profile.departmentLevelName}</div>
                  )}
                </div>

                {profile.tools.length > 0 ? (
                  <div className="flex gap-2">
                    {profile.tools.some(t => t.productType === 'staff_chatbot') && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                        Chatbot
                      </span>
                    )}
                    {profile.tools.some(t => t.productType === 'coding_assistant') && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                        Coding
                      </span>
                    )}
                    {profile.tools.some(t => t.productType === 'document_automation') && (
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                        Doc Auto
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-sm text-charcoal-400 italic">
                    No public tool identified
                  </span>
                )}
              </button>

              {/* Tools */}
              {expandedAgencies.has(profile.id) && profile.tools.length > 0 && (
                <div className="bg-cream-light border-t border-charcoal-100">
                  {profile.tools.map(tool => (
                    <ToolRow key={tool.id} tool={tool} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {(viewMode === 'hierarchy' ? departments.length : filteredProfiles.length) === 0 && (
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

function ToolRow({ tool, indent = false }: { tool: AgencyAiTool; indent?: boolean }) {
  const [showCitation, setShowCitation] = useState(false);

  return (
    <div className={`p-3 border-b border-charcoal-50 last:border-b-0 ${indent ? 'pl-20' : 'pl-16'}`}>
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

        {tool.availableToAllStaff === 'subset' && (
          <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
            Partial Rollout
          </span>
        )}

        <SolutionTypeBadge type={tool.solutionType} />

        {tool.internalOrSensitiveData && tool.internalOrSensitiveData.toLowerCase() === 'yes' && (
          <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full" title="Can be used with internal/sensitive data">
            Internal Data OK
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

function SolutionTypeBadge({ type }: { type: string | null | undefined }) {
  if (!type || type === 'unknown') return null;

  const config: Record<string, { label: string; bg: string; text: string }> = {
    custom: { label: 'Custom Built', bg: 'bg-indigo-100', text: 'text-indigo-700' },
    commercial: { label: 'Commercial', bg: 'bg-teal-100', text: 'text-teal-700' },
    hybrid: { label: 'Hybrid', bg: 'bg-amber-100', text: 'text-amber-700' },
  };

  const { label, bg, text } = config[type] || { label: type, bg: 'bg-charcoal-100', text: 'text-charcoal-500' };

  return (
    <span className={`px-2 py-0.5 text-xs ${bg} ${text} rounded-full font-medium`}>
      {label}
    </span>
  );
}

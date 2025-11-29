'use client';

import React from 'react';
import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChevronDown, ChevronRight, Building2, Landmark, Download, FileSpreadsheet } from 'lucide-react';
import type { AgencyAIUsage } from '@/lib/agency-db';
import type { FederalOrganizationWithAgencies } from '@/lib/hierarchy-db';
import { ViewModeToggle, type ViewMode } from '@/components/hierarchy/ViewModeToggle';

type SortField = 'agency_name' | 'has_staff_llm' | 'has_coding_assistant' | 'solution_type' | 'scope';
type SortDirection = 'asc' | 'desc';
type FilterType = 'all' | 'has_llm' | 'has_coding' | 'custom' | 'commercial';

interface AgencyAITableProps {
  agencies: AgencyAIUsage[];
  hierarchy?: FederalOrganizationWithAgencies[];
}

export default function AgencyAITable({ agencies, hierarchy = [] }: AgencyAITableProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortField, setSortField] = useState<SortField>('agency_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [isInitialized, setIsInitialized] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const filter = searchParams.get('filter') as FilterType || 'all';
    const sort = searchParams.get('sort') as SortField || 'agency_name';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);
    const view = searchParams.get('view') as ViewMode || 'list';

    setSearchQuery(query);
    setFilterType(filter);
    setSortField(sort);
    setSortDirection(dir);
    setCurrentPage(page);
    setItemsPerPage(perPage);
    setViewMode(view);
    setIsInitialized(true);
  }, [searchParams]);

  // Sync state to URL (only after initialization)
  useEffect(() => {
    if (!isInitialized) return;

    const params = new URLSearchParams();
    if (searchQuery) params.set('q', searchQuery);
    if (filterType !== 'all') params.set('filter', filterType);
    if (sortField !== 'agency_name') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());
    if (viewMode !== 'list') params.set('view', viewMode);

    const queryString = params.toString();
    const newUrl = queryString ? `/agency-ai-usage?${queryString}` : '/agency-ai-usage';

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, filterType, sortField, sortDirection, currentPage, itemsPerPage, viewMode, isInitialized, router]);

  // Filter by type
  const filteredByType = useMemo(() => {
    const safeAgencies = agencies || [];
    if (filterType === 'all') return safeAgencies;
    if (filterType === 'has_llm') return safeAgencies.filter((a) => a.has_staff_llm?.includes('Yes'));
    if (filterType === 'has_coding') return safeAgencies.filter((a) => a.has_coding_assistant?.includes('Yes') || a.has_coding_assistant?.includes('Allowed'));
    if (filterType === 'custom') return safeAgencies.filter((a) => a.solution_type?.includes('Custom'));
    if (filterType === 'commercial') return safeAgencies.filter((a) => a.solution_type && (a.solution_type.includes('Azure') || a.solution_type.includes('AWS') || a.solution_type.includes('Commercial')));
    return safeAgencies;
  }, [agencies, filterType]);

  // Filter by search query
  const filteredAgencies = useMemo(() => {
    if (!searchQuery) return filteredByType || [];

    const query = searchQuery.toLowerCase();
    return (filteredByType || []).filter((agency) => {
      return (
        agency.agency_name?.toLowerCase().includes(query) ||
        agency.llm_name?.toLowerCase().includes(query) ||
        agency.solution_type?.toLowerCase().includes(query) ||
        agency.tool_name?.toLowerCase().includes(query) ||
        agency.notes?.toLowerCase().includes(query)
      );
    });
  }, [filteredByType, searchQuery]);

  // Sort agencies
  const sortedAgencies = useMemo(() => {
    const sorted = [...(filteredAgencies || [])];

    sorted.sort((a, b) => {
      let aValue: any = a[sortField] || '';
      let bValue: any = b[sortField] || '';

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredAgencies, sortField, sortDirection]);

  // Filter hierarchy to only show orgs with agencies (considering aggregated stats)
  const filteredHierarchy = useMemo(() => {
    if (viewMode === 'list') return [];

    // Filter hierarchy based on current filter type
    function filterOrg(org: FederalOrganizationWithAgencies): FederalOrganizationWithAgencies | null {
      // Filter agencies at this level
      const filteredAgencies = org.agencies.filter(agency => {
        // First apply search filter
        if (searchQuery) {
          const query = searchQuery.toLowerCase();
          const matchesSearch =
            agency.agencyName?.toLowerCase().includes(query) ||
            agency.llmName?.toLowerCase().includes(query) ||
            agency.solutionType?.toLowerCase().includes(query);
          if (!matchesSearch) return false;
        }

        // Then apply type filter
        if (filterType === 'all') return true;
        if (filterType === 'has_llm') return agency.hasStaffLlm?.includes('Yes');
        if (filterType === 'has_coding') return agency.hasCodingAssistant?.includes('Yes') || agency.hasCodingAssistant?.includes('Allowed');
        if (filterType === 'custom') return agency.solutionType?.includes('Custom');
        if (filterType === 'commercial') return agency.solutionType && (agency.solutionType.includes('Azure') || agency.solutionType.includes('AWS') || agency.solutionType.includes('Commercial'));
        return true;
      });

      // Recursively filter children
      const filteredChildren = org.children
        .map(child => filterOrg(child))
        .filter((child): child is FederalOrganizationWithAgencies => child !== null);

      // Calculate new aggregated stats
      const aggregatedStats = {
        agencyCount: filteredAgencies.length,
        withLlm: filteredAgencies.filter(a => a.hasStaffLlm?.includes('Yes')).length,
        withCoding: filteredAgencies.filter(a => a.hasCodingAssistant?.includes('Yes') || a.hasCodingAssistant?.includes('Allowed')).length,
      };

      // Add child stats
      for (const child of filteredChildren) {
        aggregatedStats.agencyCount += child.aggregatedStats.agencyCount;
        aggregatedStats.withLlm += child.aggregatedStats.withLlm;
        aggregatedStats.withCoding += child.aggregatedStats.withCoding;
      }

      // Only include if there are agencies (directly or in children)
      if (aggregatedStats.agencyCount === 0) return null;

      return {
        ...org,
        agencies: filteredAgencies,
        children: filteredChildren,
        aggregatedStats,
      };
    }

    return hierarchy
      .map(org => filterOrg(org))
      .filter((org): org is FederalOrganizationWithAgencies => org !== null);
  }, [hierarchy, viewMode, filterType, searchQuery]);

  // Toggle group expansion
  const toggleGroup = (groupKey: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  };

  // Get all org keys from hierarchy recursively
  const getAllOrgKeys = (orgs: FederalOrganizationWithAgencies[]): string[] => {
    const keys: string[] = [];
    for (const org of orgs) {
      keys.push(org.abbreviation || org.name);
      keys.push(...getAllOrgKeys(org.children));
    }
    return keys;
  };

  // Expand all groups
  const expandAllGroups = () => {
    const allKeys = getAllOrgKeys(filteredHierarchy);
    setExpandedGroups(new Set(allKeys));
  };

  // Collapse all groups
  const collapseAllGroups = () => {
    setExpandedGroups(new Set());
  };

  // Pagination
  const totalPages = Math.ceil(sortedAgencies.length / itemsPerPage);
  const paginatedAgencies = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedAgencies.slice(start, start + itemsPerPage);
  }, [sortedAgencies, currentPage, itemsPerPage]);

  // Handle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Reset to page 1 when search changes
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  const handleFilterChange = (type: FilterType) => {
    setFilterType(type);
    setCurrentPage(1);
  };

  // Export full data as CSV
  const exportFullDataCSV = () => {
    const headers = [
      'ID',
      'Agency Name',
      'Agency Category',
      'Has Staff LLM',
      'LLM Name',
      'Has Coding Assistant',
      'Scope',
      'Solution Type',
      'Non-Public Allowed',
      'Other AI Present',
      'Tool Name',
      'Tool Purpose',
      'Notes',
      'Sources',
      'Organization ID',
      'Analyzed At',
      'Slug'
    ];

    const rows = agencies.map(a => [
      a.id.toString(),
      a.agency_name || '',
      a.agency_category || '',
      a.has_staff_llm || '',
      a.llm_name || '',
      a.has_coding_assistant || '',
      a.scope || '',
      a.solution_type || '',
      a.non_public_allowed || '',
      a.other_ai_present || '',
      a.tool_name || '',
      a.tool_purpose || '',
      a.notes || '',
      a.sources || '',
      a.organization_id?.toString() || '',
      a.analyzed_at ? new Date(a.analyzed_at).toISOString() : '',
      a.slug || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    downloadFile(csvContent, 'text/csv', `agency-ai-usage-full-data-${new Date().toISOString().split('T')[0]}.csv`);
  };

  // Export full data as Excel
  const exportFullDataExcel = () => {
    const headers = [
      'ID',
      'Agency Name',
      'Agency Category',
      'Has Staff LLM',
      'LLM Name',
      'Has Coding Assistant',
      'Scope',
      'Solution Type',
      'Non-Public Allowed',
      'Other AI Present',
      'Tool Name',
      'Tool Purpose',
      'Notes',
      'Sources',
      'Organization ID',
      'Analyzed At',
      'Slug'
    ];

    const rows = agencies.map(a => [
      a.id.toString(),
      a.agency_name || '',
      a.agency_category || '',
      a.has_staff_llm || '',
      a.llm_name || '',
      a.has_coding_assistant || '',
      a.scope || '',
      a.solution_type || '',
      a.non_public_allowed || '',
      a.other_ai_present || '',
      a.tool_name || '',
      a.tool_purpose || '',
      a.notes || '',
      a.sources || '',
      a.organization_id?.toString() || '',
      a.analyzed_at ? new Date(a.analyzed_at).toISOString() : '',
      a.slug || '',
    ]);

    const tsvContent = [
      headers.join('\t'),
      ...rows.map(row => row.map(cell => String(cell).replace(/\t/g, ' ').replace(/\n/g, ' ')).join('\t'))
    ].join('\n');

    downloadFile(tsvContent, 'application/vnd.ms-excel', `agency-ai-usage-full-data-${new Date().toISOString().split('T')[0]}.xls`);
  };

  function downloadFile(content: string, mimeType: string, filename: string) {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Render agency row from hierarchy data (for grouped view)
  const renderHierarchyAgencyRow = (agency: FederalOrganizationWithAgencies['agencies'][0], index: number, depth: number = 1) => (
    <tr
      key={`agency-${agency.id}`}
      onClick={() => router.push(`/agency-ai-usage/${agency.slug}`)}
      className={`cursor-pointer hover:bg-cream-200 hover:border-l-4 hover:border-charcoal-600 transition-all bg-cream`}
    >
      <td className="px-4 py-3 text-sm font-medium text-charcoal" style={{ paddingLeft: `${1 + depth * 1.5}rem` }}>
        <div className="max-w-xs" title={agency.agencyName}>
          {agency.agencyName}
        </div>
      </td>
      <td className="px-4 py-3 text-sm">
        {agency.hasStaffLlm?.includes('Yes') ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
            Yes
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-cream-200 text-charcoal-600 border border-charcoal-300">
            No
          </span>
        )}
        {agency.llmName && (
          <div className="text-xs text-charcoal-600 mt-1">{agency.llmName}</div>
        )}
      </td>
      <td className="px-4 py-3 text-sm">
        {agency.hasCodingAssistant?.includes('Yes') || agency.hasCodingAssistant?.includes('Allowed') ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
            Yes
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-cream-200 text-charcoal-600 border border-charcoal-300">
            No
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-charcoal-600">
        <div className="max-w-sm truncate" title={agency.solutionType || 'N/A'}>
          {agency.solutionType || 'N/A'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-charcoal-600">
        <div className="max-w-xs truncate">N/A</div>
      </td>
      <td className="px-4 py-3 text-sm">
        <Link
          href={`/agency-ai-usage/${agency.slug}`}
          onClick={(e) => e.stopPropagation()}
          className="text-charcoal-700 hover:text-charcoal font-medium underline"
        >
          View Details →
        </Link>
      </td>
    </tr>
  );

  // Render organization row with nested children (recursive)
  const renderOrgRow = (org: FederalOrganizationWithAgencies, depth: number = 0): React.ReactNode => {
    const groupKey = org.abbreviation || org.name;
    const isExpanded = expandedGroups.has(groupKey);
    const { aggregatedStats } = org;
    const hasDirectAgencies = org.agencies.length > 0;
    const hasChildren = org.children.length > 0;
    const isDepartment = org.level === 'department';

    return (
      <React.Fragment key={`org-${org.id}`}>
        {/* Organization Header Row */}
        <tr
          onClick={() => toggleGroup(groupKey)}
          className={`${isDepartment ? 'bg-cream-200' : 'bg-cream'} hover:bg-cream-200 cursor-pointer border-b border-charcoal-200`}
        >
          <td colSpan={6} className="px-4 py-3" style={{ paddingLeft: `${1 + depth * 1.5}rem` }}>
            <div className="flex items-center gap-3">
              {(hasDirectAgencies || hasChildren) && (
                <button className="p-0.5 rounded hover:bg-charcoal-200">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-charcoal-600" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-charcoal-600" />
                  )}
                </button>
              )}
              <div className="flex items-center gap-2">
                {isDepartment ? (
                  <Landmark className="w-4 h-4 text-charcoal-600" />
                ) : (
                  <Building2 className="w-4 h-4 text-cream-1000" />
                )}
                <span className={`font-semibold ${isDepartment ? 'text-charcoal' : 'text-charcoal-800'}`}>
                  {org.abbreviation || org.name}
                </span>
                {org.abbreviation && (
                  <span className="text-sm text-charcoal-600">
                    - {org.name}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-sm text-charcoal-600">
                  {aggregatedStats.agencyCount} {aggregatedStats.agencyCount === 1 ? 'agency' : 'agencies'}
                </span>
                {aggregatedStats.withLlm > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark">
                    {aggregatedStats.withLlm} LLM
                  </span>
                )}
                {aggregatedStats.withCoding > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark">
                    {aggregatedStats.withCoding} Coding
                  </span>
                )}
              </div>
            </div>
          </td>
        </tr>
        {/* Expanded Content */}
        {isExpanded && (
          <>
            {/* Direct agencies at this level */}
            {org.agencies.map((agency, index) =>
              renderHierarchyAgencyRow(agency, index, depth + 1)
            )}
            {/* Child organizations (recursive) */}
            {org.children.map(child => renderOrgRow(child, depth + 1))}
          </>
        )}
      </React.Fragment>
    );
  };

  // Render agency row (used in both list and grouped views)
  const renderAgencyRow = (agency: AgencyAIUsage, index: number, isNested: boolean = false) => (
    <tr
      key={agency.id}
      onClick={() => router.push(`/agency-ai-usage/${agency.slug}`)}
      className={`cursor-pointer hover:bg-cream-200 hover:border-l-4 hover:border-charcoal-600 transition-all ${
        isNested ? 'bg-cream' : (index % 2 === 0 ? 'bg-white' : 'bg-cream/30')
      }`}
    >
      <td className={`px-4 py-3 text-sm font-medium text-charcoal ${isNested ? 'pl-10' : ''}`}>
        <div className="max-w-xs" title={agency.agency_name}>
          {agency.agency_name}
        </div>
      </td>
      <td className="px-4 py-3 text-sm">
        {agency.has_staff_llm?.includes('Yes') ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
            Yes
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-cream-200 text-charcoal-600 border border-charcoal-300">
            No
          </span>
        )}
        {agency.llm_name && (
          <div className="text-xs text-charcoal-600 mt-1">{agency.llm_name}</div>
        )}
      </td>
      <td className="px-4 py-3 text-sm">
        {agency.has_coding_assistant?.includes('Yes') || agency.has_coding_assistant?.includes('Allowed') ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
            Yes
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-cream-200 text-charcoal-600 border border-charcoal-300">
            No
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-charcoal-600">
        <div className="max-w-sm truncate" title={agency.solution_type || 'N/A'}>
          {agency.solution_type || 'N/A'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-charcoal-600">
        <div className="max-w-xs truncate" title={agency.scope || 'N/A'}>
          {agency.scope || 'N/A'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm">
        <Link
          href={`/agency-ai-usage/${agency.slug}`}
          onClick={(e) => e.stopPropagation()}
          className="text-charcoal-700 hover:text-charcoal font-medium underline"
        >
          View Details →
        </Link>
      </td>
    </tr>
  );

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <div className="bg-white rounded-lg border border-charcoal-200 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'all'
                  ? 'bg-charcoal-700 text-white border-charcoal-700'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              All ({agencies.length})
            </button>
            <button
              onClick={() => handleFilterChange('has_llm')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'has_llm'
                  ? 'bg-ifp-purple text-white border-ifp-purple'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              Has LLM ({agencies.filter((a) => a.has_staff_llm?.includes('Yes')).length})
            </button>
            <button
              onClick={() => handleFilterChange('has_coding')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'has_coding'
                  ? 'bg-ifp-orange text-white border-ifp-orange'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              Has Coding ({agencies.filter((a) => a.has_coding_assistant?.includes('Yes') || a.has_coding_assistant?.includes('Allowed')).length})
            </button>
            <button
              onClick={() => handleFilterChange('custom')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'custom'
                  ? 'bg-charcoal-500 text-white border-charcoal-500'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              Custom ({agencies.filter((a) => a.solution_type?.includes('Custom')).length})
            </button>
          </div>

          {/* Search Box */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search agencies..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-cream-1000 focus:border-transparent"
            />
          </div>

          {/* Items Per Page (only for list view) */}
          {viewMode === 'list' && (
            <div className="flex items-center">
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-cream-1000"
              >
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
                <option value={100}>100 per page</option>
                <option value={999999}>All</option>
              </select>
            </div>
          )}

          {/* Export Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={exportFullDataCSV}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-charcoal-700 bg-white border border-charcoal-300 rounded-md hover:bg-cream transition-colors"
              title="Export all data as CSV"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={exportFullDataExcel}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-charcoal-700 bg-white border border-charcoal-300 rounded-md hover:bg-cream transition-colors"
              title="Export all data as Excel"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Excel
            </button>
          </div>
        </div>

        {/* View Mode Toggle and Stats */}
        <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="text-sm text-charcoal-600">
            {viewMode === 'list' ? (
              <>
                Showing {paginatedAgencies.length} of {filteredAgencies.length} agencies
                {searchQuery && ` (filtered from ${filteredByType.length} total)`}
              </>
            ) : (
              <>
                {filteredHierarchy.length} top-level orgs, {filteredHierarchy.reduce((sum, org) => sum + org.aggregatedStats.agencyCount, 0)} agencies total
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            {viewMode !== 'list' && (
              <div className="flex gap-2">
                <button
                  onClick={expandAllGroups}
                  className="text-xs text-charcoal-600 hover:text-charcoal underline"
                >
                  Expand All
                </button>
                <button
                  onClick={collapseAllGroups}
                  className="text-xs text-charcoal-600 hover:text-charcoal underline"
                >
                  Collapse All
                </button>
              </div>
            )}
            <ViewModeToggle
              currentMode={viewMode}
              onModeChange={setViewMode}
              availableModes={['list', 'grouped']}
              size="sm"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cream-200 border-b-2 border-charcoal-200">
              <tr>
                <th
                  onClick={() => handleSort('agency_name')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Agency</span>
                    {sortField === 'agency_name' && (
                      <span className="text-charcoal-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('has_staff_llm')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Staff LLM</span>
                    {sortField === 'has_staff_llm' && (
                      <span className="text-charcoal-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('has_coding_assistant')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Coding Assistant</span>
                    {sortField === 'has_coding_assistant' && (
                      <span className="text-charcoal-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('solution_type')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Solution Type</span>
                    {sortField === 'solution_type' && (
                      <span className="text-charcoal-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('scope')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Scope</span>
                    {sortField === 'scope' && (
                      <span className="text-charcoal-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-charcoal-200">
              {viewMode === 'list' ? (
                // List View - flat table with pagination
                paginatedAgencies.map((agency, index) => renderAgencyRow(agency, index, false))
              ) : (
                // Grouped View - show agencies grouped by organization hierarchy
                filteredHierarchy.map(org => renderOrgRow(org, 0))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination (only for list view) */}
        {viewMode === 'list' && totalPages > 1 && (
          <div className="p-4 bg-cream border-t border-charcoal-200 flex items-center justify-between">
            <div className="text-sm text-charcoal-600">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-white border border-charcoal-300 rounded-md text-sm font-medium text-charcoal hover:bg-cream disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-white border border-charcoal-300 rounded-md text-sm font-medium text-charcoal hover:bg-cream disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

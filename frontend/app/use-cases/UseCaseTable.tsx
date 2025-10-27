'use client';

import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { UseCase } from '@/lib/use-case-db';

type SortField = 'use_case_name' | 'agency' | 'domain_category' | 'stage_of_development' | 'date_implemented';
type SortDirection = 'asc' | 'desc';
type AITypeFilter = 'all' | 'genai' | 'llm' | 'chatbot' | 'classic_ml' | 'coding' | 'rpa';
type DomainFilter = string;

interface UseCaseTableProps {
  useCases: UseCase[];
  domains: string[];
  agencies: string[];
  stages: string[];
}

export default function UseCaseTable({ useCases, domains, agencies, stages }: UseCaseTableProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState('');
  const [aiTypeFilter, setAITypeFilter] = useState<AITypeFilter>('all');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [agencyFilter, setAgencyFilter] = useState<string>('all');
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('agency');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const aiType = searchParams.get('aiType') as AITypeFilter || 'all';
    const domain = searchParams.get('domain') || 'all';
    const agency = searchParams.get('agency') || 'all';
    const stage = searchParams.get('stage') || 'all';
    const sort = searchParams.get('sort') as SortField || 'agency';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);

    setSearchQuery(query);
    setAITypeFilter(aiType);
    setDomainFilter(domain);
    setAgencyFilter(agency);
    setStageFilter(stage);
    setSortField(sort);
    setSortDirection(dir);
    setCurrentPage(page);
    setItemsPerPage(perPage);
    setIsInitialized(true);
  }, [searchParams]);

  // Sync state to URL
  useEffect(() => {
    if (!isInitialized) return;

    const params = new URLSearchParams();
    if (searchQuery) params.set('q', searchQuery);
    if (aiTypeFilter !== 'all') params.set('aiType', aiTypeFilter);
    if (domainFilter !== 'all') params.set('domain', domainFilter);
    if (agencyFilter !== 'all') params.set('agency', agencyFilter);
    if (stageFilter !== 'all') params.set('stage', stageFilter);
    if (sortField !== 'agency') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());

    const queryString = params.toString();
    const newUrl = queryString ? `/use-cases?${queryString}` : '/use-cases';

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, aiTypeFilter, domainFilter, agencyFilter, stageFilter, sortField, sortDirection, currentPage, itemsPerPage, isInitialized, router]);

  // Parse providers for display
  const parseProviders = (providersJson: string): string[] => {
    try {
      return JSON.parse(providersJson);
    } catch {
      return [];
    }
  };

  // Filter by AI type
  const filteredByAIType = useMemo(() => {
    if (aiTypeFilter === 'all') return useCases;

    return useCases.filter(uc => {
      switch (aiTypeFilter) {
        case 'genai': return uc.genai_flag;
        case 'llm': return uc.has_llm;
        case 'chatbot': return uc.has_chatbot;
        case 'classic_ml': return uc.has_classic_ml;
        case 'coding': return uc.has_coding_assistant || uc.has_coding_agent;
        case 'rpa': return uc.has_rpa;
        default: return true;
      }
    });
  }, [useCases, aiTypeFilter]);

  // Filter by domain
  const filteredByDomain = useMemo(() => {
    if (domainFilter === 'all') return filteredByAIType;
    return filteredByAIType.filter(uc => uc.domain_category === domainFilter);
  }, [filteredByAIType, domainFilter]);

  // Filter by agency
  const filteredByAgency = useMemo(() => {
    if (agencyFilter === 'all') return filteredByDomain;
    return filteredByDomain.filter(uc => uc.agency === agencyFilter);
  }, [filteredByDomain, agencyFilter]);

  // Filter by stage
  const filteredByStage = useMemo(() => {
    if (stageFilter === 'all') return filteredByAgency;
    return filteredByAgency.filter(uc => uc.stage_of_development === stageFilter);
  }, [filteredByAgency, stageFilter]);

  // Filter by search query
  const filteredUseCases = useMemo(() => {
    if (!searchQuery) return filteredByStage;

    const query = searchQuery.toLowerCase();
    return filteredByStage.filter(uc =>
      uc.use_case_name?.toLowerCase().includes(query) ||
      uc.agency?.toLowerCase().includes(query) ||
      uc.bureau?.toLowerCase().includes(query) ||
      uc.intended_purpose?.toLowerCase().includes(query)
    );
  }, [filteredByStage, searchQuery]);

  // Sort use cases
  const sortedUseCases = useMemo(() => {
    const sorted = [...filteredUseCases];

    sorted.sort((a, b) => {
      let aValue: any = a[sortField] || '';
      let bValue: any = b[sortField] || '';

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredUseCases, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(sortedUseCases.length / itemsPerPage);
  const paginatedUseCases = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedUseCases.slice(start, start + itemsPerPage);
  }, [sortedUseCases, currentPage, itemsPerPage]);

  // Handle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Reset to page 1 when filters change
  const handleFilterChange = () => {
    setCurrentPage(1);
  };

  // Get AI type badges for a use case
  const getAITypeBadges = (uc: UseCase) => {
    const badges = [];

    if (uc.genai_flag) {
      badges.push(
        <span key="genai" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-teal-light text-ai-teal-dark border border-ai-teal">
          GenAI
        </span>
      );
    }
    if (uc.has_llm) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-indigo-light text-ai-indigo-dark border border-ai-indigo">
          LLM
        </span>
      );
    }
    if (uc.has_chatbot) {
      badges.push(
        <span key="chatbot" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ai-blue-light text-ai-blue-dark border border-ai-blue">
          Chatbot
        </span>
      );
    }
    if (uc.has_classic_ml) {
      badges.push(
        <span key="ml" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gov-slate-200 text-gov-slate-700 border border-gov-slate-400">
          ML
        </span>
      );
    }
    if (uc.has_coding_assistant || uc.has_coding_agent) {
      badges.push(
        <span key="coding" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
          Coding
        </span>
      );
    }
    if (uc.has_rpa) {
      badges.push(
        <span key="rpa" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-warning-light text-status-warning-dark border border-status-warning">
          RPA
        </span>
      );
    }

    return badges.length > 0 ? badges : [
      <span key="other" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300">
        Other AI
      </span>
    ];
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg border border-gov-slate-200 p-4">
        <div className="flex flex-col gap-4">
          {/* AI Type Filter Buttons */}
          <div>
            <label className="text-xs font-semibold text-gov-slate-600 mb-2 block">AI TYPE</label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { setAITypeFilter('all'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'all'
                    ? 'bg-gov-navy-700 text-white border-gov-navy-700'
                    : 'bg-white text-gov-navy-900 border-gov-slate-300 hover:bg-gov-slate-50'
                }`}
              >
                All ({useCases.length})
              </button>
              <button
                onClick={() => { setAITypeFilter('genai'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'genai'
                    ? 'bg-ai-teal text-white border-ai-teal'
                    : 'bg-white text-gov-navy-900 border-gov-slate-300 hover:bg-gov-slate-50'
                }`}
              >
                GenAI ({useCases.filter(uc => uc.genai_flag).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('llm'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'llm'
                    ? 'bg-ai-indigo text-white border-ai-indigo'
                    : 'bg-white text-gov-navy-900 border-gov-slate-300 hover:bg-gov-slate-50'
                }`}
              >
                LLM ({useCases.filter(uc => uc.has_llm).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('chatbot'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'chatbot'
                    ? 'bg-ai-blue text-white border-ai-blue'
                    : 'bg-white text-gov-navy-900 border-gov-slate-300 hover:bg-gov-slate-50'
                }`}
              >
                Chatbot ({useCases.filter(uc => uc.has_chatbot).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('classic_ml'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'classic_ml'
                    ? 'bg-gov-slate-600 text-white border-gov-slate-600'
                    : 'bg-white text-gov-navy-900 border-gov-slate-300 hover:bg-gov-slate-50'
                }`}
              >
                Classic ML ({useCases.filter(uc => uc.has_classic_ml).length})
              </button>
            </div>
          </div>

          {/* Dropdown Filters and Search */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Domain Filter */}
            <div>
              <label className="text-xs font-semibold text-gov-slate-600 mb-1 block">DOMAIN</label>
              <select
                value={domainFilter}
                onChange={(e) => { setDomainFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gov-slate-300 rounded-md text-sm focus:ring-2 focus:ring-gov-navy-500"
              >
                <option value="all">All Domains</option>
                {domains.map(domain => (
                  <option key={domain} value={domain}>{domain}</option>
                ))}
              </select>
            </div>

            {/* Agency Filter */}
            <div>
              <label className="text-xs font-semibold text-gov-slate-600 mb-1 block">AGENCY</label>
              <select
                value={agencyFilter}
                onChange={(e) => { setAgencyFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gov-slate-300 rounded-md text-sm focus:ring-2 focus:ring-gov-navy-500"
              >
                <option value="all">All Agencies</option>
                {agencies.slice(0, 20).map(agency => (
                  <option key={agency} value={agency}>{agency}</option>
                ))}
              </select>
            </div>

            {/* Stage Filter */}
            <div>
              <label className="text-xs font-semibold text-gov-slate-600 mb-1 block">STAGE</label>
              <select
                value={stageFilter}
                onChange={(e) => { setStageFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-gov-slate-300 rounded-md text-sm focus:ring-2 focus:ring-gov-navy-500"
              >
                <option value="all">All Stages</option>
                {stages.map(stage => (
                  <option key={stage} value={stage}>{stage}</option>
                ))}
              </select>
            </div>

            {/* Items Per Page */}
            <div>
              <label className="text-xs font-semibold text-gov-slate-600 mb-1 block">PER PAGE</label>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gov-slate-300 rounded-md text-sm focus:ring-2 focus:ring-gov-navy-500"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={999999}>All</option>
              </select>
            </div>
          </div>

          {/* Search Box */}
          <div>
            <label className="text-xs font-semibold text-gov-slate-600 mb-1 block">SEARCH</label>
            <input
              type="text"
              placeholder="Search use cases by name, agency, bureau, or purpose..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full px-4 py-2 border border-gov-slate-300 rounded-md focus:ring-2 focus:ring-gov-navy-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="mt-3 text-sm text-gov-slate-600">
          Showing {paginatedUseCases.length} of {filteredUseCases.length} use cases
          {filteredUseCases.length < useCases.length && ` (filtered from ${useCases.length} total)`}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gov-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gov-slate-100 border-b-2 border-gov-slate-200">
              <tr>
                <th
                  onClick={() => handleSort('use_case_name')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Use Case</span>
                    {sortField === 'use_case_name' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('agency')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Agency</span>
                    {sortField === 'agency' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('domain_category')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Domain</span>
                    {sortField === 'domain_category' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900">
                  AI Type
                </th>
                <th
                  onClick={() => handleSort('stage_of_development')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Stage</span>
                    {sortField === 'stage_of_development' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gov-slate-200">
              {paginatedUseCases.map((uc, index) => (
                <tr
                  key={uc.id}
                  onClick={() => router.push(`/use-cases/${uc.slug}`)}
                  className={`cursor-pointer hover:bg-gov-slate-100 hover:border-l-4 hover:border-gov-navy-600 transition-all ${index % 2 === 0 ? 'bg-white' : 'bg-gov-slate-50/30'}`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-gov-navy-900">
                    <div className="max-w-md" title={uc.use_case_name}>
                      {uc.use_case_name}
                    </div>
                    {uc.bureau && (
                      <div className="text-xs text-gov-slate-600 mt-1">{uc.bureau}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="max-w-xs truncate" title={uc.agency}>
                      {uc.agency}
                    </div>
                    {uc.agency_abbreviation && (
                      <div className="text-xs text-gov-slate-600 mt-1">{uc.agency_abbreviation}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gov-slate-700">
                    <div className="max-w-xs truncate" title={uc.domain_category || 'N/A'}>
                      {uc.domain_category || 'Unclassified'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex flex-wrap gap-1">
                      {getAITypeBadges(uc)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gov-slate-700">
                    <div className="max-w-xs truncate" title={uc.stage_of_development || 'N/A'}>
                      {uc.stage_of_development || 'N/A'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/use-cases/${uc.slug}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-gov-navy-700 hover:text-gov-navy-900 font-medium underline"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 bg-gov-slate-50 border-t border-gov-slate-200 flex items-center justify-between">
            <div className="text-sm text-gov-slate-600">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-white border border-gov-slate-300 rounded-md text-sm font-medium text-gov-navy-900 hover:bg-gov-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-white border border-gov-slate-300 rounded-md text-sm font-medium text-gov-navy-900 hover:bg-gov-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
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

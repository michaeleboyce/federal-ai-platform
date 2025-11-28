'use client';

import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { UseCase } from '@/lib/use-case-db';

type SortField = 'useCaseName' | 'agency' | 'domainCategory' | 'stageOfDevelopment' | 'dateImplemented';
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
        case 'genai': return uc.genaiFlag;
        case 'llm': return uc.hasLlm;
        case 'chatbot': return uc.hasChatbot;
        case 'classic_ml': return uc.hasClassicMl;
        case 'coding': return uc.hasCodingAssistant || uc.hasCodingAgent;
        case 'rpa': return uc.hasRpa;
        default: return true;
      }
    });
  }, [useCases, aiTypeFilter]);

  // Filter by domain
  const filteredByDomain = useMemo(() => {
    if (domainFilter === 'all') return filteredByAIType;
    return filteredByAIType.filter(uc => uc.domainCategory === domainFilter);
  }, [filteredByAIType, domainFilter]);

  // Filter by agency
  const filteredByAgency = useMemo(() => {
    if (agencyFilter === 'all') return filteredByDomain;
    return filteredByDomain.filter(uc => uc.agency === agencyFilter);
  }, [filteredByDomain, agencyFilter]);

  // Filter by stage
  const filteredByStage = useMemo(() => {
    if (stageFilter === 'all') return filteredByAgency;
    return filteredByAgency.filter(uc => uc.stageOfDevelopment === stageFilter);
  }, [filteredByAgency, stageFilter]);

  // Filter by search query
  const filteredUseCases = useMemo(() => {
    if (!searchQuery) return filteredByStage;

    const query = searchQuery.toLowerCase();
    return filteredByStage.filter(uc =>
      uc.useCaseName?.toLowerCase().includes(query) ||
      uc.agency?.toLowerCase().includes(query) ||
      uc.bureau?.toLowerCase().includes(query) ||
      uc.intendedPurpose?.toLowerCase().includes(query)
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

    if (uc.genaiFlag) {
      badges.push(
        <span key="genai" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
          GenAI
        </span>
      );
    }
    if (uc.hasLlm) {
      badges.push(
        <span key="llm" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
          LLM
        </span>
      );
    }
    if (uc.hasChatbot) {
      badges.push(
        <span key="chatbot" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
          Chatbot
        </span>
      );
    }
    if (uc.hasClassicMl) {
      badges.push(
        <span key="ml" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-200 text-charcoal-700 border border-charcoal-400">
          ML
        </span>
      );
    }
    if (uc.hasCodingAssistant || uc.hasCodingAgent) {
      badges.push(
        <span key="coding" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-success-light text-status-success-dark border border-status-success">
          Coding
        </span>
      );
    }
    if (uc.hasRpa) {
      badges.push(
        <span key="rpa" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-status-warning-light text-status-warning-dark border border-status-warning">
          RPA
        </span>
      );
    }

    return badges.length > 0 ? badges : [
      <span key="other" className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-600 border border-charcoal-300">
        Other AI
      </span>
    ];
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg border border-charcoal-200 p-4">
        <div className="flex flex-col gap-4">
          {/* AI Type Filter Buttons */}
          <div>
            <label className="text-xs font-semibold text-charcoal-500 mb-2 block">AI TYPE</label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { setAITypeFilter('all'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'all'
                    ? 'bg-charcoal-700 text-cream border-charcoal-700'
                    : 'bg-white text-charcoal border-charcoal-300 hover:bg-charcoal-50'
                }`}
              >
                All ({useCases.length})
              </button>
              <button
                onClick={() => { setAITypeFilter('genai'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'genai'
                    ? 'bg-ifp-orange text-white border-ifp-orange'
                    : 'bg-white text-charcoal border-charcoal-300 hover:bg-charcoal-50'
                }`}
              >
                GenAI ({useCases.filter(uc => uc.genaiFlag).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('llm'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'llm'
                    ? 'bg-charcoal-600 text-white border-charcoal-600'
                    : 'bg-white text-charcoal border-charcoal-300 hover:bg-charcoal-50'
                }`}
              >
                LLM ({useCases.filter(uc => uc.hasLlm).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('chatbot'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'chatbot'
                    ? 'bg-ifp-purple text-white border-ifp-purple'
                    : 'bg-white text-charcoal border-charcoal-300 hover:bg-charcoal-50'
                }`}
              >
                Chatbot ({useCases.filter(uc => uc.hasChatbot).length})
              </button>
              <button
                onClick={() => { setAITypeFilter('classic_ml'); handleFilterChange(); }}
                className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                  aiTypeFilter === 'classic_ml'
                    ? 'bg-charcoal-500 text-white border-charcoal-500'
                    : 'bg-white text-charcoal border-charcoal-300 hover:bg-charcoal-50'
                }`}
              >
                Classic ML ({useCases.filter(uc => uc.hasClassicMl).length})
              </button>
            </div>
          </div>

          {/* Dropdown Filters and Search */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Domain Filter */}
            <div>
              <label className="text-xs font-semibold text-charcoal-500 mb-1 block">DOMAIN</label>
              <select
                value={domainFilter}
                onChange={(e) => { setDomainFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-charcoal-300 rounded-md text-sm focus:ring-2 focus:ring-ifp-purple"
              >
                <option value="all">All Domains</option>
                {domains.map(domain => (
                  <option key={domain} value={domain}>{domain}</option>
                ))}
              </select>
            </div>

            {/* Agency Filter */}
            <div>
              <label className="text-xs font-semibold text-charcoal-500 mb-1 block">AGENCY</label>
              <select
                value={agencyFilter}
                onChange={(e) => { setAgencyFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-charcoal-300 rounded-md text-sm focus:ring-2 focus:ring-ifp-purple"
              >
                <option value="all">All Agencies</option>
                {agencies.slice(0, 20).map(agency => (
                  <option key={agency} value={agency}>{agency}</option>
                ))}
              </select>
            </div>

            {/* Stage Filter */}
            <div>
              <label className="text-xs font-semibold text-charcoal-500 mb-1 block">STAGE</label>
              <select
                value={stageFilter}
                onChange={(e) => { setStageFilter(e.target.value); handleFilterChange(); }}
                className="w-full px-3 py-2 border border-charcoal-300 rounded-md text-sm focus:ring-2 focus:ring-ifp-purple"
              >
                <option value="all">All Stages</option>
                {stages.map(stage => (
                  <option key={stage} value={stage}>{stage}</option>
                ))}
              </select>
            </div>

            {/* Items Per Page */}
            <div>
              <label className="text-xs font-semibold text-charcoal-500 mb-1 block">PER PAGE</label>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-charcoal-300 rounded-md text-sm focus:ring-2 focus:ring-ifp-purple"
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
            <label className="text-xs font-semibold text-charcoal-500 mb-1 block">SEARCH</label>
            <input
              type="text"
              placeholder="Search use cases by name, agency, bureau, or purpose..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
            />
          </div>
        </div>

        <div className="mt-3 text-sm text-charcoal-500">
          Showing {paginatedUseCases.length} of {filteredUseCases.length} use cases
          {filteredUseCases.length < useCases.length && ` (filtered from ${useCases.length} total)`}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-charcoal-100 border-b-2 border-charcoal-200">
              <tr>
                <th
                  onClick={() => handleSort('useCaseName')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Use Case</span>
                    {sortField === 'useCaseName' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('agency')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Agency</span>
                    {sortField === 'agency' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('domainCategory')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Domain</span>
                    {sortField === 'domainCategory' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  AI Type
                </th>
                <th
                  onClick={() => handleSort('stageOfDevelopment')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Stage</span>
                    {sortField === 'stageOfDevelopment' && (
                      <span className="text-ifp-purple">
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
              {paginatedUseCases.map((uc, index) => (
                <tr
                  key={uc.id}
                  onClick={() => router.push(`/use-cases/${uc.slug}`)}
                  className={`cursor-pointer hover:bg-charcoal-50 hover:border-l-4 hover:border-ifp-purple transition-all ${index % 2 === 0 ? 'bg-white' : 'bg-charcoal-50/30'}`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-charcoal">
                    <div className="max-w-md" title={uc.useCaseName}>
                      {uc.useCaseName}
                    </div>
                    {uc.bureau && (
                      <div className="text-xs text-charcoal-500 mt-1">{uc.bureau}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="max-w-xs truncate" title={uc.agency}>
                      {uc.agency}
                    </div>
                    {uc.agencyAbbreviation && (
                      <div className="text-xs text-charcoal-500 mt-1">{uc.agencyAbbreviation}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    <div className="max-w-xs truncate" title={uc.domainCategory || 'N/A'}>
                      {uc.domainCategory || 'Unclassified'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex flex-wrap gap-1">
                      {getAITypeBadges(uc)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    <div className="max-w-xs truncate" title={uc.stageOfDevelopment || 'N/A'}>
                      {uc.stageOfDevelopment || 'N/A'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/use-cases/${uc.slug}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-ifp-purple hover:text-ifp-purple-dark font-medium underline"
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
          <div className="p-4 bg-charcoal-50 border-t border-charcoal-200 flex items-center justify-between">
            <div className="text-sm text-charcoal-500">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-white border border-charcoal-300 rounded-md text-sm font-medium text-charcoal hover:bg-charcoal-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-white border border-charcoal-300 rounded-md text-sm font-medium text-charcoal hover:bg-charcoal-50 disabled:opacity-50 disabled:cursor-not-allowed"
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

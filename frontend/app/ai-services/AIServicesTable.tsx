'use client';

import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { AIService } from '@/lib/ai-db';

type SortField = 'provider_name' | 'product_name' | 'service_name' | 'fedramp_status' | 'impact_level' | 'auth_date';
type SortDirection = 'asc' | 'desc';
type FilterType = 'all' | 'ai' | 'genai' | 'llm';

export default function AIServicesTable({ services }: { services: AIService[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortField, setSortField] = useState<SortField>('provider_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const filter = searchParams.get('filter') as FilterType || 'all';
    const sort = searchParams.get('sort') as SortField || 'provider_name';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);

    setSearchQuery(query);
    setFilterType(filter);
    setSortField(sort);
    setSortDirection(dir);
    setCurrentPage(page);
    setItemsPerPage(perPage);
    setIsInitialized(true);
  }, [searchParams]);

  // Sync state to URL (only after initialization)
  useEffect(() => {
    if (!isInitialized) return;

    const params = new URLSearchParams();
    if (searchQuery) params.set('q', searchQuery);
    if (filterType !== 'all') params.set('filter', filterType);
    if (sortField !== 'provider_name') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());

    const queryString = params.toString();
    const newUrl = queryString ? `/ai-services?${queryString}` : '/ai-services';

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, filterType, sortField, sortDirection, currentPage, itemsPerPage, isInitialized, router]);

  // Filter by AI type
  const filteredByType = useMemo(() => {
    if (filterType === 'all') return services;
    if (filterType === 'ai') return services.filter((s) => s.has_ai);
    if (filterType === 'genai') return services.filter((s) => s.has_genai);
    if (filterType === 'llm') return services.filter((s) => s.has_llm);
    return services;
  }, [services, filterType]);

  // Filter by search query
  const filteredServices = useMemo(() => {
    if (!searchQuery) return filteredByType;

    const query = searchQuery.toLowerCase();
    return filteredByType.filter((service) => {
      return (
        service.provider_name?.toLowerCase().includes(query) ||
        service.product_name?.toLowerCase().includes(query) ||
        service.service_name?.toLowerCase().includes(query) ||
        service.relevant_excerpt?.toLowerCase().includes(query) ||
        service.fedramp_status?.toLowerCase().includes(query)
      );
    });
  }, [filteredByType, searchQuery]);

  // Sort services
  const sortedServices = useMemo(() => {
    const sorted = [...filteredServices];

    sorted.sort((a, b) => {
      let aValue: any = a[sortField] || '';
      let bValue: any = b[sortField] || '';

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredServices, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(sortedServices.length / itemsPerPage);
  const paginatedServices = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedServices.slice(start, start + itemsPerPage);
  }, [sortedServices, currentPage, itemsPerPage]);

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

  return (
    <div className="space-y-4">
      {/* Filters and Search */}
      <div className="bg-white rounded-lg border border-charcoal-200 p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* AI Type Filters */}
          <div className="flex gap-2">
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'all'
                  ? 'bg-charcoal-700 text-cream border-charcoal-700'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              All ({services.length})
            </button>
            <button
              onClick={() => handleFilterChange('ai')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'ai'
                  ? 'bg-ifp-purple text-white border-ifp-purple'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              AI/ML ({services.filter((s) => s.has_ai).length})
            </button>
            <button
              onClick={() => handleFilterChange('genai')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'genai'
                  ? 'bg-ifp-orange text-white border-ifp-orange'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              GenAI ({services.filter((s) => s.has_genai).length})
            </button>
            <button
              onClick={() => handleFilterChange('llm')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors border ${
                filterType === 'llm'
                  ? 'bg-charcoal-600 text-white border-charcoal-600'
                  : 'bg-white text-charcoal border-charcoal-300 hover:bg-cream'
              }`}
            >
              LLM ({services.filter((s) => s.has_llm).length})
            </button>
          </div>

          {/* Search Box */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search services..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
            />
          </div>

          {/* Items Per Page */}
          <div className="flex items-center">
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-ifp-purple"
            >
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
              <option value={999999}>All</option>
            </select>
          </div>
        </div>
        <div className="mt-3 text-sm text-charcoal-500">
          Showing {paginatedServices.length} of {filteredServices.length} services
          {searchQuery && ` (filtered from ${filteredByType.length} total)`}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cream-200 border-b-2 border-charcoal-200">
              <tr>
                <th
                  onClick={() => handleSort('provider_name')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Provider</span>
                    {sortField === 'provider_name' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('product_name')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Product</span>
                    {sortField === 'product_name' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('service_name')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Service</span>
                    {sortField === 'service_name' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  AI Type
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  Description
                </th>
                <th
                  onClick={() => handleSort('fedramp_status')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Status</span>
                    {sortField === 'fedramp_status' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('impact_level')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Impact</span>
                    {sortField === 'impact_level' && (
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
              {paginatedServices.map((service, index) => (
                <tr
                  key={service.id}
                  onClick={() => router.push(`/product/${service.product_id}`)}
                  className={`cursor-pointer hover:bg-cream hover:border-l-4 hover:border-ifp-purple transition-all ${index % 2 === 0 ? 'bg-white' : 'bg-cream/30'}`}
                >
                  <td className="px-4 py-3 text-sm text-charcoal">{service.provider_name}</td>
                  <td className="px-4 py-3 text-sm font-medium text-charcoal">
                    <div className="max-w-xs truncate" title={service.product_name}>
                      {service.product_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="font-semibold text-charcoal">
                      {service.service_name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex flex-wrap gap-1">
                      {service.has_ai && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple">
                          AI
                        </span>
                      )}
                      {service.has_genai && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange">
                          GenAI
                        </span>
                      )}
                      {service.has_llm && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700 border border-charcoal-400">
                          LLM
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-500">
                    <div className="max-w-md truncate" title={service.relevant_excerpt || undefined}>
                      {service.relevant_excerpt}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    {service.fedramp_status}
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    {service.impact_level}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/product/${service.product_id}`}
                      className="text-ifp-purple hover:text-ifp-purple-dark font-medium underline"
                    >
                      View Product →
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

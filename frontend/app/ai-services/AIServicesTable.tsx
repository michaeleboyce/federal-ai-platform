'use client';

import Link from 'next/link';
import { useState, useMemo, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { List, Package, Building2, ChevronDown, ChevronRight, ChevronsUpDown, Download } from 'lucide-react';
import type { AIService } from '@/lib/ai-db';

type SortField = 'provider_name' | 'product_name' | 'service_name' | 'fedramp_status' | 'impact_level' | 'auth_date';
type SortDirection = 'asc' | 'desc';
type FilterType = 'all' | 'ai' | 'genai' | 'llm';
type ViewMode = 'flat' | 'product' | 'provider';

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
  const [viewMode, setViewMode] = useState<ViewMode>('flat');
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());
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
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.style.display = 'none';
    const file = new File([blob], filename, { type: 'text/csv;charset=utf-8' });
    link.href = URL.createObjectURL(file);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }, 100);
  }

  // Export all services as CSV
  function exportServices() {
    const headers = [
      'Provider',
      'Product',
      'Service',
      'Has AI',
      'Has GenAI',
      'Has LLM',
      'FedRAMP Status',
      'Impact Level',
      'Description',
    ];

    const escapeCell = (cell: string) => {
      if (cell.includes(',') || cell.includes('\n') || cell.includes('"')) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    };

    const rows = filteredServices.map(service => [
      service.provider_name || '',
      service.product_name || '',
      service.service_name || '',
      service.has_ai ? 'Yes' : 'No',
      service.has_genai ? 'Yes' : 'No',
      service.has_llm ? 'Yes' : 'No',
      service.fedramp_status || '',
      service.impact_level || '',
      service.relevant_excerpt || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCell).join(',')),
    ].join('\n');

    const today = new Date().toISOString().split('T')[0];
    downloadFile(csvContent, `AI-Services-${today}.csv`);
    setExportMenuOpen(false);
  }

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const filter = searchParams.get('filter') as FilterType || 'all';
    const sort = searchParams.get('sort') as SortField || 'provider_name';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);
    const view = searchParams.get('view') as ViewMode || 'flat';

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
    if (sortField !== 'provider_name') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());
    if (viewMode !== 'flat') params.set('view', viewMode);

    const queryString = params.toString();
    const newUrl = queryString ? `/ai-services?${queryString}` : '/ai-services';

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, filterType, sortField, sortDirection, currentPage, itemsPerPage, viewMode, isInitialized, router]);

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

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    // Reset expand states when switching views
    setExpandedProviders(new Set());
    setExpandedProducts(new Set());
  };

  // Group services by product
  const productGroups = useMemo(() => {
    const groups = new Map<string, AIService[]>();
    for (const service of filteredServices) {
      const key = service.product_name || 'Unknown Product';
      const existing = groups.get(key) || [];
      existing.push(service);
      groups.set(key, existing);
    }
    return Array.from(groups.entries())
      .sort((a, b) => a[0].localeCompare(b[0]));
  }, [filteredServices]);

  // Group services by provider → product
  const providerGroups = useMemo(() => {
    const providers = new Map<string, { products: Map<string, AIService[]>; serviceCount: number }>();
    for (const service of filteredServices) {
      const providerKey = service.provider_name || 'Unknown Provider';
      const productKey = service.product_name || 'Unknown Product';

      if (!providers.has(providerKey)) {
        providers.set(providerKey, { products: new Map(), serviceCount: 0 });
      }
      const providerData = providers.get(providerKey)!;
      const existing = providerData.products.get(productKey) || [];
      existing.push(service);
      providerData.products.set(productKey, existing);
      providerData.serviceCount++;
    }
    return Array.from(providers.entries())
      .sort((a, b) => a[0].localeCompare(b[0]));
  }, [filteredServices]);

  // Toggle expand functions
  const toggleProvider = (provider: string) => {
    setExpandedProviders(prev => {
      const next = new Set(prev);
      if (next.has(provider)) {
        next.delete(provider);
      } else {
        next.add(provider);
      }
      return next;
    });
  };

  const toggleProduct = (product: string) => {
    setExpandedProducts(prev => {
      const next = new Set(prev);
      if (next.has(product)) {
        next.delete(product);
      } else {
        next.add(product);
      }
      return next;
    });
  };

  // Expand/Collapse all
  const expandAll = () => {
    if (viewMode === 'product') {
      setExpandedProducts(new Set(productGroups.map(([name]) => name)));
    } else if (viewMode === 'provider') {
      setExpandedProviders(new Set(providerGroups.map(([name]) => name)));
      // Also expand all products within providers
      const allProducts = new Set<string>();
      for (const [, data] of providerGroups) {
        for (const [productName] of data.products) {
          allProducts.add(productName);
        }
      }
      setExpandedProducts(allProducts);
    }
  };

  const collapseAll = () => {
    setExpandedProviders(new Set());
    setExpandedProducts(new Set());
  };

  const allExpanded = viewMode === 'product'
    ? productGroups.length > 0 && expandedProducts.size === productGroups.length
    : viewMode === 'provider'
    ? providerGroups.length > 0 && expandedProviders.size === providerGroups.length
    : false;

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
        {/* View Mode Toggle and Status */}
        <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="text-sm text-charcoal-500">
            Showing {viewMode === 'flat' ? paginatedServices.length : filteredServices.length} of {filteredServices.length} services
            {searchQuery && ` (filtered from ${filteredByType.length} total)`}
            {viewMode === 'product' && ` in ${productGroups.length} products`}
            {viewMode === 'provider' && ` from ${providerGroups.length} providers`}
          </div>
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 bg-charcoal-100 rounded-lg p-1">
              <button
                onClick={() => handleViewModeChange('flat')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'flat'
                    ? 'bg-white text-charcoal shadow-sm'
                    : 'text-charcoal-500 hover:text-charcoal'
                }`}
                title="Show all services in a table"
              >
                <List className="w-4 h-4" />
                All Services
              </button>
              <button
                onClick={() => handleViewModeChange('product')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'product'
                    ? 'bg-white text-charcoal shadow-sm'
                    : 'text-charcoal-500 hover:text-charcoal'
                }`}
                title="Group services by product"
              >
                <Package className="w-4 h-4" />
                By Product
              </button>
              <button
                onClick={() => handleViewModeChange('provider')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'provider'
                    ? 'bg-white text-charcoal shadow-sm'
                    : 'text-charcoal-500 hover:text-charcoal'
                }`}
                title="Group services by provider"
              >
                <Building2 className="w-4 h-4" />
                By Provider
              </button>
            </div>
            {/* Expand/Collapse All (only for grouped views) */}
            {viewMode !== 'flat' && (
              <button
                onClick={() => (allExpanded ? collapseAll() : expandAll())}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium text-charcoal-500 hover:text-charcoal hover:bg-charcoal-100 transition-colors"
                title={allExpanded ? 'Collapse all groups' : 'Expand all groups'}
              >
                <ChevronsUpDown className="w-4 h-4" />
                {allExpanded ? 'Collapse All' : 'Expand All'}
              </button>
            )}
            {/* Export Button */}
            <div className="relative" ref={exportMenuRef}>
              <button
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium bg-ifp-purple text-white hover:bg-ifp-purple-dark transition-colors"
                title="Export data to CSV"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              {exportMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-charcoal-200 z-50">
                  <div className="py-1">
                    <button
                      onClick={exportServices}
                      className="w-full text-left px-4 py-2 text-sm text-charcoal hover:bg-cream transition-colors"
                    >
                      <div className="font-medium">Export to CSV</div>
                      <div className="text-xs text-charcoal-500">
                        {filteredServices.length} services (filtered)
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Table View (flat mode) */}
      {viewMode === 'flat' && (
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
      )}

      {/* Product View */}
      {viewMode === 'product' && (
        <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden divide-y divide-charcoal-100">
          {productGroups.map(([productName, productServices]) => {
            const isExpanded = expandedProducts.has(productName);
            const providerName = productServices[0]?.provider_name || 'Unknown';
            const productId = productServices[0]?.product_id;
            // Aggregate badges from all services in this product
            const hasAI = productServices.some(s => s.has_ai);
            const hasGenAI = productServices.some(s => s.has_genai);
            const hasLLM = productServices.some(s => s.has_llm);

            return (
              <div key={productName}>
                <button
                  onClick={() => toggleProduct(productName)}
                  className="w-full flex items-center gap-3 p-4 hover:bg-cream text-left transition-colors"
                >
                  <span className="text-charcoal-400">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                  </span>
                  <div className="flex-1">
                    <div className="font-semibold text-charcoal">{productName}</div>
                    <div className="text-sm text-charcoal-500">{providerName}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* AI Type Badges */}
                    {hasAI && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple rounded-full">
                        AI
                      </span>
                    )}
                    {hasGenAI && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange rounded-full">
                        GenAI
                      </span>
                    )}
                    {hasLLM && (
                      <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-700 border border-charcoal-400 rounded-full">
                        LLM
                      </span>
                    )}
                    <span className="text-sm text-charcoal-500">
                      {productServices.length} service{productServices.length !== 1 ? 's' : ''}
                    </span>
                    {productId && (
                      <Link
                        href={`/product/${productId}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-ifp-purple hover:text-ifp-purple-dark text-sm font-medium"
                      >
                        View Product →
                      </Link>
                    )}
                  </div>
                </button>
                {isExpanded && (
                  <div className="bg-cream-light border-t border-charcoal-100">
                    {productServices.map((service) => (
                      <ServiceRow key={service.id} service={service} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {productGroups.length === 0 && (
            <div className="p-8 text-center text-charcoal-500">
              No products found matching the current filters.
            </div>
          )}
        </div>
      )}

      {/* Provider View */}
      {viewMode === 'provider' && (
        <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden divide-y divide-charcoal-100">
          {providerGroups.map(([providerName, providerData]) => {
            const isProviderExpanded = expandedProviders.has(providerName);
            const productCount = providerData.products.size;
            // Aggregate badges from all services under this provider
            const allProviderServices = Array.from(providerData.products.values()).flat();
            const providerHasAI = allProviderServices.some(s => s.has_ai);
            const providerHasGenAI = allProviderServices.some(s => s.has_genai);
            const providerHasLLM = allProviderServices.some(s => s.has_llm);

            return (
              <div key={providerName}>
                <button
                  onClick={() => toggleProvider(providerName)}
                  className="w-full flex items-center gap-3 p-4 hover:bg-cream text-left transition-colors"
                >
                  <span className="text-charcoal-400">
                    {isProviderExpanded ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                  </span>
                  <div className="flex-1">
                    <div className="font-semibold text-charcoal">{providerName}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* AI Type Badges */}
                    {providerHasAI && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple rounded-full">
                        AI
                      </span>
                    )}
                    {providerHasGenAI && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange rounded-full">
                        GenAI
                      </span>
                    )}
                    {providerHasLLM && (
                      <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-700 border border-charcoal-400 rounded-full">
                        LLM
                      </span>
                    )}
                    <span className="px-2 py-0.5 text-xs bg-cream text-charcoal-600 rounded-full">
                      {productCount} product{productCount !== 1 ? 's' : ''}
                    </span>
                    <span className="text-sm text-charcoal-500">
                      {providerData.serviceCount} service{providerData.serviceCount !== 1 ? 's' : ''}
                    </span>
                  </div>
                </button>
                {isProviderExpanded && (
                  <div className="bg-cream-light">
                    {Array.from(providerData.products.entries())
                      .sort((a, b) => a[0].localeCompare(b[0]))
                      .map(([productName, productServices]) => {
                        const isProductExpanded = expandedProducts.has(productName);
                        const productId = productServices[0]?.product_id;
                        // Aggregate badges for this product
                        const productHasAI = productServices.some(s => s.has_ai);
                        const productHasGenAI = productServices.some(s => s.has_genai);
                        const productHasLLM = productServices.some(s => s.has_llm);

                        return (
                          <div key={productName} className="border-t border-charcoal-100">
                            <button
                              onClick={() => toggleProduct(productName)}
                              className="w-full flex items-center gap-3 p-3 pl-12 hover:bg-cream text-left transition-colors"
                            >
                              <span className="text-charcoal-400">
                                {isProductExpanded ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </span>
                              <div className="flex-1">
                                <span className="font-medium text-charcoal">{productName}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {/* AI Type Badges */}
                                {productHasAI && (
                                  <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple-dark border border-ifp-purple rounded-full">
                                    AI
                                  </span>
                                )}
                                {productHasGenAI && (
                                  <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange-dark border border-ifp-orange rounded-full">
                                    GenAI
                                  </span>
                                )}
                                {productHasLLM && (
                                  <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-700 border border-charcoal-400 rounded-full">
                                    LLM
                                  </span>
                                )}
                                <span className="text-sm text-charcoal-500">
                                  {productServices.length} service{productServices.length !== 1 ? 's' : ''}
                                </span>
                                {productId && (
                                  <Link
                                    href={`/product/${productId}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className="text-ifp-purple hover:text-ifp-purple-dark text-sm font-medium"
                                  >
                                    View →
                                  </Link>
                                )}
                              </div>
                            </button>
                            {isProductExpanded && (
                              <div className="bg-white border-t border-charcoal-100">
                                {productServices.map((service) => (
                                  <ServiceRow key={service.id} service={service} indent />
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            );
          })}
          {providerGroups.length === 0 && (
            <div className="p-8 text-center text-charcoal-500">
              No providers found matching the current filters.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Service row component for grouped views
function ServiceRow({ service, indent = false }: { service: AIService; indent?: boolean }) {
  return (
    <div className={`p-3 border-b border-charcoal-50 last:border-b-0 ${indent ? 'pl-20' : 'pl-16'}`}>
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <span className="font-medium text-charcoal">{service.service_name}</span>
          {service.relevant_excerpt && (
            <p className="text-sm text-charcoal-500 mt-0.5 line-clamp-1">
              {service.relevant_excerpt}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {service.has_ai && (
            <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
              AI
            </span>
          )}
          {service.has_genai && (
            <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
              GenAI
            </span>
          )}
          {service.has_llm && (
            <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-700 rounded-full">
              LLM
            </span>
          )}
        </div>
        {service.fedramp_status && (
          <span className="text-sm text-charcoal-500">{service.fedramp_status}</span>
        )}
        {service.impact_level && (
          <span className="text-sm text-charcoal-500">{service.impact_level}</span>
        )}
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface Product {
  id: string;
  name: string;
  csp: string;
  cso: string;
  service_offering: string;
  status: string;
  service_model: string[];
  impact_level: string[];
  service_desc: string;
  all_others: string[];
  auth_date: string;
}

interface IncidentScoreInfo {
  maxScore: number;
  matchCount: number;
}

type SortField = 'csp' | 'cso' | 'status' | 'auth_date' | 'services' | 'incidents';
type SortDirection = 'asc' | 'desc';
type IncidentFilter = 'all' | 'high' | 'any' | 'none';

interface ProductTableProps {
  products: Product[];
  incidentScores?: Record<string, IncidentScoreInfo>;
}

export default function ProductTable({ products, incidentScores = {} }: ProductTableProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('csp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [incidentFilter, setIncidentFilter] = useState<IncidentFilter>('all');
  const [isInitialized, setIsInitialized] = useState(false);

  const hasIncidentScores = Object.keys(incidentScores).length > 0;

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const sort = searchParams.get('sort') as SortField || 'csp';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);
    const incidents = searchParams.get('incidents') as IncidentFilter || 'all';

    setSearchQuery(query);
    setSortField(sort);
    setSortDirection(dir);
    setCurrentPage(page);
    setItemsPerPage(perPage);
    setIncidentFilter(incidents);
    setIsInitialized(true);
  }, [searchParams]);

  // Sync state to URL (only after initialization)
  useEffect(() => {
    if (!isInitialized) return;

    const params = new URLSearchParams();
    if (searchQuery) params.set('q', searchQuery);
    if (sortField !== 'csp') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());
    if (incidentFilter !== 'all') params.set('incidents', incidentFilter);

    const queryString = params.toString();
    const newUrl = queryString ? `/products?${queryString}` : '/products';

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, sortField, sortDirection, currentPage, itemsPerPage, incidentFilter, isInitialized, router]);

  // Filter products based on search query and incident filter
  const filteredProducts = useMemo(() => {
    let filtered = products;

    // Apply incident filter
    if (incidentFilter !== 'all' && hasIncidentScores) {
      filtered = filtered.filter((product) => {
        const scoreInfo = incidentScores[product.id];
        switch (incidentFilter) {
          case 'high':
            return scoreInfo && scoreInfo.maxScore >= 0.75;
          case 'any':
            return scoreInfo && scoreInfo.matchCount > 0;
          case 'none':
            return !scoreInfo || scoreInfo.matchCount === 0;
          default:
            return true;
        }
      });
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((product) => {
        // Search in provider, offering, description, and services
        const matchesBasic =
          product.csp?.toLowerCase().includes(query) ||
          product.cso?.toLowerCase().includes(query) ||
          product.id?.toLowerCase().includes(query) ||
          product.service_desc?.toLowerCase().includes(query);

        // Search in service names
        const matchesServices = product.all_others?.some((service) =>
          service.toLowerCase().includes(query)
        );

        return matchesBasic || matchesServices;
      });
    }

    return filtered;
  }, [products, searchQuery, incidentFilter, hasIncidentScores, incidentScores]);

  // Sort products
  const sortedProducts = useMemo(() => {
    const sorted = [...filteredProducts];

    sorted.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'csp':
          aValue = a.csp || '';
          bValue = b.csp || '';
          break;
        case 'cso':
          aValue = a.cso || '';
          bValue = b.cso || '';
          break;
        case 'status':
          aValue = a.status || '';
          bValue = b.status || '';
          break;
        case 'auth_date':
          aValue = a.auth_date || '';
          bValue = b.auth_date || '';
          break;
        case 'services':
          aValue = a.all_others?.length || 0;
          bValue = b.all_others?.length || 0;
          break;
        case 'incidents':
          aValue = incidentScores[a.id]?.maxScore || 0;
          bValue = incidentScores[b.id]?.maxScore || 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredProducts, sortField, sortDirection, incidentScores]);

  // Pagination
  const totalPages = Math.ceil(sortedProducts.length / itemsPerPage);
  const paginatedProducts = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedProducts.slice(start, start + itemsPerPage);
  }, [sortedProducts, currentPage, itemsPerPage]);

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

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="bg-white rounded-lg border border-gov-slate-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gov-navy-900 mb-2">
              Search Products
            </label>
            <input
              id="search"
              type="text"
              placeholder="Search by provider, offering, service name (e.g., 'Bedrock')..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-4 py-2 border border-gov-slate-300 rounded-md focus:ring-2 focus:ring-gov-navy-500 focus:border-transparent"
            />
          </div>
          {hasIncidentScores && (
            <div className="flex flex-col">
              <label htmlFor="incidentFilter" className="block text-sm font-medium text-gov-navy-900 mb-2">
                Incident Matches
              </label>
              <select
                id="incidentFilter"
                value={incidentFilter}
                onChange={(e) => {
                  setIncidentFilter(e.target.value as IncidentFilter);
                  setCurrentPage(1);
                }}
                className="px-4 py-2 border border-gov-slate-300 rounded-md focus:ring-2 focus:ring-gov-navy-500"
              >
                <option value="all">All Products</option>
                <option value="high">High Match (≥75%)</option>
                <option value="any">Any Match</option>
                <option value="none">No Matches</option>
              </select>
            </div>
          )}
          <div className="flex flex-col">
            <label htmlFor="perPage" className="block text-sm font-medium text-gov-navy-900 mb-2">
              Per Page
            </label>
            <select
              id="perPage"
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-4 py-2 border border-gov-slate-300 rounded-md focus:ring-2 focus:ring-gov-navy-500"
            >
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
              <option value={999999}>All</option>
            </select>
          </div>
        </div>
        <div className="mt-3 text-sm text-gov-slate-600">
          Showing {paginatedProducts.length} of {filteredProducts.length} products
          {searchQuery && ` (filtered from ${products.length} total)`}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gov-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gov-slate-100 border-b-2 border-gov-slate-200">
              <tr>
                <th
                  onClick={() => handleSort('csp')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Provider</span>
                    {sortField === 'csp' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('cso')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Offering</span>
                    {sortField === 'cso' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900">
                  Service Model
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900">
                  Impact Level
                </th>
                <th
                  onClick={() => handleSort('services')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Services</span>
                    {sortField === 'services' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('auth_date')}
                  className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Auth Date</span>
                    {sortField === 'auth_date' && (
                      <span className="text-gov-navy-700">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                {hasIncidentScores && (
                  <th
                    onClick={() => handleSort('incidents')}
                    className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900 cursor-pointer hover:bg-gov-slate-200 transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Incidents</span>
                      {sortField === 'incidents' && (
                        <span className="text-gov-navy-700">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                )}
                <th className="px-4 py-3 text-left text-sm font-semibold text-gov-navy-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gov-slate-200">
              {paginatedProducts.map((product, index) => (
                <tr
                  key={product.id}
                  onClick={() => router.push(`/product/${product.id}`)}
                  className={`cursor-pointer hover:bg-gov-slate-100 hover:border-l-4 hover:border-gov-navy-600 transition-all ${index % 2 === 0 ? 'bg-white' : 'bg-gov-slate-50/30'}`}
                >
                  <td className="px-4 py-3 text-sm text-gov-navy-900">{product.csp}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gov-navy-900">
                    <div className="max-w-xs truncate" title={product.cso}>
                      {product.cso}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gov-slate-700">
                    {Array.isArray(product.service_model)
                      ? product.service_model.join(', ')
                      : product.service_model}
                  </td>
                  <td className="px-4 py-3 text-sm text-gov-slate-700">
                    {Array.isArray(product.impact_level)
                      ? product.impact_level.join(', ')
                      : product.impact_level}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {product.all_others ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gov-navy-100 text-gov-navy-800">
                        {product.all_others.length} services
                      </span>
                    ) : (
                      <span className="text-gov-slate-400">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gov-slate-600">
                    {product.auth_date || 'N/A'}
                  </td>
                  {hasIncidentScores && (
                    <td className="px-4 py-3 text-sm">
                      {incidentScores[product.id] ? (
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            incidentScores[product.id].maxScore >= 0.75
                              ? 'bg-status-error-light text-status-error-dark border border-status-error'
                              : incidentScores[product.id].maxScore >= 0.60
                              ? 'bg-status-warning-light text-status-warning-dark border border-status-warning'
                              : 'bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300'
                          }`}
                        >
                          {incidentScores[product.id].matchCount} ({Math.round(incidentScores[product.id].maxScore * 100)}%)
                        </span>
                      ) : (
                        <span className="text-gov-slate-400">—</span>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/product/${product.id}`}
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

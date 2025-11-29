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

type SortField = 'csp' | 'cso' | 'status' | 'auth_date' | 'services';
type SortDirection = 'asc' | 'desc';

export default function ProductTable({ products }: { products: Product[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('csp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize state from URL on mount
  useEffect(() => {
    const query = searchParams.get('q') || '';
    const sort = searchParams.get('sort') as SortField || 'csp';
    const dir = searchParams.get('dir') as SortDirection || 'asc';
    const page = parseInt(searchParams.get('page') || '1', 10);
    const perPage = parseInt(searchParams.get('perPage') || '50', 10);

    setSearchQuery(query);
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
    if (sortField !== 'csp') params.set('sort', sortField);
    if (sortDirection !== 'asc') params.set('dir', sortDirection);
    if (currentPage !== 1) params.set('page', currentPage.toString());
    if (itemsPerPage !== 50) params.set('perPage', itemsPerPage.toString());

    const queryString = params.toString();
    // Preserve current pathname instead of hardcoding to '/'
    const currentPath = window.location.pathname;
    const newUrl = queryString ? `${currentPath}?${queryString}` : currentPath;

    router.replace(newUrl, { scroll: false });
  }, [searchQuery, sortField, sortDirection, currentPage, itemsPerPage, isInitialized, router]);

  // Filter products based on search query
  const filteredProducts = useMemo(() => {
    if (!searchQuery) return products;

    const query = searchQuery.toLowerCase();
    return products.filter((product) => {
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
  }, [products, searchQuery]);

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
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredProducts, sortField, sortDirection]);

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
      <div className="bg-white rounded-lg border border-charcoal-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-charcoal mb-2">
              Search Products
            </label>
            <input
              id="search"
              type="text"
              placeholder="Search by provider, offering, service name (e.g., 'Bedrock')..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
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
          Showing {paginatedProducts.length} of {filteredProducts.length} products
          {searchQuery && ` (filtered from ${products.length} total)`}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-cream-200 border-b-2 border-charcoal-200">
              <tr>
                <th
                  onClick={() => handleSort('csp')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Provider</span>
                    {sortField === 'csp' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('cso')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Offering</span>
                    {sortField === 'cso' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  Service Model
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-charcoal">
                  Impact Level
                </th>
                <th
                  onClick={() => handleSort('services')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Services</span>
                    {sortField === 'services' && (
                      <span className="text-ifp-purple">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('auth_date')}
                  className="px-4 py-3 text-left text-sm font-semibold text-charcoal cursor-pointer hover:bg-charcoal-200 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>Auth Date</span>
                    {sortField === 'auth_date' && (
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
              {paginatedProducts.map((product, index) => (
                <tr
                  key={product.id}
                  onClick={() => router.push(`/product/${product.id}`)}
                  className={`cursor-pointer hover:bg-cream hover:border-l-4 hover:border-ifp-purple transition-all ${index % 2 === 0 ? 'bg-white' : 'bg-cream/30'}`}
                >
                  <td className="px-4 py-3 text-sm text-charcoal">{product.csp}</td>
                  <td className="px-4 py-3 text-sm font-medium text-charcoal">
                    <div className="max-w-xs truncate" title={product.cso}>
                      {product.cso}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    {Array.isArray(product.service_model)
                      ? product.service_model.join(', ')
                      : product.service_model}
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-600">
                    {Array.isArray(product.impact_level)
                      ? product.impact_level.join(', ')
                      : product.impact_level}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {product.all_others ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-charcoal-100 text-charcoal-700">
                        {product.all_others.length} services
                      </span>
                    ) : (
                      <span className="text-charcoal-400">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-charcoal-500">
                    {product.auth_date || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link
                      href={`/product/${product.id}`}
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

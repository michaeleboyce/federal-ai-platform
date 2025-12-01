'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { logoutAction } from '../actions';
import { updateProductAnalysisAction } from './actions';
import type { ProductWithAnalysis, ProductStats } from '@/lib/products-admin-db';
import {
  ChevronDown,
  ChevronRight,
  Save,
  X,
  ExternalLink,
  Check,
  Search,
  Filter,
  Download,
} from 'lucide-react';

interface ProductsAdminPanelProps {
  initialProducts: ProductWithAnalysis[];
  initialStats: ProductStats;
}

type TagFilter =
  | 'all'
  | 'hasAi'
  | 'hasGenai'
  | 'hasLlm'
  | 'hasChatbot'
  | 'hasCodingAssistant'
  | 'hasImageGeneration'
  | 'hasDocumentAnalysis'
  | 'hasSpeechToText'
  | 'hasTranslation'
  | 'hasAiSearch'
  | 'unreviewed';

const TAG_FILTER_OPTIONS: { key: TagFilter; label: string; color: string }[] = [
  { key: 'all', label: 'All', color: 'bg-charcoal-100 text-charcoal-700' },
  { key: 'hasAi', label: 'AI', color: 'bg-ifp-purple-light text-ifp-purple' },
  { key: 'hasGenai', label: 'GenAI', color: 'bg-ifp-orange-light text-ifp-orange' },
  { key: 'hasLlm', label: 'LLM', color: 'bg-green-100 text-green-700' },
  { key: 'hasChatbot', label: 'Chatbot', color: 'bg-blue-100 text-blue-700' },
  { key: 'hasCodingAssistant', label: 'Coding', color: 'bg-violet-100 text-violet-700' },
  { key: 'hasImageGeneration', label: 'Image', color: 'bg-pink-100 text-pink-700' },
  { key: 'hasDocumentAnalysis', label: 'Documents', color: 'bg-amber-100 text-amber-700' },
  { key: 'hasSpeechToText', label: 'Speech', color: 'bg-teal-100 text-teal-700' },
  { key: 'hasTranslation', label: 'Translation', color: 'bg-cyan-100 text-cyan-700' },
  { key: 'hasAiSearch', label: 'AI Search', color: 'bg-indigo-100 text-indigo-700' },
  { key: 'unreviewed', label: 'Unreviewed', color: 'bg-charcoal-200 text-charcoal-600' },
];

export default function ProductsAdminPanel({
  initialProducts,
  initialStats,
}: ProductsAdminPanelProps) {
  const [products, setProducts] = useState(initialProducts);
  const [stats] = useState(initialStats);
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTagFilter, setActiveTagFilter] = useState<TagFilter>('all');
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

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
    const file = new File([blob], filename, { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.style.display = 'none';
    link.href = URL.createObjectURL(file);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }, 100);
  }

  // Export function that filters products and generates CSV
  function exportProducts(filter: 'all' | 'ai' | 'llm') {
    const today = new Date().toISOString().split('T')[0];

    // Filter products based on export type
    let exportData = products;
    let filename = `fedramp-products-all-${today}.csv`;

    if (filter === 'ai') {
      exportData = products.filter(p => p.hasAi);
      filename = `fedramp-products-ai-ml-${today}.csv`;
    } else if (filter === 'llm') {
      exportData = products.filter(p => p.hasLlm);
      filename = `fedramp-products-llm-${today}.csv`;
    }

    const headers = [
      'FedRAMP ID',
      'Provider',
      'Product Name',
      'Service Name',
      'Has AI',
      'Has GenAI',
      'Has LLM',
      'Has Chatbot',
      'Has Coding Assistant',
      'Has Image Generation',
      'Has Document Analysis',
      'Has Speech to Text',
      'Has Translation',
      'Has AI Search',
      'FedRAMP Status',
      'Impact Level',
      'Auth Date',
      'Authorization Count',
      'Reviewed',
      'Relevant Excerpt',
      'Admin Notes',
      'Custom Description',
    ];

    const rows = exportData.map(p => [
      p.productId,
      p.providerName,
      p.productName,
      p.serviceName,
      p.hasAi ? 'Yes' : 'No',
      p.hasGenai ? 'Yes' : 'No',
      p.hasLlm ? 'Yes' : 'No',
      p.hasChatbot ? 'Yes' : 'No',
      p.hasCodingAssistant ? 'Yes' : 'No',
      p.hasImageGeneration ? 'Yes' : 'No',
      p.hasDocumentAnalysis ? 'Yes' : 'No',
      p.hasSpeechToText ? 'Yes' : 'No',
      p.hasTranslation ? 'Yes' : 'No',
      p.hasAiSearch ? 'Yes' : 'No',
      p.fedrampStatus || '',
      p.impactLevel || '',
      p.authDate || '',
      p.authorizationCount.toString(),
      p.reviewedAt ? 'Yes' : 'No',
      (p.relevantExcerpt || '').replace(/"/g, '""'),
      (p.adminNotes || '').replace(/"/g, '""'),
      (p.customDescription || '').replace(/"/g, '""'),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    downloadFile(csvContent, filename);
    setExportMenuOpen(false);
  }

  // Filter products
  const filteredProducts = products.filter(product => {
    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        product.productName.toLowerCase().includes(query) ||
        product.providerName.toLowerCase().includes(query) ||
        product.serviceName.toLowerCase().includes(query);
      if (!matchesSearch) return false;
    }

    // Tag filter
    if (activeTagFilter !== 'all') {
      if (activeTagFilter === 'unreviewed') {
        if (product.reviewedAt) return false;
      } else {
        const flagValue = product[activeTagFilter as keyof typeof product];
        if (!flagValue) return false;
      }
    }

    return true;
  });

  async function handleLogout() {
    await logoutAction();
    router.refresh();
  }

  function toggleProduct(id: number) {
    setExpandedProducts(prev => {
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
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-charcoal text-white py-4 px-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold font-serif">Admin Panel</h1>
            <p className="text-sm text-charcoal-300">FedRAMP Products AI Annotation</p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/admin"
              className="text-sm text-charcoal-300 hover:text-white transition-colors"
            >
              ← Agency Tools
            </Link>
            <button
              onClick={handleLogout}
              className="bg-charcoal-600 hover:bg-charcoal-500 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Stats and Export */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-3xl font-bold text-charcoal">{stats.total}</div>
              <div className="text-sm text-charcoal-600">Products</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-3xl font-bold text-ifp-purple">{stats.withAi}</div>
              <div className="text-sm text-charcoal-600">Has AI</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-3xl font-bold text-green-600">{stats.reviewed}</div>
              <div className="text-sm text-charcoal-600">Reviewed</div>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="text-3xl font-bold text-charcoal-400">{stats.unreviewed}</div>
              <div className="text-sm text-charcoal-600">Unreviewed</div>
            </div>
          </div>

          {/* Export Dropdown */}
          <div className="relative" ref={exportMenuRef}>
            <button
              onClick={() => setExportMenuOpen(!exportMenuOpen)}
              className="flex items-center gap-2 px-4 py-2 bg-ifp-purple text-white rounded-lg text-sm font-medium hover:bg-ifp-purple-dark transition-colors shadow-sm"
            >
              <Download className="w-4 h-4" />
              Export
              <ChevronDown className={`w-4 h-4 transition-transform ${exportMenuOpen ? 'rotate-180' : ''}`} />
            </button>
            {exportMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-charcoal-200 z-50">
                <div className="py-1">
                  <button
                    onClick={() => exportProducts('all')}
                    className="w-full text-left px-4 py-2.5 text-sm text-charcoal hover:bg-cream transition-colors"
                  >
                    <div className="font-medium">All Products</div>
                    <div className="text-xs text-charcoal-500">{stats.total} products</div>
                  </button>
                  <button
                    onClick={() => exportProducts('ai')}
                    className="w-full text-left px-4 py-2.5 text-sm text-charcoal hover:bg-cream transition-colors"
                  >
                    <div className="font-medium">AI/ML Products</div>
                    <div className="text-xs text-charcoal-500">{stats.withAi} products with AI capabilities</div>
                  </button>
                  <button
                    onClick={() => exportProducts('llm')}
                    className="w-full text-left px-4 py-2.5 text-sm text-charcoal hover:bg-cream transition-colors"
                  >
                    <div className="font-medium">LLM Products</div>
                    <div className="text-xs text-charcoal-500">{stats.withLlm} products with LLM</div>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow-sm mb-6 p-4">
          <div className="flex flex-col gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by product name, provider, or service..."
                className="w-full pl-10 pr-4 py-2 border border-charcoal-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
              />
            </div>

            {/* Tag Filters */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Filter className="w-4 h-4 text-charcoal-400" />
                <span className="text-sm text-charcoal-600 font-medium">Filter by capability:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {TAG_FILTER_OPTIONS.map(option => (
                  <button
                    key={option.key}
                    onClick={() => setActiveTagFilter(option.key)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                      activeTagFilter === option.key
                        ? `${option.color} ring-2 ring-offset-1 ring-charcoal-400`
                        : `${option.color} opacity-60 hover:opacity-100`
                    }`}
                  >
                    {option.label}
                    {option.key !== 'all' && option.key !== 'unreviewed' && (
                      <span className="ml-1 opacity-70">
                        ({products.filter(p => p[option.key as keyof typeof p]).length})
                      </span>
                    )}
                    {option.key === 'unreviewed' && (
                      <span className="ml-1 opacity-70">
                        ({products.filter(p => !p.reviewedAt).length})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {(searchQuery || activeTagFilter !== 'all') && (
            <p className="text-xs text-charcoal-500 mt-3 pt-3 border-t border-charcoal-100">
              Showing {filteredProducts.length} of {products.length} products
              {activeTagFilter !== 'all' && (
                <button
                  onClick={() => setActiveTagFilter('all')}
                  className="ml-2 text-ifp-purple hover:underline"
                >
                  Clear filter
                </button>
              )}
            </p>
          )}
        </div>

        {/* Products List */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b border-charcoal-200">
            <h2 className="font-semibold text-charcoal">FedRAMP Products</h2>
            <p className="text-sm text-charcoal-500 mt-1">
              Click a product to edit AI annotations
            </p>
          </div>

          <div className="divide-y divide-charcoal-100 max-h-[600px] overflow-y-auto">
            {filteredProducts.map(product => (
              <div key={product.id}>
                {/* Product Row */}
                <div
                  className={`flex items-center gap-3 p-4 hover:bg-cream cursor-pointer ${
                    expandedProducts.has(product.id) ? 'bg-cream' : ''
                  }`}
                  onClick={() => toggleProduct(product.id)}
                >
                  <button className="text-charcoal-400">
                    {expandedProducts.has(product.id) ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                  </button>

                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-charcoal truncate">
                      <span className="text-ifp-purple font-semibold mr-2">
                        {product.providerName}
                      </span>
                      {product.productName}
                    </div>
                    <div className="text-sm text-charcoal-500 truncate">
                      {product.serviceName}
                    </div>
                  </div>

                  {/* AI Flags Badges */}
                  <div className="flex flex-wrap gap-1 max-w-[300px]">
                    {product.hasAi && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                        AI
                      </span>
                    )}
                    {product.hasGenai && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                        GenAI
                      </span>
                    )}
                    {product.hasLlm && (
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                        LLM
                      </span>
                    )}
                    {product.hasChatbot && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                        Chatbot
                      </span>
                    )}
                    {product.hasCodingAssistant && (
                      <span className="px-2 py-0.5 text-xs bg-violet-100 text-violet-700 rounded-full">
                        Coding
                      </span>
                    )}
                    {product.hasImageGeneration && (
                      <span className="px-2 py-0.5 text-xs bg-pink-100 text-pink-700 rounded-full">
                        Image
                      </span>
                    )}
                    {product.hasDocumentAnalysis && (
                      <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded-full">
                        Docs
                      </span>
                    )}
                    {product.hasSpeechToText && (
                      <span className="px-2 py-0.5 text-xs bg-teal-100 text-teal-700 rounded-full">
                        Speech
                      </span>
                    )}
                    {product.hasTranslation && (
                      <span className="px-2 py-0.5 text-xs bg-cyan-100 text-cyan-700 rounded-full">
                        Translation
                      </span>
                    )}
                    {product.hasAiSearch && (
                      <span className="px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded-full">
                        Search
                      </span>
                    )}
                  </div>

                  {/* Review Status */}
                  {product.reviewedAt ? (
                    <span className="flex items-center gap-1 text-green-600">
                      <Check className="w-4 h-4" />
                    </span>
                  ) : (
                    <span className="w-4 h-4 rounded-full border-2 border-charcoal-300" />
                  )}

                  {/* Agency Count */}
                  <span className="text-sm text-charcoal-500 w-16 text-right">
                    {product.authorizationCount} agencies
                  </span>

                  {/* Link to FedRAMP Product Page */}
                  <Link
                    href={`/product/${product.productId}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-charcoal-400 hover:text-ifp-purple p-1"
                    title="View FedRAMP product details"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </div>

                {/* Expanded Edit Form */}
                {expandedProducts.has(product.id) && (
                  <ProductEditForm
                    product={product}
                    onSave={async (data) => {
                      const result = await updateProductAnalysisAction(product.id, data);
                      if (result.success) {
                        // Update local state
                        setProducts(prev =>
                          prev.map(p =>
                            p.id === product.id
                              ? { ...p, ...data, reviewedAt: new Date() }
                              : p
                          )
                        );
                      }
                    }}
                    onCancel={() => setExpandedProducts(prev => {
                      const next = new Set(prev);
                      next.delete(product.id);
                      return next;
                    })}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ========================================
// PRODUCT EDIT FORM
// ========================================

interface ProductEditFormProps {
  product: ProductWithAnalysis;
  onSave: (data: {
    hasAi: boolean;
    hasGenai: boolean;
    hasLlm: boolean;
    hasChatbot: boolean;
    hasCodingAssistant: boolean;
    hasImageGeneration: boolean;
    hasDocumentAnalysis: boolean;
    hasSpeechToText: boolean;
    hasTranslation: boolean;
    hasAiSearch: boolean;
    relevantExcerpt: string | null;
    adminNotes: string | null;
    customDescription: string | null;
  }) => Promise<void>;
  onCancel: () => void;
}

function ProductEditForm({ product, onSave, onCancel }: ProductEditFormProps) {
  const [formData, setFormData] = useState({
    // Original AI flags
    hasAi: product.hasAi,
    hasGenai: product.hasGenai,
    hasLlm: product.hasLlm,
    // Expanded capabilities
    hasChatbot: product.hasChatbot ?? false,
    hasCodingAssistant: product.hasCodingAssistant ?? false,
    hasImageGeneration: product.hasImageGeneration ?? false,
    hasDocumentAnalysis: product.hasDocumentAnalysis ?? false,
    hasSpeechToText: product.hasSpeechToText ?? false,
    hasTranslation: product.hasTranslation ?? false,
    hasAiSearch: product.hasAiSearch ?? false,
    // Text fields
    relevantExcerpt: product.relevantExcerpt || '',
    adminNotes: product.adminNotes || '',
    customDescription: product.customDescription || '',
  });
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    setIsSaving(true);
    await onSave({
      ...formData,
      relevantExcerpt: formData.relevantExcerpt || null,
      adminNotes: formData.adminNotes || null,
      customDescription: formData.customDescription || null,
    });
    setIsSaving(false);
  }

  function toggleFlag(flag: keyof typeof formData) {
    setFormData(prev => ({ ...prev, [flag]: !prev[flag] }));
  }

  return (
    <div className="bg-cream-light border-t border-charcoal-100 p-6">
      {/* Original AI Flags Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-charcoal mb-3">
          AI Classification (computer-annotated, editable)
        </h3>
        <div className="flex flex-wrap gap-3">
          <FlagCheckbox
            label="Has AI"
            checked={formData.hasAi}
            onChange={() => toggleFlag('hasAi')}
            color="purple"
          />
          <FlagCheckbox
            label="Has GenAI"
            checked={formData.hasGenai}
            onChange={() => toggleFlag('hasGenai')}
            color="orange"
          />
          <FlagCheckbox
            label="Has LLM"
            checked={formData.hasLlm}
            onChange={() => toggleFlag('hasLlm')}
            color="green"
          />
        </div>
      </div>

      {/* Expanded Capabilities Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-charcoal mb-3">
          Expanded AI Capabilities
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <FlagCheckbox
            label="Chatbot"
            checked={formData.hasChatbot}
            onChange={() => toggleFlag('hasChatbot')}
          />
          <FlagCheckbox
            label="Coding Assistant"
            checked={formData.hasCodingAssistant}
            onChange={() => toggleFlag('hasCodingAssistant')}
          />
          <FlagCheckbox
            label="Image Generation"
            checked={formData.hasImageGeneration}
            onChange={() => toggleFlag('hasImageGeneration')}
          />
          <FlagCheckbox
            label="Document Analysis"
            checked={formData.hasDocumentAnalysis}
            onChange={() => toggleFlag('hasDocumentAnalysis')}
          />
          <FlagCheckbox
            label="Speech to Text"
            checked={formData.hasSpeechToText}
            onChange={() => toggleFlag('hasSpeechToText')}
          />
          <FlagCheckbox
            label="Translation"
            checked={formData.hasTranslation}
            onChange={() => toggleFlag('hasTranslation')}
          />
          <FlagCheckbox
            label="AI Search"
            checked={formData.hasAiSearch}
            onChange={() => toggleFlag('hasAiSearch')}
          />
        </div>
      </div>

      {/* Relevant Excerpt */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-charcoal mb-1">
          Relevant Excerpt
        </label>
        <textarea
          value={formData.relevantExcerpt}
          onChange={(e) => setFormData(prev => ({ ...prev, relevantExcerpt: e.target.value }))}
          className="w-full px-3 py-2 text-sm border border-charcoal-300 rounded-lg resize-y"
          rows={3}
          placeholder="Key text from service description that indicates AI capabilities..."
        />
      </div>

      {/* Admin Notes */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-charcoal mb-1">
          Admin Notes
        </label>
        <textarea
          value={formData.adminNotes}
          onChange={(e) => setFormData(prev => ({ ...prev, adminNotes: e.target.value }))}
          className="w-full px-3 py-2 text-sm border border-charcoal-300 rounded-lg resize-y"
          rows={2}
          placeholder="Internal notes about this product's AI capabilities..."
        />
      </div>

      {/* Custom Description */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-charcoal mb-1">
          Custom Description
        </label>
        <textarea
          value={formData.customDescription}
          onChange={(e) => setFormData(prev => ({ ...prev, customDescription: e.target.value }))}
          className="w-full px-3 py-2 text-sm border border-charcoal-300 rounded-lg resize-y"
          rows={2}
          placeholder="Override or supplement the FedRAMP description..."
        />
      </div>

      {/* FedRAMP Metadata (read-only) */}
      <div className="mb-6 p-4 bg-white rounded-lg">
        <h3 className="text-sm font-semibold text-charcoal mb-2">FedRAMP Metadata</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-charcoal-500">Status:</span>
            <span className="ml-1 text-charcoal">{product.fedrampStatus || 'N/A'}</span>
          </div>
          <div>
            <span className="text-charcoal-500">Impact Level:</span>
            <span className="ml-1 text-charcoal">{product.impactLevel || 'N/A'}</span>
          </div>
          <div>
            <span className="text-charcoal-500">Auth Date:</span>
            <span className="ml-1 text-charcoal">{product.authDate || 'N/A'}</span>
          </div>
          <div>
            <span className="text-charcoal-500">Authorizations:</span>
            <span className="ml-1 text-charcoal">{product.authorizationCount}</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-ifp-purple text-white text-sm font-medium rounded-lg hover:bg-ifp-purple-dark disabled:opacity-50 transition-colors"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save & Mark Reviewed'}
          </button>
          <button
            onClick={onCancel}
            className="flex items-center gap-2 px-4 py-2 bg-charcoal-200 text-charcoal text-sm font-medium rounded-lg hover:bg-charcoal-300 transition-colors"
          >
            <X className="w-4 h-4" />
            Cancel
          </button>
        </div>

        {product.reviewedAt && (
          <span className="text-xs text-charcoal-500">
            Last reviewed: {new Date(product.reviewedAt).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}

// ========================================
// FLAG CHECKBOX COMPONENT
// ========================================

interface FlagCheckboxProps {
  label: string;
  checked: boolean;
  onChange: () => void;
  color?: 'purple' | 'orange' | 'green' | 'default';
}

function FlagCheckbox({ label, checked, onChange, color = 'default' }: FlagCheckboxProps) {
  const colorClasses = {
    purple: checked
      ? 'bg-ifp-purple-light border-ifp-purple text-ifp-purple'
      : 'bg-white border-charcoal-300 text-charcoal-600',
    orange: checked
      ? 'bg-ifp-orange-light border-ifp-orange text-ifp-orange'
      : 'bg-white border-charcoal-300 text-charcoal-600',
    green: checked
      ? 'bg-green-100 border-green-600 text-green-700'
      : 'bg-white border-charcoal-300 text-charcoal-600',
    default: checked
      ? 'bg-ifp-purple-light border-ifp-purple text-ifp-purple'
      : 'bg-white border-charcoal-300 text-charcoal-600',
  };

  return (
    <button
      type="button"
      onClick={onChange}
      className={`flex items-center gap-2 px-3 py-2 border rounded-lg text-sm font-medium transition-colors ${colorClasses[color]}`}
    >
      <span
        className={`w-4 h-4 rounded border flex items-center justify-center ${
          checked
            ? color === 'purple'
              ? 'bg-ifp-purple border-ifp-purple'
              : color === 'orange'
              ? 'bg-ifp-orange border-ifp-orange'
              : color === 'green'
              ? 'bg-green-600 border-green-600'
              : 'bg-ifp-purple border-ifp-purple'
            : 'border-charcoal-400'
        }`}
      >
        {checked && <Check className="w-3 h-3 text-white" />}
      </span>
      {label}
    </button>
  );
}

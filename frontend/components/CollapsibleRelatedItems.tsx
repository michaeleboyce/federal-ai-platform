'use client';

import { useState } from 'react';
import Link from 'next/link';

interface BaseMatch {
  similarityScore: number;
  matchSource: 'semantic' | 'text' | 'hybrid';
}

interface ProductMatch extends BaseMatch {
  productFedrampId: string;
  productName: string;
  providerName: string;
}

interface UseCaseMatch extends BaseMatch {
  useCaseId: number;
  useCaseName: string;
  agency: string;
  slug: string;
}

interface CollapsibleRelatedProductsProps {
  items: ProductMatch[];
  type: 'product';
  highThreshold?: number;
  lowThreshold?: number;
  emptyMessage?: string;
}

interface CollapsibleRelatedUseCasesProps {
  items: UseCaseMatch[];
  type: 'useCase';
  highThreshold?: number;
  lowThreshold?: number;
  emptyMessage?: string;
}

type CollapsibleRelatedItemsProps = CollapsibleRelatedProductsProps | CollapsibleRelatedUseCasesProps;

const HIGH_THRESHOLD = 0.75;
const LOW_THRESHOLD = 0.60;

export default function CollapsibleRelatedItems(props: CollapsibleRelatedItemsProps) {
  const {
    items,
    type,
    highThreshold = HIGH_THRESHOLD,
    lowThreshold = LOW_THRESHOLD,
    emptyMessage,
  } = props;

  const [showMore, setShowMore] = useState(false);

  // Split items into tiers
  const primaryItems = items.filter((i) => i.similarityScore >= highThreshold);
  const secondaryItems = items.filter(
    (i) => i.similarityScore >= lowThreshold && i.similarityScore < highThreshold
  );

  if (items.length === 0) {
    return (
      <p className="text-sm text-gov-slate-500">
        {emptyMessage || `No related ${type === 'product' ? 'products' : 'use cases'} found.`}
      </p>
    );
  }

  const renderMatchBadge = (score: number) => (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded ${
        score >= 0.8
          ? 'bg-status-success-light text-status-success-dark border border-status-success'
          : score >= 0.7
          ? 'bg-status-warning-light text-status-warning-dark border border-status-warning'
          : 'bg-gov-slate-100 text-gov-slate-600 border border-gov-slate-300'
      }`}
    >
      {Math.round(score * 100)}% match
    </span>
  );

  const renderSourceBadge = (source: 'semantic' | 'text' | 'hybrid') => (
    <span
      className={`text-xs px-1.5 py-0.5 rounded ${
        source === 'hybrid'
          ? 'bg-ai-indigo-light text-ai-indigo-dark'
          : source === 'semantic'
          ? 'bg-ai-teal-light text-ai-teal-dark'
          : 'bg-gov-slate-100 text-gov-slate-600'
      }`}
    >
      {source}
    </span>
  );

  const renderProductCard = (product: ProductMatch) => (
    <Link
      key={product.productFedrampId}
      href={`/product/${product.productFedrampId}`}
      className="block p-3 bg-gov-slate-50 hover:bg-gov-slate-100 rounded-md border border-gov-slate-200 transition-colors"
    >
      <div className="font-medium text-gov-navy-900 text-sm line-clamp-2">
        {product.productName}
      </div>
      <div className="text-xs text-gov-slate-600 mt-1">{product.providerName}</div>
      <div className="flex items-center justify-between mt-2">
        {renderMatchBadge(product.similarityScore)}
        {renderSourceBadge(product.matchSource)}
      </div>
    </Link>
  );

  const renderUseCaseCard = (useCase: UseCaseMatch) => (
    <Link
      key={useCase.useCaseId}
      href={`/use-cases/${useCase.slug}`}
      className="block p-3 bg-gov-slate-50 hover:bg-gov-slate-100 rounded-md border border-gov-slate-200 transition-colors"
    >
      <div className="font-medium text-gov-navy-900 text-sm line-clamp-2">
        {useCase.useCaseName}
      </div>
      <div className="text-xs text-gov-slate-600 mt-1">{useCase.agency}</div>
      <div className="flex items-center justify-between mt-2">
        {renderMatchBadge(useCase.similarityScore)}
        {renderSourceBadge(useCase.matchSource)}
      </div>
    </Link>
  );

  const renderCard = (item: ProductMatch | UseCaseMatch) => {
    if (type === 'product') {
      return renderProductCard(item as ProductMatch);
    }
    return renderUseCaseCard(item as UseCaseMatch);
  };

  const itemLabel = type === 'product' ? 'product' : 'use case';

  return (
    <div className="space-y-2">
      {/* Primary items - always visible */}
      {primaryItems.map(renderCard)}

      {/* Secondary items - collapsed by default */}
      {showMore && secondaryItems.map(renderCard)}

      {/* Show more/less toggle */}
      {secondaryItems.length > 0 && (
        <button
          onClick={() => setShowMore(!showMore)}
          className="w-full py-2 px-3 text-xs font-medium text-gov-navy-700 hover:text-gov-navy-900 bg-gov-slate-100 hover:bg-gov-slate-200 rounded-md border border-gov-slate-300 transition-colors flex items-center justify-center gap-1"
        >
          {showMore ? (
            <>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
              Show less
            </>
          ) : (
            <>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              {secondaryItems.length} more {itemLabel}
              {secondaryItems.length > 1 ? 's' : ''}
            </>
          )}
        </button>
      )}

      {/* Message when no high-confidence matches */}
      {primaryItems.length === 0 && secondaryItems.length > 0 && !showMore && (
        <p className="text-xs text-gov-slate-500 text-center">
          No high-confidence matches. Click above to see moderate matches.
        </p>
      )}
    </div>
  );
}

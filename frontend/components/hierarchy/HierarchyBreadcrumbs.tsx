'use client';

import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import type { HierarchyBreadcrumb } from '@/lib/db/schema';

export interface HierarchyBreadcrumbsProps {
  breadcrumbs: HierarchyBreadcrumb[];
  showHome?: boolean;
  homeHref?: string;
  homeLabel?: string;
  className?: string;
}

export function HierarchyBreadcrumbs({
  breadcrumbs,
  showHome = true,
  homeHref = '/agencies',
  homeLabel = 'Agencies',
  className = '',
}: HierarchyBreadcrumbsProps) {
  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav className={`flex items-center text-sm ${className}`} aria-label="Breadcrumb">
      <ol className="flex items-center flex-wrap gap-1">
        {/* Home link */}
        {showHome && (
          <li className="flex items-center">
            <Link
              href={homeHref}
              className="flex items-center gap-1 text-charcoal-300 hover:text-cream transition-colors"
            >
              <Home className="w-4 h-4" />
              <span>{homeLabel}</span>
            </Link>
            <ChevronRight className="w-4 h-4 text-charcoal-400 mx-1" />
          </li>
        )}

        {/* Breadcrumb items */}
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;

          return (
            <li key={crumb.id} className="flex items-center">
              {isLast ? (
                <span className="font-medium text-cream">
                  {crumb.abbreviation ? (
                    <>
                      <span className="font-semibold">{crumb.abbreviation}</span>
                      <span className="text-charcoal-400 mx-1">-</span>
                      {crumb.name}
                    </>
                  ) : (
                    crumb.name
                  )}
                </span>
              ) : (
                <>
                  <Link
                    href={`/agencies/${crumb.slug}`}
                    className="text-charcoal-300 hover:text-cream transition-colors"
                  >
                    {crumb.abbreviation || crumb.name}
                  </Link>
                  <ChevronRight className="w-4 h-4 text-charcoal-400 mx-1" />
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default HierarchyBreadcrumbs;

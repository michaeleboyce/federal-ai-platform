import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav className="flex items-center space-x-2 text-sm mb-4" aria-label="Breadcrumb">
      <Link
        href="/"
        className="flex items-center text-charcoal-300 hover:text-cream transition-colors"
        aria-label="Home"
      >
        <Home className="h-4 w-4" />
      </Link>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <div key={index} className="flex items-center space-x-2">
            <ChevronRight className="h-4 w-4 text-charcoal-400" />

            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="text-charcoal-300 hover:text-cream transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-cream font-semibold' : 'text-charcoal-300'}>
                {item.label}
              </span>
            )}
          </div>
        );
      })}
    </nav>
  );
}

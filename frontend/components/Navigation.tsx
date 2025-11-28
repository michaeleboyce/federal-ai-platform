'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  Building2,
  FileText,
  LayoutDashboard,
  Users,
  Shield,
  Package,
  Menu,
  X,
  ChevronDown,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: typeof Building2;
  description?: string;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    description: 'Overview and statistics',
  },
  {
    label: 'AI Services',
    href: '/ai-services',
    icon: Shield,
    description: 'FedRAMP AI catalog',
  },
  {
    label: 'Use Cases',
    href: '/use-cases',
    icon: FileText,
    description: 'AI implementations',
  },
  {
    label: 'Agency Adoption',
    href: '/agency-ai-usage',
    icon: Users,
    description: 'Internal AI tools',
  },
  {
    label: 'Agency Hierarchy',
    href: '/agencies',
    icon: Building2,
    description: 'Org structure',
  },
  {
    label: 'Products',
    href: '/products',
    icon: Package,
    description: 'All FedRAMP products',
  },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <nav className="bg-gov-navy-900 border-b border-gov-navy-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Brand */}
          <Link href="/" className="flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 bg-ai-blue rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <span className="text-white font-bold text-lg">Federal AI Platform</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium
                    transition-colors duration-150
                    ${
                      active
                        ? 'bg-gov-navy-700 text-white'
                        : 'text-gov-navy-100 hover:bg-gov-navy-800 hover:text-white'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-md text-gov-navy-100 hover:text-white hover:bg-gov-navy-800"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-gov-navy-700">
            <div className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      flex items-center gap-3 px-3 py-3 rounded-md text-sm font-medium
                      transition-colors duration-150
                      ${
                        active
                          ? 'bg-gov-navy-700 text-white'
                          : 'text-gov-navy-100 hover:bg-gov-navy-800 hover:text-white'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    <div>
                      <div>{item.label}</div>
                      {item.description && (
                        <div className="text-xs text-gov-navy-300">{item.description}</div>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

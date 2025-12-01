'use client';

import Link from 'next/link';
import { Cpu, ChevronRight } from 'lucide-react';

interface AIService {
  fedrampId: string;
  cloudServiceProvider: string | null;
  cloudServiceOffering: string | null;
  atoIssuanceDate: string | null;
}

interface AgencyAIServicesProps {
  services: AIService[];
  totalCount: number;
  agencyName: string;
}

export default function AgencyAIServices({
  services,
  totalCount,
  agencyName,
}: AgencyAIServicesProps) {
  if (services.length === 0) {
    return null;
  }

  const displayedServices = services.slice(0, 6);
  const hasMore = services.length > 6;

  return (
    <div className="bg-white rounded-lg border border-charcoal-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-charcoal-100 bg-ifp-purple-light/30">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-ifp-purple" />
          <h2 className="font-serif font-medium text-charcoal">
            Authorized AI Services ({totalCount})
          </h2>
        </div>
        <p className="text-xs text-charcoal-500 mt-1">
          FedRAMP-authorized AI/ML products with an ATO from {agencyName}
        </p>
      </div>
      <div className="divide-y divide-charcoal-100">
        {displayedServices.map((service) => (
          <Link
            key={service.fedrampId}
            href={`/product/${service.fedrampId}`}
            className="flex items-center justify-between p-4 hover:bg-cream transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="font-medium text-charcoal">
                {service.cloudServiceOffering || 'Unknown Service'}
              </div>
              <div className="text-sm text-charcoal-500">
                {service.cloudServiceProvider || 'Unknown Provider'}
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              {service.atoIssuanceDate && (
                <span className="text-xs text-charcoal-400">
                  ATO: {service.atoIssuanceDate}
                </span>
              )}
              <ChevronRight className="w-4 h-4 text-charcoal-300" />
            </div>
          </Link>
        ))}
      </div>
      {hasMore && (
        <div className="px-4 py-3 border-t border-charcoal-100 bg-cream">
          <Link
            href={`/products?agency=${encodeURIComponent(agencyName)}`}
            className="text-sm text-ifp-purple hover:text-ifp-purple-dark font-medium"
          >
            View all {services.length} AI services
          </Link>
        </div>
      )}
    </div>
  );
}

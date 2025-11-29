'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Building2, ChevronDown, ChevronRight } from 'lucide-react';

interface Authorization {
  id: number;
  parentAgencyName: string;
  subAgencyName: string | null;
  atoIssuanceDate: string | null;
  organizationSlug: string | null;
}

interface GroupedAuth {
  parentAgency: string;
  subAgencies: Authorization[];
}

interface ProductAuthorizationsProps {
  authorizations: GroupedAuth[];
  totalCount: number;
}

export default function ProductAuthorizations({ authorizations, totalCount }: ProductAuthorizationsProps) {
  const [expandedAgencies, setExpandedAgencies] = useState<Set<string>>(new Set());
  const [showAll, setShowAll] = useState(false);

  const toggleAgency = (agency: string) => {
    const next = new Set(expandedAgencies);
    if (next.has(agency)) {
      next.delete(agency);
    } else {
      next.add(agency);
    }
    setExpandedAgencies(next);
  };

  const displayedAuths = showAll ? authorizations : authorizations.slice(0, 8);

  if (authorizations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-charcoal-200 p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Building2 className="w-6 h-6 text-ifp-purple" />
        <h2 className="font-serif text-2xl font-medium text-charcoal">
          Authorized by {totalCount} {totalCount === 1 ? 'Agency' : 'Agencies'}
        </h2>
      </div>
      <p className="text-charcoal-500 mb-4 text-sm">
        Federal agencies that have issued an Authority to Operate (ATO) for this service.
      </p>

      <div className="space-y-2">
        {displayedAuths.map((group) => (
          <div key={group.parentAgency} className="border border-charcoal-200 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleAgency(group.parentAgency)}
              className="w-full flex items-center justify-between px-4 py-3 bg-cream hover:bg-cream-200 transition-colors text-left"
            >
              <div className="flex items-center gap-2">
                {expandedAgencies.has(group.parentAgency) ? (
                  <ChevronDown className="w-4 h-4 text-charcoal-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-charcoal-500" />
                )}
                <span className="font-medium text-charcoal">{group.parentAgency}</span>
              </div>
              <span className="text-sm text-charcoal-500 bg-charcoal-100 px-2 py-0.5 rounded">
                {group.subAgencies.length} {group.subAgencies.length === 1 ? 'authorization' : 'authorizations'}
              </span>
            </button>

            {expandedAgencies.has(group.parentAgency) && (
              <div className="bg-white border-t border-charcoal-200">
                {group.subAgencies.map((auth) => (
                  <div
                    key={auth.id}
                    className="px-4 py-2 border-b border-charcoal-100 last:border-b-0 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-6" />
                      {auth.organizationSlug ? (
                        <Link
                          href={`/agencies/${auth.organizationSlug}`}
                          className="text-ifp-purple hover:text-ifp-purple-dark underline"
                        >
                          {auth.subAgencyName || auth.parentAgencyName}
                        </Link>
                      ) : (
                        <span className="text-charcoal-700">
                          {auth.subAgencyName || auth.parentAgencyName}
                        </span>
                      )}
                    </div>
                    {auth.atoIssuanceDate && (
                      <span className="text-xs text-charcoal-400">
                        ATO: {auth.atoIssuanceDate}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {authorizations.length > 8 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-4 text-ifp-purple hover:text-ifp-purple-dark text-sm font-medium"
        >
          {showAll ? 'Show fewer agencies' : `View all ${authorizations.length} agencies`}
        </button>
      )}
    </div>
  );
}

'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { Incident } from '@/lib/incident-db';

interface IncidentTableProps {
  incidents: Incident[];
  years: string[];
}

export default function IncidentTable({ incidents, years }: IncidentTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedYear, setSelectedYear] = useState<string>('');

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      // Year filter
      if (selectedYear && incident.date && !incident.date.startsWith(selectedYear)) {
        return false;
      }

      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        const titleMatch = incident.title?.toLowerCase().includes(search);
        const descMatch = incident.description?.toLowerCase().includes(search);
        if (!titleMatch && !descMatch) return false;
      }

      return true;
    });
  }, [incidents, searchTerm, selectedYear]);

  return (
    <div className="bg-white rounded-lg border border-charcoal-200">
      {/* Filters */}
      <div className="p-4 border-b border-charcoal-200">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
            />
          </div>

          {/* Year Filter */}
          <div className="w-40">
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="w-full px-4 py-2 border border-charcoal-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ifp-purple"
            >
              <option value="">All Years</option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-3 text-sm text-charcoal-600">
          Showing {filteredIncidents.length} of {incidents.length} incidents
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-cream-200 border-b-2 border-charcoal-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-600 uppercase tracking-wider">
                ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-600 uppercase tracking-wider">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-600 uppercase tracking-wider">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-600 uppercase tracking-wider">
                Developers
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-charcoal-600 uppercase tracking-wider">
                Reports
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-charcoal-200">
            {filteredIncidents.slice(0, 100).map((incident) => (
              <tr
                key={incident.incidentId}
                className="hover:bg-cream transition-colors"
              >
                <td className="px-4 py-3 text-sm font-medium text-charcoal-700">
                  {incident.incidentId}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/incidents/${incident.incidentId}`}
                    className="text-charcoal-700 hover:text-charcoal hover:underline font-medium"
                  >
                    <span className="line-clamp-2">{incident.title}</span>
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm text-charcoal-600 whitespace-nowrap">
                  {incident.date || '—'}
                </td>
                <td className="px-4 py-3 text-sm text-charcoal-600">
                  <div className="flex flex-wrap gap-1">
                    {(incident.developers as string[] || []).slice(0, 3).map((dev, idx) => (
                      <span
                        key={idx}
                        className="inline-flex px-2 py-0.5 bg-cream-200 text-charcoal-600 rounded text-xs"
                      >
                        {dev}
                      </span>
                    ))}
                    {(incident.developers as string[] || []).length > 3 && (
                      <span className="text-xs text-cream0">
                        +{(incident.developers as string[]).length - 3} more
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-charcoal-600">
                  {incident.reportCount || 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredIncidents.length > 100 && (
          <div className="p-4 text-center text-sm text-charcoal-600 border-t border-charcoal-200">
            Showing first 100 of {filteredIncidents.length} results. Use filters to narrow down.
          </div>
        )}

        {filteredIncidents.length === 0 && (
          <div className="p-8 text-center text-charcoal-600">
            No incidents match your filters.
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useMemo, useState } from 'react';
import { Download, Check, Minus, ChevronDown, ChevronRight } from 'lucide-react';
import type { FederalOrganizationWithAgencies, AgencyUsageData } from '@/lib/hierarchy-db';
import type { AgencyAIUsage } from '@/lib/agency-db';

interface AgencyAdoptionOverviewProps {
  hierarchy: FederalOrganizationWithAgencies[];
  agencies: AgencyAIUsage[]; // Raw data for full export
}

interface DisplayRow {
  id: string;
  type: 'org' | 'agency';
  name: string;
  abbreviation: string | null;
  level: string;
  depth: number;
  hasLlm: boolean;
  hasCoding: boolean;
  llmSources: number;
  codingSources: number;
  totalSources: number;
  isCfoActAgency: boolean;
  hasData: boolean;
  hasChildren: boolean;
  parentKey: string | null;
}

function buildDisplayRows(
  orgs: FederalOrganizationWithAgencies[],
  depth: number = 0,
  parentKey: string | null = null
): DisplayRow[] {
  const result: DisplayRow[] = [];

  // Sort orgs alphabetically by name
  const sortedOrgs = [...orgs].sort((a, b) => {
    const nameA = a.abbreviation || a.name;
    const nameB = b.abbreviation || b.name;
    return nameA.localeCompare(nameB);
  });

  for (const org of sortedOrgs) {
    // Include CFO Act agencies or orgs with data
    if (org.isCfoActAgency || org.aggregatedStats.agencyCount > 0) {
      const key = org.abbreviation || org.name;
      const hasChildren = org.children.some(c => c.aggregatedStats.agencyCount > 0) || org.agencies.length > 0;

      result.push({
        id: `org-${org.id}`,
        type: 'org',
        name: org.name,
        abbreviation: org.abbreviation,
        level: org.level,
        depth,
        hasLlm: org.aggregatedStats.withLlm > 0,
        hasCoding: org.aggregatedStats.withCoding > 0,
        llmSources: org.aggregatedStats.withLlm,
        codingSources: org.aggregatedStats.withCoding,
        totalSources: org.aggregatedStats.agencyCount,
        isCfoActAgency: org.isCfoActAgency,
        hasData: org.aggregatedStats.agencyCount > 0,
        hasChildren,
        parentKey,
      });

      // Add direct agencies under this org (sorted alphabetically)
      const sortedAgencies = [...org.agencies].sort((a, b) => a.agencyName.localeCompare(b.agencyName));
      for (const agency of sortedAgencies) {
        result.push({
          id: `agency-${agency.id}`,
          type: 'agency',
          name: agency.agencyName,
          abbreviation: null,
          level: 'source',
          depth: depth + 1,
          hasLlm: agency.hasStaffLlm?.includes('Yes') || false,
          hasCoding: agency.hasCodingAssistant?.includes('Yes') || agency.hasCodingAssistant?.includes('Allowed') || false,
          llmSources: agency.hasStaffLlm?.includes('Yes') ? 1 : 0,
          codingSources: (agency.hasCodingAssistant?.includes('Yes') || agency.hasCodingAssistant?.includes('Allowed')) ? 1 : 0,
          totalSources: 1,
          isCfoActAgency: false,
          hasData: true,
          hasChildren: false,
          parentKey: key,
        });
      }

      // Add child orgs recursively
      if (org.children.length > 0) {
        result.push(...buildDisplayRows(org.children, depth + 1, key));
      }
    }
  }

  return result;
}

export default function AgencyAdoptionOverview({ hierarchy, agencies }: AgencyAdoptionOverviewProps) {
  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());

  // Build flat display rows with hierarchy info
  const allRows = useMemo(() => buildDisplayRows(hierarchy), [hierarchy]);

  // Get visible rows based on expansion state
  const visibleRows = useMemo(() => {
    const visible: DisplayRow[] = [];
    const expandedPaths = new Set<string>();

    // Build set of all expanded paths
    for (const row of allRows) {
      if (row.depth === 0) {
        expandedPaths.add(row.abbreviation || row.name);
      }
    }

    for (const row of allRows) {
      // Always show top-level orgs
      if (row.depth === 0) {
        visible.push(row);
        continue;
      }

      // Check if parent chain is expanded
      let isVisible = true;
      let currentKey = row.parentKey;
      while (currentKey) {
        if (!expandedOrgs.has(currentKey)) {
          isVisible = false;
          break;
        }
        // Find parent row to get its parent key
        const parentRow = allRows.find(r => (r.abbreviation || r.name) === currentKey);
        currentKey = parentRow?.parentKey || null;
      }

      if (isVisible) {
        visible.push(row);
      }
    }

    return visible;
  }, [allRows, expandedOrgs]);

  const toggleExpand = (key: string) => {
    setExpandedOrgs(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const expandAll = () => {
    const allKeys = allRows
      .filter(r => r.type === 'org' && r.hasChildren)
      .map(r => r.abbreviation || r.name);
    setExpandedOrgs(new Set(allKeys));
  };

  const collapseAll = () => {
    setExpandedOrgs(new Set());
  };

  // Export summary data as CSV
  const exportSummaryCSV = () => {
    const headers = ['Agency', 'Abbreviation', 'Level', 'CFO Act Agency', 'Has Staff LLM', 'Has Coding Assistant', 'LLM Sources', 'Coding Sources', 'Total Sources'];
    const rows = allRows
      .filter(r => r.type === 'org')
      .map(row => [
        '  '.repeat(row.depth) + row.name,
        row.abbreviation || '',
        row.level,
        row.isCfoActAgency ? 'Yes' : 'No',
        row.hasLlm ? 'Yes' : 'No',
        row.hasCoding ? 'Yes' : 'No',
        row.llmSources.toString(),
        row.codingSources.toString(),
        row.totalSources.toString(),
      ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    downloadFile(csvContent, 'text/csv', `agency-ai-adoption-summary-${new Date().toISOString().split('T')[0]}.csv`);
  };

  function downloadFile(content: string, mimeType: string, filename: string) {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Summary stats
  const topLevelOrgs = allRows.filter(r => r.type === 'org' && r.depth === 0);
  const cfoAgencies = topLevelOrgs.filter(a => a.isCfoActAgency);
  const summary = {
    total: topLevelOrgs.length,
    cfoTotal: cfoAgencies.length,
    cfoWithData: cfoAgencies.filter(a => a.hasData).length,
    withBoth: topLevelOrgs.filter(a => a.hasLlm && a.hasCoding).length,
    withLlmOnly: topLevelOrgs.filter(a => a.hasLlm && !a.hasCoding).length,
    withCodingOnly: topLevelOrgs.filter(a => !a.hasLlm && a.hasCoding).length,
    noData: topLevelOrgs.filter(a => !a.hasData).length,
    totalSources: agencies.length,
  };

  return (
    <div className="bg-white rounded-lg border border-gov-slate-200 p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <h2 className="text-xl font-semibold text-gov-navy-900">Agency AI Tool Adoption Summary</h2>
        <button
          onClick={exportSummaryCSV}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gov-navy-700 bg-white border border-gov-slate-300 rounded-md hover:bg-gov-slate-50 transition-colors"
          title="Export summary by agency"
        >
          <Download className="w-3.5 h-3.5" />
          Export Summary
        </button>
      </div>

      {/* Quick Stats */}
      <div className="flex flex-wrap gap-4 mb-4 text-sm">
        <span className="text-gov-slate-600">
          <strong>{summary.cfoWithData}</strong> of {summary.cfoTotal} CFO Act agencies
        </span>
        <span className="text-gov-slate-400">|</span>
        <span className="text-status-success-dark">
          <strong>{summary.withBoth}</strong> both tools
        </span>
        <span className="text-ai-blue-dark">
          <strong>{summary.withLlmOnly}</strong> LLM only
        </span>
        <span className="text-ai-teal-dark">
          <strong>{summary.withCodingOnly}</strong> coding only
        </span>
        <span className="text-gov-slate-400">|</span>
        <span className="text-gov-slate-600">
          <strong>{summary.totalSources}</strong> total data sources
        </span>
      </div>

      {/* Expand/Collapse controls */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={expandAll}
          className="text-xs text-gov-navy-600 hover:text-gov-navy-900 underline"
        >
          Expand All
        </button>
        <button
          onClick={collapseAll}
          className="text-xs text-gov-navy-600 hover:text-gov-navy-900 underline"
        >
          Collapse All
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gov-slate-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gov-slate-100 border-b border-gov-slate-200">
            <tr>
              <th className="px-3 py-2 text-left font-semibold text-gov-navy-900">Agency / Source</th>
              <th className="px-3 py-2 text-center font-semibold text-gov-navy-900 w-24">Staff LLM</th>
              <th className="px-3 py-2 text-center font-semibold text-gov-navy-900 w-24">Coding</th>
              <th className="px-3 py-2 text-right font-semibold text-gov-navy-900 w-20">Sources</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gov-slate-200">
            {visibleRows.map((row, index) => {
              const isOrg = row.type === 'org';
              const key = row.abbreviation || row.name;
              const isExpanded = expandedOrgs.has(key);

              return (
                <tr
                  key={row.id}
                  className={`
                    ${!row.hasData && isOrg ? 'opacity-50' : ''}
                    ${row.type === 'agency' ? 'bg-gov-slate-50/70' : ''}
                    ${index % 2 === 0 && isOrg ? 'bg-white' : isOrg ? 'bg-gov-slate-50/30' : ''}
                  `}
                >
                  <td className="px-3 py-2">
                    <div
                      className="flex items-center gap-2"
                      style={{ paddingLeft: `${row.depth * 1.25}rem` }}
                    >
                      {isOrg && row.hasChildren ? (
                        <button
                          onClick={() => toggleExpand(key)}
                          className="p-0.5 rounded hover:bg-gov-slate-200 shrink-0"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gov-slate-500" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gov-slate-500" />
                          )}
                        </button>
                      ) : (
                        <span className="w-5" />
                      )}
                      <div className="min-w-0">
                        <div className={`${isOrg ? 'font-medium text-gov-navy-900' : 'text-gov-slate-700'}`}>
                          {isOrg && row.abbreviation ? `${row.abbreviation} - ${row.name}` : row.name}
                          {row.isCfoActAgency && (
                            <span className="ml-2 text-xs text-gov-slate-400">(CFO Act)</span>
                          )}
                        </div>
                        {!row.hasData && isOrg && (
                          <div className="text-xs text-gov-slate-400 italic">No public data available</div>
                        )}
                        {row.type === 'agency' && (
                          <div className="text-xs text-gov-slate-500">data source</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {row.hasLlm ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-status-success-light text-status-success-dark">
                        <Check className="w-4 h-4" />
                      </span>
                    ) : (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gov-slate-100 text-gov-slate-400">
                        <Minus className="w-4 h-4" />
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {row.hasCoding ? (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-ai-teal-light text-ai-teal-dark">
                        <Check className="w-4 h-4" />
                      </span>
                    ) : (
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gov-slate-100 text-gov-slate-400">
                        <Minus className="w-4 h-4" />
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right text-gov-slate-600">
                    {row.type === 'agency' ? '—' : (row.totalSources || '—')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-3 text-xs text-gov-slate-500">
        <strong>Note:</strong> Shows all 24 CFO Act agencies plus agencies with data. Click to expand and see sub-agencies and individual data sources.
        <strong> Full Data export</strong> includes all fields: sources, notes, tool details, etc.
      </div>
    </div>
  );
}

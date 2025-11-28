'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { ChevronRight, ChevronDown, Building2, Landmark, Building, FolderOpen, Download, FileSpreadsheet } from 'lucide-react';
import type { FederalOrganizationWithChildren, OrgLevel } from '@/lib/db/schema';

// Icon mapping for organization levels
const levelIcons: Record<OrgLevel, typeof Building2> = {
  department: Landmark,
  independent: Building2,
  sub_agency: Building,
  office: FolderOpen,
  component: FolderOpen,
};

// Color classes for organization levels
const levelColors: Record<OrgLevel, string> = {
  department: 'text-ai-indigo',
  independent: 'text-ai-blue',
  sub_agency: 'text-slate-600',
  office: 'text-slate-500',
  component: 'text-slate-400',
};

interface TreeNodeProps {
  organization: FederalOrganizationWithChildren;
  depth: number;
  expandedIds: Set<number>;
  selectedId?: number;
  onToggle: (id: number) => void;
  onSelect?: (org: FederalOrganizationWithChildren) => void;
  linkMode?: 'detail' | 'use-cases' | 'none';
  showCounts?: boolean;
  useCaseCounts?: Record<number, number>;
}

function TreeNode({
  organization,
  depth,
  expandedIds,
  selectedId,
  onToggle,
  onSelect,
  linkMode = 'detail',
  showCounts = false,
  useCaseCounts = {},
}: TreeNodeProps) {
  const hasChildren = organization.children && organization.children.length > 0;
  const isExpanded = expandedIds.has(organization.id);
  const isSelected = selectedId === organization.id;
  const Icon = levelIcons[organization.level as OrgLevel] || Building;
  const colorClass = levelColors[organization.level as OrgLevel] || 'text-slate-500';
  const count = useCaseCounts[organization.id] || 0;

  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (hasChildren) {
        onToggle(organization.id);
      }
    },
    [hasChildren, onToggle, organization.id]
  );

  const handleSelect = useCallback(() => {
    if (onSelect) {
      onSelect(organization);
    }
  }, [onSelect, organization]);

  const content = (
    <div
      className={`
        flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer
        transition-colors duration-150
        ${isSelected ? 'bg-ai-blue-light text-ai-blue-dark' : 'hover:bg-slate-100'}
      `}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
      onClick={handleSelect}
    >
      {/* Expand/Collapse Button */}
      <button
        onClick={handleToggle}
        className={`
          flex-shrink-0 w-5 h-5 flex items-center justify-center rounded
          ${hasChildren ? 'hover:bg-slate-200' : 'invisible'}
        `}
      >
        {hasChildren &&
          (isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-500" />
          ))}
      </button>

      {/* Icon */}
      <Icon className={`w-4 h-4 flex-shrink-0 ${colorClass}`} />

      {/* Organization Name */}
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium text-slate-800 truncate">
          {organization.abbreviation && (
            <span className="font-semibold">{organization.abbreviation}</span>
          )}
          {organization.abbreviation && ' - '}
          <span className={organization.abbreviation ? 'font-normal' : ''}>
            {organization.name}
          </span>
        </span>
      </div>

      {/* CFO Act Badge */}
      {organization.isCfoActAgency && (
        <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium bg-status-success-light text-status-success-dark border border-status-success rounded">
          CFO
        </span>
      )}

      {/* Use Case Count */}
      {showCounts && count > 0 && (
        <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium bg-slate-100 text-slate-600 rounded">
          {count}
        </span>
      )}
    </div>
  );

  // Wrap in Link if linkMode is set
  const wrappedContent =
    linkMode === 'detail' ? (
      <Link href={`/agencies/${organization.slug}`}>{content}</Link>
    ) : linkMode === 'use-cases' ? (
      <Link href={`/use-cases?organization=${organization.id}`}>{content}</Link>
    ) : (
      content
    );

  return (
    <div>
      {wrappedContent}
      {hasChildren && isExpanded && (
        <div>
          {organization.children.map((child) => (
            <TreeNode
              key={child.id}
              organization={child}
              depth={depth + 1}
              expandedIds={expandedIds}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
              linkMode={linkMode}
              showCounts={showCounts}
              useCaseCounts={useCaseCounts}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export interface AgencyHierarchyTreeProps {
  organizations: FederalOrganizationWithChildren[];
  selectedId?: number;
  onSelect?: (org: FederalOrganizationWithChildren) => void;
  linkMode?: 'detail' | 'use-cases' | 'none';
  showCounts?: boolean;
  useCaseCounts?: Record<number, number>;
  defaultExpandedIds?: number[];
  expandAll?: boolean;
  className?: string;
}

export function AgencyHierarchyTree({
  organizations,
  selectedId,
  onSelect,
  linkMode = 'detail',
  showCounts = false,
  useCaseCounts = {},
  defaultExpandedIds = [],
  expandAll = false,
  className = '',
}: AgencyHierarchyTreeProps) {
  // Initialize expanded state
  const [expandedIds, setExpandedIds] = useState<Set<number>>(() => {
    if (expandAll) {
      // Collect all organization IDs
      const allIds = new Set<number>();
      const collectIds = (orgs: FederalOrganizationWithChildren[]) => {
        orgs.forEach((org) => {
          allIds.add(org.id);
          if (org.children) {
            collectIds(org.children);
          }
        });
      };
      collectIds(organizations);
      return allIds;
    }
    return new Set(defaultExpandedIds);
  });

  const handleToggle = useCallback((id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const expandAllNodes = useCallback(() => {
    const allIds = new Set<number>();
    const collectIds = (orgs: FederalOrganizationWithChildren[]) => {
      orgs.forEach((org) => {
        allIds.add(org.id);
        if (org.children) {
          collectIds(org.children);
        }
      });
    };
    collectIds(organizations);
    setExpandedIds(allIds);
  }, [organizations]);

  const collapseAllNodes = useCallback(() => {
    setExpandedIds(new Set());
  }, []);

  // Flatten hierarchy for export
  const flattenHierarchy = useCallback((orgs: FederalOrganizationWithChildren[], parentName: string | null = null, depth: number = 0): Array<{
    name: string;
    abbreviation: string;
    level: string;
    parentName: string;
    depth: number;
    isCfoActAgency: boolean;
    isCabinetDepartment: boolean;
    slug: string;
    website: string;
    description: string;
  }> => {
    const result: Array<{
      name: string;
      abbreviation: string;
      level: string;
      parentName: string;
      depth: number;
      isCfoActAgency: boolean;
      isCabinetDepartment: boolean;
      slug: string;
      website: string;
      description: string;
    }> = [];

    for (const org of orgs) {
      result.push({
        name: org.name,
        abbreviation: org.abbreviation || '',
        level: org.level,
        parentName: parentName || '',
        depth,
        isCfoActAgency: org.isCfoActAgency,
        isCabinetDepartment: org.isCabinetDepartment,
        slug: org.slug,
        website: org.website || '',
        description: org.description || '',
      });

      if (org.children && org.children.length > 0) {
        result.push(...flattenHierarchy(org.children, org.abbreviation || org.name, depth + 1));
      }
    }

    return result;
  }, []);

  // Export as CSV
  const exportCSV = useCallback(() => {
    const data = flattenHierarchy(organizations);
    const headers = ['Name', 'Abbreviation', 'Level', 'Parent', 'Depth', 'CFO Act Agency', 'Cabinet Department', 'Slug', 'Website', 'Description'];

    const rows = data.map(row => [
      row.name,
      row.abbreviation,
      row.level,
      row.parentName,
      row.depth.toString(),
      row.isCfoActAgency ? 'Yes' : 'No',
      row.isCabinetDepartment ? 'Yes' : 'No',
      row.slug,
      row.website,
      row.description,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `federal-agency-hierarchy-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [organizations, flattenHierarchy]);

  // Export as Excel
  const exportExcel = useCallback(() => {
    const data = flattenHierarchy(organizations);
    const headers = ['Name', 'Abbreviation', 'Level', 'Parent', 'Depth', 'CFO Act Agency', 'Cabinet Department', 'Slug', 'Website', 'Description'];

    const rows = data.map(row => [
      row.name,
      row.abbreviation,
      row.level,
      row.parentName,
      row.depth.toString(),
      row.isCfoActAgency ? 'Yes' : 'No',
      row.isCabinetDepartment ? 'Yes' : 'No',
      row.slug,
      row.website,
      row.description,
    ]);

    const tsvContent = [
      headers.join('\t'),
      ...rows.map(row => row.map(cell => String(cell).replace(/\t/g, ' ').replace(/\n/g, ' ')).join('\t'))
    ].join('\n');

    const blob = new Blob([tsvContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `federal-agency-hierarchy-${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [organizations, flattenHierarchy]);

  return (
    <div className={`${className}`}>
      {/* Controls */}
      <div className="flex items-center justify-between gap-2 mb-3 px-2">
        <div className="flex items-center gap-2">
          <button
            onClick={expandAllNodes}
            className="text-xs text-ai-blue hover:text-ai-blue-dark"
          >
            Expand All
          </button>
          <span className="text-slate-300">|</span>
          <button
            onClick={collapseAllNodes}
            className="text-xs text-ai-blue hover:text-ai-blue-dark"
          >
            Collapse All
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportCSV}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 bg-white border border-slate-300 rounded hover:bg-slate-50 transition-colors"
            title="Export hierarchy as CSV"
          >
            <Download className="w-3 h-3" />
            CSV
          </button>
          <button
            onClick={exportExcel}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 bg-white border border-slate-300 rounded hover:bg-slate-50 transition-colors"
            title="Export hierarchy as Excel"
          >
            <FileSpreadsheet className="w-3 h-3" />
            Excel
          </button>
        </div>
      </div>

      {/* Tree */}
      <div className="space-y-0.5">
        {organizations.map((org) => (
          <TreeNode
            key={org.id}
            organization={org}
            depth={0}
            expandedIds={expandedIds}
            selectedId={selectedId}
            onToggle={handleToggle}
            onSelect={onSelect}
            linkMode={linkMode}
            showCounts={showCounts}
            useCaseCounts={useCaseCounts}
          />
        ))}
      </div>
    </div>
  );
}

export default AgencyHierarchyTree;

'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { ChevronDown, Search, X, Building2, Landmark, Building } from 'lucide-react';
import type { FederalOrganization, OrgLevel } from '@/lib/db/schema';

// Icon mapping for organization levels
const levelIcons: Record<OrgLevel, typeof Building2> = {
  department: Landmark,
  independent: Building2,
  sub_agency: Building,
  office: Building,
  component: Building,
};

export interface AgencyFilterDropdownProps {
  organizations: (FederalOrganization & { parentName: string | null })[];
  selectedId: number | null;
  onSelect: (id: number | null, includeDescendants: boolean) => void;
  placeholder?: string;
  showIncludeDescendants?: boolean;
  className?: string;
}

export function AgencyFilterDropdown({
  organizations,
  selectedId,
  onSelect,
  placeholder = 'All Agencies',
  showIncludeDescendants = true,
  className = '',
}: AgencyFilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [includeDescendants, setIncludeDescendants] = useState(true);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Filter organizations based on search
  const filteredOrganizations = useMemo(() => {
    if (!searchQuery.trim()) return organizations;
    const query = searchQuery.toLowerCase();
    return organizations.filter(
      (org) =>
        org.name.toLowerCase().includes(query) ||
        (org.abbreviation && org.abbreviation.toLowerCase().includes(query)) ||
        (org.parentName && org.parentName.toLowerCase().includes(query))
    );
  }, [organizations, searchQuery]);

  // Get selected organization
  const selectedOrg = selectedId ? organizations.find((o) => o.id === selectedId) : null;

  const handleSelect = (id: number | null) => {
    onSelect(id, includeDescendants);
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(null, includeDescendants);
    setSearchQuery('');
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center justify-between w-full px-3 py-2 text-sm
          bg-white border border-slate-300 rounded-lg
          hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-ai-blue focus:border-ai-blue
          ${isOpen ? 'ring-2 ring-ai-blue border-ai-blue' : ''}
        `}
      >
        <span className={selectedOrg ? 'text-slate-900' : 'text-slate-500'}>
          {selectedOrg ? (
            <span className="flex items-center gap-2">
              {selectedOrg.abbreviation && (
                <span className="font-semibold">{selectedOrg.abbreviation}</span>
              )}
              {selectedOrg.abbreviation && <span className="text-slate-300">|</span>}
              <span className="truncate">{selectedOrg.name}</span>
            </span>
          ) : (
            placeholder
          )}
        </span>
        <div className="flex items-center gap-1">
          {selectedOrg && (
            <span
              role="button"
              tabIndex={0}
              onClick={handleClear}
              onKeyDown={(e) => e.key === 'Enter' && handleClear(e as unknown as React.MouseEvent)}
              className="p-0.5 hover:bg-slate-100 rounded cursor-pointer"
            >
              <X className="w-4 h-4 text-slate-400" />
            </span>
          )}
          <ChevronDown
            className={`w-4 h-4 text-slate-400 transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
          {/* Search Input */}
          <div className="p-2 border-b border-slate-100">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agencies..."
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ai-blue focus:border-ai-blue"
              />
            </div>
          </div>

          {/* Include Descendants Toggle */}
          {showIncludeDescendants && selectedId && (
            <div className="px-3 py-2 border-b border-slate-100 bg-slate-50">
              <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeDescendants}
                  onChange={(e) => {
                    setIncludeDescendants(e.target.checked);
                    onSelect(selectedId, e.target.checked);
                  }}
                  className="rounded border-slate-300 text-ai-blue focus:ring-ai-blue"
                />
                Include sub-agencies
              </label>
            </div>
          )}

          {/* Options */}
          <div className="max-h-56 overflow-y-auto">
            {/* All Agencies Option */}
            <button
              onClick={() => handleSelect(null)}
              className={`
                w-full px-3 py-2 text-left text-sm hover:bg-slate-50
                ${!selectedId ? 'bg-ai-blue-light text-ai-blue-dark font-medium' : ''}
              `}
            >
              {placeholder}
            </button>

            {/* Organization List */}
            {filteredOrganizations.map((org) => {
              const Icon = levelIcons[org.level as OrgLevel] || Building;
              const isSelected = selectedId === org.id;

              return (
                <button
                  key={org.id}
                  onClick={() => handleSelect(org.id)}
                  className={`
                    w-full px-3 py-2 text-left text-sm hover:bg-slate-50
                    ${isSelected ? 'bg-ai-blue-light text-ai-blue-dark' : ''}
                  `}
                  style={{ paddingLeft: `${org.depth * 12 + 12}px` }}
                >
                  <div className="flex items-center gap-2">
                    <Icon
                      className={`w-4 h-4 flex-shrink-0 ${
                        org.level === 'department'
                          ? 'text-ai-indigo'
                          : org.level === 'independent'
                          ? 'text-ai-blue'
                          : 'text-slate-400'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {org.abbreviation && (
                          <span className="font-semibold">{org.abbreviation}</span>
                        )}
                        {org.abbreviation && org.depth > 0 && (
                          <span className="text-slate-300">-</span>
                        )}
                        <span className="truncate">{org.name}</span>
                      </div>
                      {org.parentName && org.depth > 0 && (
                        <div className="text-xs text-slate-400 truncate">
                          {org.parentName}
                        </div>
                      )}
                    </div>
                    {org.isCfoActAgency && (
                      <span className="flex-shrink-0 px-1 py-0.5 text-[9px] font-medium bg-status-success-light text-status-success-dark rounded">
                        CFO
                      </span>
                    )}
                  </div>
                </button>
              );
            })}

            {filteredOrganizations.length === 0 && (
              <div className="px-3 py-4 text-center text-sm text-slate-500">
                No agencies found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AgencyFilterDropdown;

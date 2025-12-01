'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  logoutAction,
  updateProfileAction,
  deleteProfileAction,
  createToolAction,
  updateToolAction,
  deleteToolAction,
  createProfileFromOrgAction,
} from './actions';
import type { AgencyProfileWithTools, ToolStats, FederalOrgWithProfileStatus } from '@/lib/agency-tools-db';
import type { AgencyAiTool, ProductType } from '@/lib/db/schema';
import { ChevronDown, ChevronRight, Plus, Trash2, Save, X, ExternalLink, Building2 } from 'lucide-react';

type ViewMode = 'with_use_cases' | 'all_agencies';

interface AdminPanelProps {
  initialProfiles: AgencyProfileWithTools[];
  initialStats: ToolStats;
  initialFederalOrgs: FederalOrgWithProfileStatus[];
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .trim();
}

export default function AdminPanel({ initialProfiles, initialStats, initialFederalOrgs }: AdminPanelProps) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [federalOrgs, setFederalOrgs] = useState(initialFederalOrgs);
  const [stats] = useState(initialStats);
  const [viewMode, setViewMode] = useState<ViewMode>('with_use_cases');
  const [expandedProfiles, setExpandedProfiles] = useState<Set<number>>(new Set());
  const [expandedOrgs, setExpandedOrgs] = useState<Set<number>>(new Set());
  const [editingTool, setEditingTool] = useState<number | null>(null);
  const [editingProfile, setEditingProfile] = useState<number | null>(null);
  const [addingToolTo, setAddingToolTo] = useState<number | null>(null);
  const [addingToolToOrg, setAddingToolToOrg] = useState<number | null>(null);
  const [creatingProfileForOrg, setCreatingProfileForOrg] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();

  // Filter profiles to only show those with actual tools
  const profilesWithTools = profiles.filter(p => p.toolCount > 0);

  // Filter federal orgs based on search query
  const filteredFederalOrgs = federalOrgs.filter(org => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      org.name.toLowerCase().includes(query) ||
      (org.abbreviation?.toLowerCase().includes(query)) ||
      (org.shortName?.toLowerCase().includes(query))
    );
  });

  async function handleLogout() {
    await logoutAction();
    router.refresh();
  }

  function toggleProfile(id: number) {
    setExpandedProfiles(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleDeleteProfile(id: number) {
    if (!confirm('Delete this agency and all its tools?')) return;
    const result = await deleteProfileAction(id);
    if (result.success) {
      setProfiles(prev => prev.filter(p => p.id !== id));
      // Also update federal orgs to reflect the deleted profile
      setFederalOrgs(prev => prev.map(org =>
        org.profileId === id
          ? { ...org, hasProfile: false, profileId: null, toolCount: 0, tools: [], hasStaffChatbot: false, hasCodingAssistant: false, hasDocumentAutomation: false }
          : org
      ));
    }
  }

  function toggleOrg(id: number) {
    setExpandedOrgs(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleCreateProfileFromOrg(orgId: number) {
    setCreatingProfileForOrg(orgId);
    const result = await createProfileFromOrgAction(orgId);
    setCreatingProfileForOrg(null);

    if (result.success && result.profileId) {
      // Refresh to get the new profile data
      router.refresh();
    }
  }

  async function handleDeleteTool(toolId: number, profileId: number) {
    if (!confirm('Delete this tool?')) return;
    const result = await deleteToolAction(toolId);
    if (result.success) {
      setProfiles(prev =>
        prev.map(p =>
          p.id === profileId
            ? { ...p, tools: p.tools.filter(t => t.id !== toolId), toolCount: p.toolCount - 1 }
            : p
        )
      );
    }
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-charcoal text-white py-4 px-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold font-serif">Admin Panel</h1>
            <p className="text-sm text-charcoal-300">Manage Agency AI Tools</p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/admin/products"
              className="text-sm text-charcoal-300 hover:text-white transition-colors"
            >
              FedRAMP Products →
            </Link>
            <button
              onClick={handleLogout}
              className="bg-charcoal-600 hover:bg-charcoal-500 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-charcoal">{profiles.length}</div>
            <div className="text-sm text-charcoal-600">Agencies</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-ifp-purple">{stats.staffChatbot}</div>
            <div className="text-sm text-charcoal-600">Chatbots</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-ifp-orange">{stats.codingAssistant}</div>
            <div className="text-sm text-charcoal-600">Coding Assistants</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-green-600">{stats.documentAutomation}</div>
            <div className="text-sm text-charcoal-600">Doc Automation</div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setViewMode('with_use_cases')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'with_use_cases'
                ? 'bg-ifp-purple text-white'
                : 'bg-white text-charcoal-600 hover:bg-charcoal-100'
            }`}
          >
            With AI Tools ({profilesWithTools.length})
          </button>
          <button
            onClick={() => setViewMode('all_agencies')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'all_agencies'
                ? 'bg-ifp-purple text-white'
                : 'bg-white text-charcoal-600 hover:bg-charcoal-100'
            }`}
          >
            All Agencies ({federalOrgs.length})
          </button>
        </div>

        {/* Agency List - With AI Tools View */}
        {viewMode === 'with_use_cases' && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b border-charcoal-200">
            <h2 className="font-semibold text-charcoal">Agencies with AI Tools</h2>
          </div>

          <div className="divide-y divide-charcoal-100">
            {profilesWithTools.map(profile => (
              <div key={profile.id}>
                {/* Profile Row */}
                <div
                  className={`flex items-center gap-3 p-4 hover:bg-cream cursor-pointer ${
                    editingProfile === profile.id ? 'bg-ifp-purple-light' : ''
                  }`}
                  onClick={() => toggleProfile(profile.id)}
                >
                  <button className="text-charcoal-400">
                    {expandedProfiles.has(profile.id) ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                  </button>

                  <div className="flex-1">
                    <div className="font-medium text-charcoal">
                      {profile.abbreviation && (
                        <span className="text-ifp-purple font-semibold mr-2">
                          {profile.abbreviation}
                        </span>
                      )}
                      {profile.agencyName}
                    </div>
                    <div className="text-sm text-charcoal-500">
                      {profile.toolCount} tool{profile.toolCount !== 1 ? 's' : ''}
                      {profile.parentAbbreviation && ` • Parent: ${profile.parentAbbreviation}`}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {profile.hasStaffChatbot && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                        Chatbot
                      </span>
                    )}
                    {profile.hasCodingAssistant && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                        Coding
                      </span>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteProfile(profile.id);
                    }}
                    className="text-red-400 hover:text-red-600 p-1"
                    title="Delete agency"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Expanded Tools */}
                {expandedProfiles.has(profile.id) && (
                  <div className="bg-cream-light border-t border-charcoal-100">
                    {profile.tools.length === 0 ? (
                      <div className="p-4 pl-12 text-charcoal-500 italic text-sm">
                        No tools identified
                      </div>
                    ) : (
                      profile.tools.map(tool => (
                        <ToolRow
                          key={tool.id}
                          tool={tool}
                          isEditing={editingTool === tool.id}
                          onEdit={() => setEditingTool(tool.id)}
                          onCancelEdit={() => setEditingTool(null)}
                          onSave={async (data) => {
                            await updateToolAction(tool.id, data);
                            setEditingTool(null);
                            router.refresh();
                          }}
                          onDelete={() => handleDeleteTool(tool.id, profile.id)}
                        />
                      ))
                    )}

                    {/* Add Tool Button */}
                    {addingToolTo === profile.id ? (
                      <AddToolForm
                        profileId={profile.id}
                        profileSlug={profile.slug}
                        onCancel={() => setAddingToolTo(null)}
                        onSave={async (data) => {
                          await createToolAction(data);
                          setAddingToolTo(null);
                          router.refresh();
                        }}
                      />
                    ) : (
                      <button
                        onClick={() => setAddingToolTo(profile.id)}
                        className="flex items-center gap-2 p-3 pl-12 text-ifp-purple hover:bg-ifp-purple-light w-full text-left text-sm"
                      >
                        <Plus className="w-4 h-4" />
                        Add Tool
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        )}

        {/* All Agencies View */}
        {viewMode === 'all_agencies' && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b border-charcoal-200">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="font-semibold text-charcoal">All Federal Organizations</h2>
                <p className="text-sm text-charcoal-500 mt-1">
                  {federalOrgs.filter(o => o.hasProfile).length} of {federalOrgs.length} agencies have AI tools tracked
                </p>
              </div>
            </div>
            {/* Search Input */}
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search agencies by name or abbreviation..."
              className="w-full px-4 py-2 border border-charcoal-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ifp-purple focus:border-transparent"
            />
            {searchQuery && (
              <p className="text-xs text-charcoal-500 mt-2">
                Showing {filteredFederalOrgs.length} of {federalOrgs.length} agencies
              </p>
            )}
            {/* Legend */}
            <div className="flex items-center gap-4 mt-3 text-xs text-charcoal-500">
              <span className="flex items-center gap-1">
                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full">N tools</span>
                = Has AI tools
              </span>
              <span className="flex items-center gap-1">
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">Profile only</span>
                = Profile exists, no tools yet
              </span>
              <span className="flex items-center gap-1">
                <span className="px-2 py-0.5 bg-charcoal-100 text-charcoal-500 rounded-full">No profile</span>
                = Not tracked yet
              </span>
            </div>
          </div>

          <div className="divide-y divide-charcoal-100 max-h-[600px] overflow-y-auto">
            {filteredFederalOrgs.map(org => (
              <div key={org.id}>
                {/* Org Row */}
                <div
                  className={`flex items-center gap-3 p-4 hover:bg-cream cursor-pointer ${
                    org.hasProfile ? '' : 'bg-charcoal-50'
                  }`}
                  onClick={() => org.hasProfile && toggleOrg(org.id)}
                >
                  {org.hasProfile ? (
                    <button className="text-charcoal-400">
                      {expandedOrgs.has(org.id) ? (
                        <ChevronDown className="w-5 h-5" />
                      ) : (
                        <ChevronRight className="w-5 h-5" />
                      )}
                    </button>
                  ) : (
                    <div className="w-5 h-5 flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-charcoal-300" />
                    </div>
                  )}

                  <div className="flex-1">
                    <div className="font-medium text-charcoal flex items-center gap-2">
                      {org.abbreviation && (
                        <span className={`font-semibold ${org.hasProfile ? 'text-ifp-purple' : 'text-charcoal-400'}`}>
                          {org.abbreviation}
                        </span>
                      )}
                      <span className={org.hasProfile ? '' : 'text-charcoal-500'}>{org.name}</span>
                      {/* Status badge */}
                      {org.hasProfile ? (
                        org.toolCount > 0 ? (
                          <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                            {org.toolCount} tool{org.toolCount !== 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
                            Profile only
                          </span>
                        )
                      ) : (
                        <span className="px-2 py-0.5 text-xs bg-charcoal-100 text-charcoal-500 rounded-full">
                          No profile
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-charcoal-500">
                      {org.level && (
                        <span className="text-charcoal-400 capitalize">
                          {org.level.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {org.hasStaffChatbot && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-purple-light text-ifp-purple rounded-full">
                        Chatbot
                      </span>
                    )}
                    {org.hasCodingAssistant && (
                      <span className="px-2 py-0.5 text-xs bg-ifp-orange-light text-ifp-orange rounded-full">
                        Coding
                      </span>
                    )}
                    {org.hasDocumentAutomation && (
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                        Doc Auto
                      </span>
                    )}
                  </div>

                  {/* Create Profile button for orgs without profiles */}
                  {!org.hasProfile && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCreateProfileFromOrg(org.id);
                      }}
                      disabled={creatingProfileForOrg === org.id}
                      className="flex items-center gap-1 px-3 py-1.5 bg-ifp-purple text-white text-sm rounded hover:bg-ifp-purple-dark disabled:opacity-50"
                    >
                      <Plus className="w-4 h-4" />
                      {creatingProfileForOrg === org.id ? 'Creating...' : 'Create Profile'}
                    </button>
                  )}

                  {/* Delete button for orgs with profiles */}
                  {org.hasProfile && org.profileId && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProfile(org.profileId!);
                      }}
                      className="text-red-400 hover:text-red-600 p-1"
                      title="Delete agency profile"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Expanded Tools for orgs with profiles */}
                {org.hasProfile && expandedOrgs.has(org.id) && (
                  <div className="bg-cream-light border-t border-charcoal-100">
                    {org.tools.length === 0 ? (
                      <div className="p-4 pl-12 text-charcoal-500 italic text-sm">
                        No tools identified
                      </div>
                    ) : (
                      org.tools.map(tool => (
                        <ToolRow
                          key={tool.id}
                          tool={tool}
                          isEditing={editingTool === tool.id}
                          onEdit={() => setEditingTool(tool.id)}
                          onCancelEdit={() => setEditingTool(null)}
                          onSave={async (data) => {
                            await updateToolAction(tool.id, data);
                            setEditingTool(null);
                            router.refresh();
                          }}
                          onDelete={() => org.profileId && handleDeleteTool(tool.id, org.profileId)}
                        />
                      ))
                    )}

                    {/* Add Tool Button */}
                    {org.profileId && (
                      addingToolToOrg === org.id ? (
                        <AddToolForm
                          profileId={org.profileId}
                          profileSlug={org.slug}
                          onCancel={() => setAddingToolToOrg(null)}
                          onSave={async (data) => {
                            await createToolAction(data);
                            setAddingToolToOrg(null);
                            router.refresh();
                          }}
                        />
                      ) : (
                        <button
                          onClick={() => setAddingToolToOrg(org.id)}
                          className="flex items-center gap-2 p-3 pl-12 text-ifp-purple hover:bg-ifp-purple-light w-full text-left text-sm"
                        >
                          <Plus className="w-4 h-4" />
                          Add Tool
                        </button>
                      )
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        )}
      </div>
    </div>
  );
}

// ========================================
// TOOL ROW COMPONENT
// ========================================

interface ToolRowProps {
  tool: AgencyAiTool;
  isEditing: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSave: (data: {
    productName?: string;
    productType?: ProductType;
    availableToAllStaff?: string;
    isPilotOrLimited?: boolean;
    citationUrl?: string;
  }) => Promise<void>;
  onDelete: () => void;
}

function ToolRow({ tool, isEditing, onEdit, onCancelEdit, onSave, onDelete }: ToolRowProps) {
  const [formData, setFormData] = useState({
    productName: tool.productName,
    productType: tool.productType,
    availableToAllStaff: tool.availableToAllStaff || '',
    isPilotOrLimited: tool.isPilotOrLimited || false,
    citationUrl: tool.citationUrl || '',
  });
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    setIsSaving(true);
    await onSave(formData);
    setIsSaving(false);
  }

  if (isEditing) {
    return (
      <div className="p-4 pl-12 bg-ifp-orange-light border-b border-charcoal-100">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Product Name</label>
            <input
              type="text"
              value={formData.productName}
              onChange={(e) => setFormData(prev => ({ ...prev, productName: e.target.value }))}
              className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Type</label>
            <select
              value={formData.productType}
              onChange={(e) => setFormData(prev => ({ ...prev, productType: e.target.value as ProductType }))}
              className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            >
              <option value="staff_chatbot">Staff Chatbot</option>
              <option value="coding_assistant">Coding Assistant</option>
              <option value="document_automation">Document Automation</option>
              <option value="none_identified">None Identified</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Available to All Staff</label>
            <select
              value={formData.availableToAllStaff}
              onChange={(e) => setFormData(prev => ({ ...prev, availableToAllStaff: e.target.value }))}
              className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            >
              <option value="">Unknown</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
              <option value="subset">Subset</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">Pilot/Limited</label>
            <select
              value={formData.isPilotOrLimited ? 'yes' : 'no'}
              onChange={(e) => setFormData(prev => ({ ...prev, isPilotOrLimited: e.target.value === 'yes' }))}
              className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            >
              <option value="no">No</option>
              <option value="yes">Yes</option>
            </select>
          </div>
        </div>
        <div className="mb-4">
          <label className="block text-xs font-medium text-charcoal mb-1">Citation URL</label>
          <input
            type="url"
            value={formData.citationUrl}
            onChange={(e) => setFormData(prev => ({ ...prev, citationUrl: e.target.value }))}
            className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            placeholder="https://..."
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1 px-3 py-1.5 bg-ifp-purple text-white text-sm rounded hover:bg-ifp-purple-dark disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={onCancelEdit}
            className="flex items-center gap-1 px-3 py-1.5 bg-charcoal-200 text-charcoal text-sm rounded hover:bg-charcoal-300"
          >
            <X className="w-4 h-4" />
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex items-center gap-3 p-3 pl-12 hover:bg-cream border-b border-charcoal-100 cursor-pointer"
      onClick={onEdit}
    >
      <div className="flex-1">
        <span className="text-sm font-medium text-charcoal">{tool.productName}</span>
      </div>

      <ProductTypeBadge type={tool.productType} />

      {tool.isPilotOrLimited && (
        <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full">
          Pilot
        </span>
      )}

      {tool.citationUrl && (
        <a
          href={tool.citationUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-charcoal-400 hover:text-ifp-purple"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      )}

      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="text-red-400 hover:text-red-600 p-1"
        title="Delete tool"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

// ========================================
// ADD TOOL FORM
// ========================================

interface AddToolFormProps {
  profileId: number;
  profileSlug: string;
  onCancel: () => void;
  onSave: (data: {
    agencyProfileId: number;
    productName: string;
    productType: ProductType;
    slug: string;
    availableToAllStaff?: string;
    isPilotOrLimited?: boolean;
    citationUrl?: string;
  }) => Promise<void>;
}

function AddToolForm({ profileId, profileSlug, onCancel, onSave }: AddToolFormProps) {
  const [formData, setFormData] = useState({
    productName: '',
    productType: 'staff_chatbot' as ProductType,
    availableToAllStaff: '',
    isPilotOrLimited: false,
    citationUrl: '',
  });
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    if (!formData.productName.trim()) return;

    setIsSaving(true);
    await onSave({
      agencyProfileId: profileId,
      productName: formData.productName,
      productType: formData.productType,
      slug: `${profileSlug}-${slugify(formData.productName)}-${Date.now()}`,
      availableToAllStaff: formData.availableToAllStaff || undefined,
      isPilotOrLimited: formData.isPilotOrLimited,
      citationUrl: formData.citationUrl || undefined,
    });
    setIsSaving(false);
  }

  return (
    <div className="p-4 pl-12 bg-ifp-purple-light border-b border-charcoal-100">
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Product Name *</label>
          <input
            type="text"
            value={formData.productName}
            onChange={(e) => setFormData(prev => ({ ...prev, productName: e.target.value }))}
            className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
            placeholder="e.g., ChatGPT Enterprise"
            autoFocus
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Type</label>
          <select
            value={formData.productType}
            onChange={(e) => setFormData(prev => ({ ...prev, productType: e.target.value as ProductType }))}
            className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
          >
            <option value="staff_chatbot">Staff Chatbot</option>
            <option value="coding_assistant">Coding Assistant</option>
            <option value="document_automation">Document Automation</option>
            <option value="none_identified">None Identified</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Available to All Staff</label>
          <select
            value={formData.availableToAllStaff}
            onChange={(e) => setFormData(prev => ({ ...prev, availableToAllStaff: e.target.value }))}
            className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
          >
            <option value="">Unknown</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="subset">Subset</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-charcoal mb-1">Pilot/Limited</label>
          <select
            value={formData.isPilotOrLimited ? 'yes' : 'no'}
            onChange={(e) => setFormData(prev => ({ ...prev, isPilotOrLimited: e.target.value === 'yes' }))}
            className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
          >
            <option value="no">No</option>
            <option value="yes">Yes</option>
          </select>
        </div>
      </div>
      <div className="mb-4">
        <label className="block text-xs font-medium text-charcoal mb-1">Citation URL</label>
        <input
          type="url"
          value={formData.citationUrl}
          onChange={(e) => setFormData(prev => ({ ...prev, citationUrl: e.target.value }))}
          className="w-full px-3 py-1.5 text-sm border border-charcoal-300 rounded"
          placeholder="https://..."
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={isSaving || !formData.productName.trim()}
          className="flex items-center gap-1 px-3 py-1.5 bg-ifp-purple text-white text-sm rounded hover:bg-ifp-purple-dark disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {isSaving ? 'Adding...' : 'Add Tool'}
        </button>
        <button
          onClick={onCancel}
          className="flex items-center gap-1 px-3 py-1.5 bg-charcoal-200 text-charcoal text-sm rounded hover:bg-charcoal-300"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
      </div>
    </div>
  );
}

// ========================================
// BADGE COMPONENT
// ========================================

function ProductTypeBadge({ type }: { type: ProductType }) {
  const config = {
    staff_chatbot: { label: 'Chatbot', bg: 'bg-ifp-purple-light', text: 'text-ifp-purple' },
    coding_assistant: { label: 'Coding', bg: 'bg-ifp-orange-light', text: 'text-ifp-orange' },
    document_automation: { label: 'Doc Auto', bg: 'bg-green-100', text: 'text-green-700' },
    none_identified: { label: 'None', bg: 'bg-charcoal-100', text: 'text-charcoal-500' },
  };

  const { label, bg, text } = config[type] || config.none_identified;

  return (
    <span className={`px-2 py-0.5 text-xs ${bg} ${text} rounded-full`}>
      {label}
    </span>
  );
}

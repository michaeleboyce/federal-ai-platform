'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  logoutAction,
  updateProfileAction,
  deleteProfileAction,
  createToolAction,
  updateToolAction,
  deleteToolAction,
} from './actions';
import type { AgencyProfileWithTools, ToolStats } from '@/lib/agency-tools-db';
import type { AgencyAiTool, ProductType } from '@/lib/db/schema';
import { ChevronDown, ChevronRight, Plus, Trash2, Save, X, ExternalLink } from 'lucide-react';

interface AdminPanelProps {
  initialProfiles: AgencyProfileWithTools[];
  initialStats: ToolStats;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .trim();
}

export default function AdminPanel({ initialProfiles, initialStats }: AdminPanelProps) {
  const [profiles, setProfiles] = useState(initialProfiles);
  const [stats] = useState(initialStats);
  const [expandedProfiles, setExpandedProfiles] = useState<Set<number>>(new Set());
  const [editingTool, setEditingTool] = useState<number | null>(null);
  const [editingProfile, setEditingProfile] = useState<number | null>(null);
  const [addingToolTo, setAddingToolTo] = useState<number | null>(null);
  const router = useRouter();

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
          <button
            onClick={handleLogout}
            className="bg-charcoal-600 hover:bg-charcoal-500 px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            Logout
          </button>
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

        {/* Agency List */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b border-charcoal-200">
            <h2 className="font-semibold text-charcoal">Agencies & Tools</h2>
          </div>

          <div className="divide-y divide-charcoal-100">
            {profiles.map(profile => (
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

/**
 * Database query functions for Agency AI Profiles and Tools
 */

import { db } from './db/client';
import {
  agencyAiProfiles,
  agencyAiTools,
  federalOrganizations,
  type AgencyAiProfile,
  type AgencyAiTool,
  type ProductType,
} from './db/schema';
import { eq, sql, desc, asc } from 'drizzle-orm';

// ========================================
// TYPES
// ========================================

export interface AgencyProfileWithTools extends AgencyAiProfile {
  tools: AgencyAiTool[];
}

export interface ToolStats {
  total: number;
  staffChatbot: number;
  codingAssistant: number;
  documentAutomation: number;
  noneIdentified: number;
  agenciesWithTools: number;
  agenciesWithoutTools: number;
}

export interface DepartmentAggregation {
  departmentLevelName: string;
  agencyCount: number;
  toolCount: number;
  withChatbot: number;
  withCoding: number;
  withDocAutomation: number;
}

// ========================================
// BASIC QUERIES
// ========================================

/**
 * Get all agency profiles
 */
export async function getAgencyProfiles(): Promise<AgencyAiProfile[]> {
  return db
    .select()
    .from(agencyAiProfiles)
    .orderBy(asc(agencyAiProfiles.agencyName));
}

/**
 * Get all AI tools
 */
export async function getAllTools(): Promise<AgencyAiTool[]> {
  return db
    .select()
    .from(agencyAiTools)
    .orderBy(asc(agencyAiTools.productName));
}

/**
 * Get a single profile by slug
 */
export async function getProfileBySlug(slug: string): Promise<AgencyProfileWithTools | null> {
  const profiles = await db
    .select()
    .from(agencyAiProfiles)
    .where(eq(agencyAiProfiles.slug, slug))
    .limit(1);

  if (profiles.length === 0) return null;

  const profile = profiles[0];
  const tools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.agencyProfileId, profile.id))
    .orderBy(asc(agencyAiTools.productName));

  return { ...profile, tools };
}

/**
 * Get a single profile by ID
 */
export async function getProfileById(id: number): Promise<AgencyProfileWithTools | null> {
  const profiles = await db
    .select()
    .from(agencyAiProfiles)
    .where(eq(agencyAiProfiles.id, id))
    .limit(1);

  if (profiles.length === 0) return null;

  const profile = profiles[0];
  const tools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.agencyProfileId, profile.id))
    .orderBy(asc(agencyAiTools.productName));

  return { ...profile, tools };
}

/**
 * Get a single profile by organization ID (links to federal_organizations)
 */
export async function getProfileByOrganizationId(organizationId: number): Promise<AgencyProfileWithTools | null> {
  const profiles = await db
    .select()
    .from(agencyAiProfiles)
    .where(eq(agencyAiProfiles.organizationId, organizationId))
    .limit(1);

  if (profiles.length === 0) return null;

  const profile = profiles[0];
  const tools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.agencyProfileId, profile.id))
    .orderBy(asc(agencyAiTools.productName));

  return { ...profile, tools };
}

// ========================================
// PROFILES WITH TOOLS
// ========================================

/**
 * Get all profiles with their tools
 */
export async function getProfilesWithTools(): Promise<AgencyProfileWithTools[]> {
  const profiles = await db
    .select()
    .from(agencyAiProfiles)
    .orderBy(asc(agencyAiProfiles.agencyName));

  const tools = await db
    .select()
    .from(agencyAiTools)
    .orderBy(asc(agencyAiTools.productName));

  // Group tools by profile ID
  const toolsByProfile = new Map<number, AgencyAiTool[]>();
  for (const tool of tools) {
    const existing = toolsByProfile.get(tool.agencyProfileId) || [];
    existing.push(tool);
    toolsByProfile.set(tool.agencyProfileId, existing);
  }

  // Combine profiles with their tools
  return profiles.map(profile => ({
    ...profile,
    tools: toolsByProfile.get(profile.id) || [],
  }));
}

/**
 * Get profiles with tools filtered by product type
 */
export async function getProfilesWithToolsByType(
  productType: ProductType
): Promise<AgencyProfileWithTools[]> {
  const profiles = await getProfilesWithTools();

  return profiles.map(profile => ({
    ...profile,
    tools: profile.tools.filter(t => t.productType === productType),
  })).filter(profile =>
    // Keep agencies with matching tools or those with no tools (none_identified)
    profile.tools.length > 0 || (productType === 'none_identified' && profile.toolCount === 0)
  );
}

// ========================================
// STATISTICS
// ========================================

/**
 * Get overall tool statistics
 */
export async function getToolStats(): Promise<ToolStats> {
  const statsResult = await db
    .select({
      total: sql<number>`count(*)::int`.as('total'),
      staffChatbot: sql<number>`sum(case when ${agencyAiTools.productType} = 'staff_chatbot' then 1 else 0 end)::int`.as('staff_chatbot'),
      codingAssistant: sql<number>`sum(case when ${agencyAiTools.productType} = 'coding_assistant' then 1 else 0 end)::int`.as('coding_assistant'),
      documentAutomation: sql<number>`sum(case when ${agencyAiTools.productType} = 'document_automation' then 1 else 0 end)::int`.as('document_automation'),
      noneIdentified: sql<number>`sum(case when ${agencyAiTools.productType} = 'none_identified' then 1 else 0 end)::int`.as('none_identified'),
    })
    .from(agencyAiTools);

  const agencyStats = await db
    .select({
      agenciesWithTools: sql<number>`sum(case when ${agencyAiProfiles.toolCount} > 0 then 1 else 0 end)::int`.as('with_tools'),
      agenciesWithoutTools: sql<number>`sum(case when ${agencyAiProfiles.toolCount} = 0 then 1 else 0 end)::int`.as('without_tools'),
    })
    .from(agencyAiProfiles);

  return {
    total: statsResult[0]?.total || 0,
    staffChatbot: statsResult[0]?.staffChatbot || 0,
    codingAssistant: statsResult[0]?.codingAssistant || 0,
    documentAutomation: statsResult[0]?.documentAutomation || 0,
    noneIdentified: statsResult[0]?.noneIdentified || 0,
    agenciesWithTools: agencyStats[0]?.agenciesWithTools || 0,
    agenciesWithoutTools: agencyStats[0]?.agenciesWithoutTools || 0,
  };
}

/**
 * Get aggregated stats by department
 */
export async function getDepartmentStats(): Promise<DepartmentAggregation[]> {
  const result = await db
    .select({
      departmentLevelName: agencyAiProfiles.departmentLevelName,
      agencyCount: sql<number>`count(distinct ${agencyAiProfiles.id})::int`,
      toolCount: sql<number>`sum(${agencyAiProfiles.toolCount})::int`,
      withChatbot: sql<number>`sum(case when ${agencyAiProfiles.hasStaffChatbot} then 1 else 0 end)::int`,
      withCoding: sql<number>`sum(case when ${agencyAiProfiles.hasCodingAssistant} then 1 else 0 end)::int`,
      withDocAutomation: sql<number>`sum(case when ${agencyAiProfiles.hasDocumentAutomation} then 1 else 0 end)::int`,
    })
    .from(agencyAiProfiles)
    .groupBy(agencyAiProfiles.departmentLevelName)
    .orderBy(desc(sql`sum(${agencyAiProfiles.toolCount})`));

  return result.map(r => ({
    departmentLevelName: r.departmentLevelName || 'Unknown',
    agencyCount: r.agencyCount || 0,
    toolCount: r.toolCount || 0,
    withChatbot: r.withChatbot || 0,
    withCoding: r.withCoding || 0,
    withDocAutomation: r.withDocAutomation || 0,
  }));
}

// ========================================
// HIERARCHY HELPERS
// ========================================

/**
 * Get profiles grouped by parent abbreviation for hierarchy display
 */
export async function getProfilesByParent(): Promise<Map<string | null, AgencyProfileWithTools[]>> {
  const profiles = await getProfilesWithTools();

  const byParent = new Map<string | null, AgencyProfileWithTools[]>();

  for (const profile of profiles) {
    const parent = profile.parentAbbreviation;
    const existing = byParent.get(parent) || [];
    existing.push(profile);
    byParent.set(parent, existing);
  }

  return byParent;
}

/**
 * Get top-level departments (those without a parent)
 */
export async function getTopLevelProfiles(): Promise<AgencyProfileWithTools[]> {
  const profiles = await getProfilesWithTools();
  return profiles.filter(p => !p.parentAbbreviation);
}

/**
 * Get children of a specific parent
 */
export async function getChildProfiles(parentAbbreviation: string): Promise<AgencyProfileWithTools[]> {
  const profiles = await getProfilesWithTools();
  return profiles.filter(p => p.parentAbbreviation === parentAbbreviation);
}

// ========================================
// ADMIN CRUD OPERATIONS
// ========================================

/**
 * Create a new agency profile
 */
export async function createProfile(data: {
  agencyName: string;
  abbreviation?: string;
  slug: string;
  departmentLevelName?: string;
  parentAbbreviation?: string;
  deploymentStatus?: 'all_staff' | 'pilot_or_limited' | 'no_public_internal_assistant';
}): Promise<AgencyAiProfile> {
  const result = await db
    .insert(agencyAiProfiles)
    .values({
      agencyName: data.agencyName,
      abbreviation: data.abbreviation || null,
      slug: data.slug,
      departmentLevelName: data.departmentLevelName || null,
      parentAbbreviation: data.parentAbbreviation || null,
      deploymentStatus: data.deploymentStatus || 'no_public_internal_assistant',
      hasStaffChatbot: false,
      hasCodingAssistant: false,
      hasDocumentAutomation: false,
      toolCount: 0,
    })
    .returning();

  return result[0];
}

/**
 * Update an agency profile
 */
export async function updateProfile(
  id: number,
  data: Partial<{
    agencyName: string;
    abbreviation: string | null;
    departmentLevelName: string | null;
    parentAbbreviation: string | null;
    deploymentStatus: 'all_staff' | 'pilot_or_limited' | 'no_public_internal_assistant';
  }>
): Promise<AgencyAiProfile> {
  const result = await db
    .update(agencyAiProfiles)
    .set({
      ...data,
      updatedAt: new Date(),
    })
    .where(eq(agencyAiProfiles.id, id))
    .returning();

  return result[0];
}

/**
 * Delete an agency profile (and all its tools via cascade)
 */
export async function deleteProfile(id: number): Promise<void> {
  await db.delete(agencyAiProfiles).where(eq(agencyAiProfiles.id, id));
}

/**
 * Create a new tool
 */
export async function createTool(data: {
  agencyProfileId: number;
  productName: string;
  productType: ProductType;
  slug: string;
  availableToAllStaff?: string;
  isPilotOrLimited?: boolean;
  codingAssistantFlag?: string;
  internalOrSensitiveData?: string;
  citationChicago?: string;
  citationAccessedDate?: string;
  citationUrl?: string;
}): Promise<AgencyAiTool> {
  const result = await db
    .insert(agencyAiTools)
    .values({
      agencyProfileId: data.agencyProfileId,
      productName: data.productName,
      productType: data.productType,
      slug: data.slug,
      availableToAllStaff: data.availableToAllStaff || null,
      isPilotOrLimited: data.isPilotOrLimited || false,
      codingAssistantFlag: data.codingAssistantFlag || null,
      internalOrSensitiveData: data.internalOrSensitiveData || null,
      citationChicago: data.citationChicago || null,
      citationAccessedDate: data.citationAccessedDate || null,
      citationUrl: data.citationUrl || null,
    })
    .returning();

  // Update profile summary flags
  await updateProfileSummary(data.agencyProfileId);

  return result[0];
}

/**
 * Update a tool
 */
export async function updateTool(
  id: number,
  data: Partial<{
    productName: string;
    productType: ProductType;
    availableToAllStaff: string | null;
    isPilotOrLimited: boolean;
    codingAssistantFlag: string | null;
    internalOrSensitiveData: string | null;
    citationChicago: string | null;
    citationAccessedDate: string | null;
    citationUrl: string | null;
  }>
): Promise<AgencyAiTool> {
  // Get the tool first to find the profile ID
  const existingTools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.id, id))
    .limit(1);

  if (existingTools.length === 0) {
    throw new Error('Tool not found');
  }

  const result = await db
    .update(agencyAiTools)
    .set({
      ...data,
      updatedAt: new Date(),
    })
    .where(eq(agencyAiTools.id, id))
    .returning();

  // Update profile summary flags
  await updateProfileSummary(existingTools[0].agencyProfileId);

  return result[0];
}

/**
 * Delete a tool
 */
export async function deleteTool(id: number): Promise<void> {
  // Get the tool first to find the profile ID
  const existingTools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.id, id))
    .limit(1);

  if (existingTools.length === 0) {
    return;
  }

  const profileId = existingTools[0].agencyProfileId;

  await db.delete(agencyAiTools).where(eq(agencyAiTools.id, id));

  // Update profile summary flags
  await updateProfileSummary(profileId);
}

/**
 * Update profile summary flags based on its tools
 */
async function updateProfileSummary(profileId: number): Promise<void> {
  const tools = await db
    .select()
    .from(agencyAiTools)
    .where(eq(agencyAiTools.agencyProfileId, profileId));

  const hasStaffChatbot = tools.some(t => t.productType === 'staff_chatbot');
  const hasCodingAssistant = tools.some(t => t.productType === 'coding_assistant');
  const hasDocumentAutomation = tools.some(t => t.productType === 'document_automation');
  const toolCount = tools.length;

  await db
    .update(agencyAiProfiles)
    .set({
      hasStaffChatbot,
      hasCodingAssistant,
      hasDocumentAutomation,
      toolCount,
      updatedAt: new Date(),
    })
    .where(eq(agencyAiProfiles.id, profileId));
}

// ========================================
// FEDERAL ORGANIZATIONS WITH PROFILE STATUS
// ========================================

export interface FederalOrgWithProfileStatus {
  id: number;
  name: string;
  shortName: string | null;
  abbreviation: string | null;
  slug: string;
  parentId: number | null;
  level: 'department' | 'independent' | 'sub_agency' | 'office' | 'component';
  depth: number;
  isCfoActAgency: boolean;
  isCabinetDepartment: boolean;
  isActive: boolean;
  // Profile info
  hasProfile: boolean;
  profileId: number | null;
  toolCount: number;
  hasStaffChatbot: boolean;
  hasCodingAssistant: boolean;
  hasDocumentAutomation: boolean;
  // Tools (if profile exists)
  tools: AgencyAiTool[];
}

/**
 * Get all federal organizations with their profile status
 * Used in admin panel to show all agencies and whether they have AI use cases
 */
export async function getAllFederalOrgsWithProfileStatus(): Promise<FederalOrgWithProfileStatus[]> {
  // Get all active federal organizations
  const orgs = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.isActive, true))
    .orderBy(asc(federalOrganizations.depth), asc(federalOrganizations.name));

  // Get all profiles with their tools
  const profiles = await getProfilesWithTools();

  // Create maps for lookup - by organizationId, slug, and abbreviation
  const profileByOrgId = new Map<number, AgencyProfileWithTools>();
  const profileBySlug = new Map<string, AgencyProfileWithTools>();
  const profileByAbbreviation = new Map<string, AgencyProfileWithTools>();

  for (const profile of profiles) {
    if (profile.organizationId) {
      profileByOrgId.set(profile.organizationId, profile);
    }
    if (profile.slug) {
      profileBySlug.set(profile.slug.toLowerCase(), profile);
    }
    if (profile.abbreviation) {
      profileByAbbreviation.set(profile.abbreviation.toLowerCase(), profile);
    }
  }

  // Combine orgs with profile status - try matching by orgId, then slug, then abbreviation
  return orgs.map(org => {
    let profile = profileByOrgId.get(org.id);

    // If no match by organizationId, try matching by slug
    if (!profile && org.slug) {
      profile = profileBySlug.get(org.slug.toLowerCase());
    }

    // If still no match, try matching by abbreviation
    if (!profile && org.abbreviation) {
      profile = profileByAbbreviation.get(org.abbreviation.toLowerCase());
    }

    return {
      id: org.id,
      name: org.name,
      shortName: org.shortName,
      abbreviation: org.abbreviation,
      slug: org.slug,
      parentId: org.parentId,
      level: org.level,
      depth: org.depth,
      isCfoActAgency: org.isCfoActAgency,
      isCabinetDepartment: org.isCabinetDepartment,
      isActive: org.isActive,
      hasProfile: !!profile,
      profileId: profile?.id ?? null,
      toolCount: profile?.toolCount ?? 0,
      hasStaffChatbot: profile?.hasStaffChatbot ?? false,
      hasCodingAssistant: profile?.hasCodingAssistant ?? false,
      hasDocumentAutomation: profile?.hasDocumentAutomation ?? false,
      tools: profile?.tools ?? [],
    };
  });
}

/**
 * Get a single federal organization by ID
 */
export async function getFederalOrgById(id: number) {
  const orgs = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.id, id))
    .limit(1);

  return orgs[0] ?? null;
}

/**
 * Get parent organization for a given org
 */
export async function getParentOrg(parentId: number) {
  const orgs = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.id, parentId))
    .limit(1);

  return orgs[0] ?? null;
}

/**
 * Create a profile from a federal organization
 * Links the new profile to the federal org via organizationId
 */
export async function createProfileFromOrg(orgId: number): Promise<AgencyAiProfile> {
  // Get the org
  const org = await getFederalOrgById(orgId);
  if (!org) {
    throw new Error(`Federal organization with ID ${orgId} not found`);
  }

  // Get parent org for department level info
  let departmentLevelName: string | null = null;
  let parentAbbreviation: string | null = null;

  if (org.parentId) {
    const parentOrg = await getParentOrg(org.parentId);
    if (parentOrg) {
      // If parent is a department, use its name
      if (parentOrg.level === 'department' || parentOrg.level === 'independent') {
        departmentLevelName = parentOrg.name;
        parentAbbreviation = parentOrg.abbreviation;
      } else {
        // Climb up the tree to find the department
        let currentParent = parentOrg;
        while (currentParent.parentId) {
          const grandParent = await getParentOrg(currentParent.parentId);
          if (!grandParent) break;
          if (grandParent.level === 'department' || grandParent.level === 'independent') {
            departmentLevelName = grandParent.name;
            parentAbbreviation = grandParent.abbreviation;
            break;
          }
          currentParent = grandParent;
        }
      }
    }
  } else if (org.level === 'department' || org.level === 'independent') {
    // This org IS a department/independent agency
    departmentLevelName = org.name;
  }

  // Create the profile
  const result = await db
    .insert(agencyAiProfiles)
    .values({
      agencyName: org.name,
      abbreviation: org.abbreviation || null,
      slug: org.slug,
      organizationId: org.id,
      departmentLevelName,
      parentAbbreviation,
      deploymentStatus: 'no_public_internal_assistant',
      hasStaffChatbot: false,
      hasCodingAssistant: false,
      hasDocumentAutomation: false,
      toolCount: 0,
    })
    .returning();

  return result[0];
}

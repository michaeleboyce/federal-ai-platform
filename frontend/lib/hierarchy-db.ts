import { db } from './db/client';
import { federalOrganizations } from './db/schema';
import type { FederalOrganization, FederalOrganizationWithChildren, HierarchyBreadcrumb, OrgLevel } from './db/schema';
import { eq, isNull, asc, ilike, or, sql, and, inArray } from 'drizzle-orm';

// ========================================
// BASIC QUERIES
// ========================================

/**
 * Get all top-level organizations (departments and independent agencies)
 */
export async function getTopLevelOrganizations(): Promise<FederalOrganization[]> {
  return db
    .select()
    .from(federalOrganizations)
    .where(isNull(federalOrganizations.parentId))
    .orderBy(asc(federalOrganizations.displayOrder), asc(federalOrganizations.name));
}

/**
 * Get a single organization by its ID
 */
export async function getOrganizationById(id: number): Promise<FederalOrganization | null> {
  const results = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.id, id))
    .limit(1);

  return results[0] || null;
}

/**
 * Get a single organization by its URL slug
 */
export async function getOrganizationBySlug(slug: string): Promise<FederalOrganization | null> {
  const results = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.slug, slug))
    .limit(1);

  return results[0] || null;
}

/**
 * Get organization by abbreviation
 */
export async function getOrganizationByAbbreviation(abbreviation: string): Promise<FederalOrganization | null> {
  const results = await db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.abbreviation, abbreviation.toUpperCase()))
    .limit(1);

  return results[0] || null;
}

/**
 * Get all organizations of a specific level
 */
export async function getOrganizationsByLevel(level: OrgLevel): Promise<FederalOrganization[]> {
  return db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.level, level))
    .orderBy(asc(federalOrganizations.name));
}

/**
 * Get all CFO Act agencies
 */
export async function getCfoActAgencies(): Promise<FederalOrganization[]> {
  return db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.isCfoActAgency, true))
    .orderBy(asc(federalOrganizations.displayOrder), asc(federalOrganizations.name));
}

/**
 * Get all cabinet departments
 */
export async function getCabinetDepartments(): Promise<FederalOrganization[]> {
  return db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.isCabinetDepartment, true))
    .orderBy(asc(federalOrganizations.displayOrder), asc(federalOrganizations.name));
}

// ========================================
// HIERARCHY QUERIES
// ========================================

/**
 * Get direct children of an organization
 */
export async function getChildren(parentId: number): Promise<FederalOrganization[]> {
  return db
    .select()
    .from(federalOrganizations)
    .where(eq(federalOrganizations.parentId, parentId))
    .orderBy(asc(federalOrganizations.displayOrder), asc(federalOrganizations.name));
}

/**
 * Get organization with its direct children
 */
export async function getOrganizationWithChildren(id: number): Promise<FederalOrganizationWithChildren | null> {
  const org = await getOrganizationById(id);
  if (!org) return null;

  const children = await getChildren(id);
  const childrenWithChildren: FederalOrganizationWithChildren[] = children.map(child => ({
    ...child,
    children: [],
  }));

  return {
    ...org,
    children: childrenWithChildren,
  };
}

/**
 * Get the full hierarchy tree starting from a given organization
 * Recursively fetches all descendants
 */
export async function getOrganizationHierarchy(id: number): Promise<FederalOrganizationWithChildren | null> {
  const org = await getOrganizationById(id);
  if (!org) return null;

  const children = await getChildren(id);
  const childrenWithHierarchy = await Promise.all(
    children.map(async (child) => {
      const childHierarchy = await getOrganizationHierarchy(child.id);
      return childHierarchy || { ...child, children: [] };
    })
  );

  return {
    ...org,
    children: childrenWithHierarchy,
  };
}

/**
 * Get the full hierarchy tree for all top-level organizations
 */
export async function getFullHierarchy(): Promise<FederalOrganizationWithChildren[]> {
  const topLevel = await getTopLevelOrganizations();

  const fullHierarchy = await Promise.all(
    topLevel.map(async (org) => {
      const hierarchy = await getOrganizationHierarchy(org.id);
      return hierarchy || { ...org, children: [] };
    })
  );

  return fullHierarchy;
}

/**
 * Get all descendants of an organization using the materialized path
 * Much faster than recursive queries for deep hierarchies
 */
export async function getDescendants(id: number): Promise<FederalOrganization[]> {
  const org = await getOrganizationById(id);
  if (!org || !org.hierarchyPath) return [];

  // Use LIKE query on hierarchy_path to find all descendants
  // e.g., if org has path '/1/', find all with path LIKE '/1/%'
  return db
    .select()
    .from(federalOrganizations)
    .where(
      and(
        sql`${federalOrganizations.hierarchyPath} LIKE ${org.hierarchyPath + '%'}`,
        sql`${federalOrganizations.id} != ${id}`
      )
    )
    .orderBy(asc(federalOrganizations.depth), asc(federalOrganizations.name));
}

/**
 * Get ancestors (parent chain) of an organization
 */
export async function getAncestors(id: number): Promise<FederalOrganization[]> {
  const org = await getOrganizationById(id);
  if (!org || !org.hierarchyPath) return [];

  // Parse the hierarchy path to get ancestor IDs
  // e.g., '/1/13/18/' -> [1, 13]
  const pathParts = org.hierarchyPath.split('/').filter(Boolean);
  const ancestorIds = pathParts.slice(0, -1).map(Number);

  if (ancestorIds.length === 0) return [];

  return db
    .select()
    .from(federalOrganizations)
    .where(inArray(federalOrganizations.id, ancestorIds))
    .orderBy(asc(federalOrganizations.depth));
}

/**
 * Get breadcrumb path from root to organization
 */
export async function getOrganizationBreadcrumbs(id: number): Promise<HierarchyBreadcrumb[]> {
  const ancestors = await getAncestors(id);
  const org = await getOrganizationById(id);

  if (!org) return [];

  const allOrgs = [...ancestors, org];

  return allOrgs.map((o) => ({
    id: o.id,
    name: o.name,
    abbreviation: o.abbreviation,
    slug: o.slug,
    level: o.level as OrgLevel,
  }));
}

/**
 * Get the parent organization
 */
export async function getParent(id: number): Promise<FederalOrganization | null> {
  const org = await getOrganizationById(id);
  if (!org || !org.parentId) return null;

  return getOrganizationById(org.parentId);
}

// ========================================
// SEARCH QUERIES
// ========================================

/**
 * Search organizations by name or abbreviation
 */
export async function searchOrganizations(query: string): Promise<FederalOrganization[]> {
  if (!query || query.trim().length === 0) {
    return getTopLevelOrganizations();
  }

  const searchTerm = `%${query.trim()}%`;

  return db
    .select()
    .from(federalOrganizations)
    .where(
      or(
        ilike(federalOrganizations.name, searchTerm),
        ilike(federalOrganizations.abbreviation, searchTerm),
        ilike(federalOrganizations.shortName, searchTerm)
      )
    )
    .orderBy(asc(federalOrganizations.depth), asc(federalOrganizations.name))
    .limit(50);
}

// ========================================
// STATISTICS
// ========================================

export interface HierarchyStats {
  totalOrganizations: number;
  cfoActAgencies: number;
  cabinetDepartments: number;
  independentAgencies: number;
  subAgencies: number;
  offices: number;
  maxDepth: number;
}

/**
 * Get statistics about the federal hierarchy
 */
export async function getHierarchyStats(): Promise<HierarchyStats> {
  const result = await db.execute(sql`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN is_cfo_act_agency THEN 1 ELSE 0 END) as cfo_act,
      SUM(CASE WHEN is_cabinet_department THEN 1 ELSE 0 END) as cabinet,
      SUM(CASE WHEN level = 'independent' THEN 1 ELSE 0 END) as independent,
      SUM(CASE WHEN level = 'sub_agency' THEN 1 ELSE 0 END) as sub_agency,
      SUM(CASE WHEN level = 'office' THEN 1 ELSE 0 END) as office,
      MAX(depth) as max_depth
    FROM federal_organizations
  `);

  const row = result.rows[0] as Record<string, unknown>;

  return {
    totalOrganizations: Number(row.total) || 0,
    cfoActAgencies: Number(row.cfo_act) || 0,
    cabinetDepartments: Number(row.cabinet) || 0,
    independentAgencies: Number(row.independent) || 0,
    subAgencies: Number(row.sub_agency) || 0,
    offices: Number(row.office) || 0,
    maxDepth: Number(row.max_depth) || 0,
  };
}

// ========================================
// MATCHING HELPERS
// ========================================

/**
 * Find organization that best matches an agency name from use cases or agency AI usage
 * Uses fuzzy matching on name and abbreviation
 */
export async function findMatchingOrganization(
  agencyName: string,
  abbreviation?: string | null
): Promise<FederalOrganization | null> {
  // First try exact abbreviation match
  if (abbreviation) {
    const abbrevMatch = await getOrganizationByAbbreviation(abbreviation);
    if (abbrevMatch) return abbrevMatch;
  }

  // Try to extract abbreviation from name (e.g., "Department of State (DOS)")
  const abbrevInName = agencyName.match(/\(([A-Z]{2,10})\)/);
  if (abbrevInName) {
    const extracted = abbrevInName[1];
    const abbrevMatch = await getOrganizationByAbbreviation(extracted);
    if (abbrevMatch) return abbrevMatch;
  }

  // Try name matching
  const nameResults = await searchOrganizations(agencyName);
  if (nameResults.length > 0) {
    // Prefer exact match
    const exactMatch = nameResults.find(
      (org) => org.name.toLowerCase() === agencyName.toLowerCase()
    );
    if (exactMatch) return exactMatch;

    // Otherwise return first result (best match)
    return nameResults[0];
  }

  return null;
}

/**
 * Get all organizations as a flat list with depth information
 * Useful for building hierarchical dropdowns
 */
export async function getAllOrganizationsFlat(): Promise<(FederalOrganization & { parentName: string | null })[]> {
  const result = await db.execute(sql`
    SELECT
      fo.*,
      parent.name as parent_name
    FROM federal_organizations fo
    LEFT JOIN federal_organizations parent ON fo.parent_id = parent.id
    ORDER BY fo.depth, fo.display_order, fo.name
  `);

  return result.rows.map((row: Record<string, unknown>) => ({
    id: row.id as number,
    name: row.name as string,
    shortName: row.short_name as string | null,
    abbreviation: row.abbreviation as string | null,
    slug: row.slug as string,
    parentId: row.parent_id as number | null,
    level: row.level as OrgLevel,
    hierarchyPath: row.hierarchy_path as string | null,
    depth: row.depth as number,
    samOrgId: row.sam_org_id as string | null,
    cgacCode: row.cgac_code as string | null,
    agencyCode: row.agency_code as string | null,
    isCfoActAgency: row.is_cfo_act_agency as boolean,
    isCabinetDepartment: row.is_cabinet_department as boolean,
    isActive: row.is_active as boolean,
    displayOrder: row.display_order as number | null,
    description: row.description as string | null,
    website: row.website as string | null,
    createdAt: new Date(row.created_at as string),
    updatedAt: new Date(row.updated_at as string),
    parentName: row.parent_name as string | null,
  }));
}

// ========================================
// HIERARCHY WITH AGENCY USAGE
// ========================================

import { agencyAiUsage } from './db/schema';

export interface AgencyUsageData {
  id: number;
  agencyName: string;
  slug: string;
  hasStaffLlm: string | null;
  hasCodingAssistant: string | null;
  solutionType: string | null;
  llmName: string | null;
}

export interface AggregatedStats {
  agencyCount: number;
  withLlm: number;
  withCoding: number;
}

export interface FederalOrganizationWithAgencies extends FederalOrganization {
  children: FederalOrganizationWithAgencies[];
  agencies: AgencyUsageData[];
  aggregatedStats: AggregatedStats;
}

/**
 * Get all agencies grouped by organization ID
 */
async function getAgenciesByOrgId(): Promise<Map<number, AgencyUsageData[]>> {
  const agencies = await db
    .select({
      id: agencyAiUsage.id,
      agencyName: agencyAiUsage.agencyName,
      slug: agencyAiUsage.slug,
      hasStaffLlm: agencyAiUsage.hasStaffLlm,
      hasCodingAssistant: agencyAiUsage.hasCodingAssistant,
      solutionType: agencyAiUsage.solutionType,
      llmName: agencyAiUsage.llmName,
      organizationId: agencyAiUsage.organizationId,
    })
    .from(agencyAiUsage)
    .orderBy(asc(agencyAiUsage.agencyName));

  const byOrgId = new Map<number, AgencyUsageData[]>();

  for (const agency of agencies) {
    if (agency.organizationId) {
      if (!byOrgId.has(agency.organizationId)) {
        byOrgId.set(agency.organizationId, []);
      }
      byOrgId.get(agency.organizationId)!.push({
        id: agency.id,
        agencyName: agency.agencyName,
        slug: agency.slug,
        hasStaffLlm: agency.hasStaffLlm,
        hasCodingAssistant: agency.hasCodingAssistant,
        solutionType: agency.solutionType,
        llmName: agency.llmName,
      });
    }
  }

  return byOrgId;
}

/**
 * Calculate stats for a single set of agencies
 */
function calculateStats(agencies: AgencyUsageData[]): AggregatedStats {
  return {
    agencyCount: agencies.length,
    withLlm: agencies.filter(a => a.hasStaffLlm?.includes('Yes')).length,
    withCoding: agencies.filter(a =>
      a.hasCodingAssistant?.includes('Yes') || a.hasCodingAssistant?.includes('Allowed')
    ).length,
  };
}

/**
 * Build hierarchy tree with agencies attached and aggregate stats bubbled up
 */
function buildHierarchyWithAgencies(
  orgs: FederalOrganization[],
  agenciesByOrgId: Map<number, AgencyUsageData[]>,
  parentId: number | null = null
): FederalOrganizationWithAgencies[] {
  const children = orgs.filter(org => org.parentId === parentId);

  return children.map(org => {
    // Get agencies directly attached to this org
    const directAgencies = agenciesByOrgId.get(org.id) || [];

    // Recursively build children
    const childOrgs = buildHierarchyWithAgencies(orgs, agenciesByOrgId, org.id);

    // Calculate direct stats
    const directStats = calculateStats(directAgencies);

    // Aggregate stats from children
    const aggregatedStats: AggregatedStats = {
      agencyCount: directStats.agencyCount,
      withLlm: directStats.withLlm,
      withCoding: directStats.withCoding,
    };

    for (const child of childOrgs) {
      aggregatedStats.agencyCount += child.aggregatedStats.agencyCount;
      aggregatedStats.withLlm += child.aggregatedStats.withLlm;
      aggregatedStats.withCoding += child.aggregatedStats.withCoding;
    }

    return {
      ...org,
      children: childOrgs,
      agencies: directAgencies,
      aggregatedStats,
    };
  });
}

/**
 * Get the full federal hierarchy with agencies attached and stats aggregated
 * Stats bubble up from children to parents
 */
export async function getHierarchyWithAgencyUsage(): Promise<FederalOrganizationWithAgencies[]> {
  // Fetch all organizations
  const allOrgs = await db
    .select()
    .from(federalOrganizations)
    .orderBy(asc(federalOrganizations.displayOrder), asc(federalOrganizations.name));

  // Fetch all agencies grouped by org ID
  const agenciesByOrgId = await getAgenciesByOrgId();

  // Build the tree starting from top-level (no parent)
  return buildHierarchyWithAgencies(allOrgs, agenciesByOrgId, null);
}

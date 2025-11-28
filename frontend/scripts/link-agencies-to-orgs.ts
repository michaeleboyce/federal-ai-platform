/**
 * Link agency_ai_usage records to federal_organizations hierarchy
 *
 * This script:
 * 1. Fetches all agency_ai_usage records
 * 2. Matches each to a federal_organizations entry
 * 3. Creates missing organizations if needed
 * 4. Updates the organizationId FK
 */

import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

// Utility to create slug from name
function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

interface AgencyRecord {
  id: number;
  agency_name: string;
  organization_id: number | null;
}

interface OrgRecord {
  id: number;
  name: string;
  abbreviation: string | null;
  parent_id: number | null;
  level: string;
}

/**
 * Manual mappings for agencies that need explicit linking
 * Format: exact agency_name -> organization abbreviation or special handling
 */
const EXACT_MAPPINGS: Record<string, string> = {
  // Short-form entries that need explicit mapping
  'EPA': 'EPA',
  'NASA': 'NASA',
  'SSA': 'SSA',
  'USPTO': 'USPTO',
  'FDIC': 'FDIC',

  // Special cases with odd formatting
  'DOE (labs)': 'DOE',
  'NIST NCCoE (Dept. of Commerce)': 'NIST',
  'Department of the Treasury / Internal Revenue Service (IRS)': 'TREAS',

  // Entries with multiple abbreviations in parens
  'Centers for Disease Control and Prevention (CDC, HHS)': 'CDC',
  'Food and Drug Administration (FDA, HHS)': 'FDA',
  'National Institutes of Health (NIH, HHS)': 'NIH',
  'U.S. Patent and Trademark Office (USPTO, Dept. of Commerce)': 'USPTO',
  'Department of the Air Force (Air Force + Space Force)': 'USAF',
};

/**
 * New organizations to add to the hierarchy
 * These are independent agencies not in the original CFO Act seed
 */
const NEW_ORGANIZATIONS = [
  { name: 'Executive Office of the President', abbreviation: 'EOP', level: 'independent', description: 'Supports the President in executing duties' },
  { name: 'Federal Communications Commission', abbreviation: 'FCC', level: 'independent', description: 'Regulates communications by radio, television, wire, satellite, and cable' },
  { name: 'Federal Deposit Insurance Corporation', abbreviation: 'FDIC', level: 'independent', description: 'Provides deposit insurance and examines financial institutions' },
  { name: 'Federal Election Commission', abbreviation: 'FEC', level: 'independent', description: 'Enforces federal campaign finance laws' },
  { name: 'Federal Trade Commission', abbreviation: 'FTC', level: 'independent', description: 'Protects consumers and promotes competition' },
  { name: 'Merit Systems Protection Board', abbreviation: 'MSPB', level: 'independent', description: 'Protects federal merit systems' },
  { name: 'National Archives and Records Administration', abbreviation: 'NARA', level: 'independent', description: 'Preserves government and historical records' },
  { name: 'National Labor Relations Board', abbreviation: 'NLRB', level: 'independent', description: 'Enforces labor law regarding collective bargaining' },
  { name: 'Securities and Exchange Commission', abbreviation: 'SEC', level: 'independent', description: 'Regulates securities markets' },
  { name: 'U.S. Postal Service', abbreviation: 'USPS', level: 'independent', description: 'Provides postal services' },
];

/**
 * Extract abbreviation from agency name like "Department of Defense (DOD)"
 */
function extractAbbreviation(agencyName: string): string | null {
  const match = agencyName.match(/\(([A-Z]{2,10})\)/);
  return match ? match[1] : null;
}

/**
 * Normalize agency name for matching
 */
function normalizeName(name: string): string {
  return name
    .toLowerCase()
    .replace(/^(u\.?s\.?\s+|united states\s+|federal\s+)/i, '')
    .replace(/\s+/g, ' ')
    .trim();
}

async function main() {
  console.log('🔗 Linking Agency AI Usage records to Federal Organizations\n');
  console.log('='.repeat(60));

  // 1. First, create any missing organizations
  console.log('\n📦 Creating missing organizations...\n');

  for (const newOrg of NEW_ORGANIZATIONS) {
    const existing = await sql`
      SELECT id FROM federal_organizations WHERE abbreviation = ${newOrg.abbreviation}
    `;

    if (existing.length === 0) {
      const slug = slugify(newOrg.name);
      const result = await sql`
        INSERT INTO federal_organizations (
          name, abbreviation, slug, level, depth,
          is_cfo_act_agency, is_cabinet_department, is_active, description
        ) VALUES (
          ${newOrg.name},
          ${newOrg.abbreviation},
          ${slug},
          ${newOrg.level},
          0,
          false,
          false,
          true,
          ${newOrg.description}
        )
        RETURNING id
      `;
      // Update hierarchy path
      const newId = result[0].id;
      await sql`
        UPDATE federal_organizations
        SET hierarchy_path = ${'/' + newId + '/'}
        WHERE id = ${newId}
      `;
      console.log(`  ✓ Created: ${newOrg.abbreviation} - ${newOrg.name} (id: ${newId})`);
    } else {
      console.log(`  - Exists: ${newOrg.abbreviation} - ${newOrg.name}`);
    }
  }

  // 2. Fetch all agencies
  const agencies = await sql`
    SELECT id, agency_name, organization_id
    FROM agency_ai_usage
    ORDER BY agency_name
  ` as AgencyRecord[];

  console.log(`\n📊 Found ${agencies.length} agency records\n`);

  // 3. Fetch all federal organizations (fresh, including newly created)
  const organizations = await sql`
    SELECT id, name, abbreviation, parent_id, level
    FROM federal_organizations
    ORDER BY depth, name
  ` as OrgRecord[];

  console.log(`📊 Found ${organizations.length} federal organizations\n`);

  // Create lookup maps
  const orgByAbbreviation = new Map<string, OrgRecord>();
  const orgByName = new Map<string, OrgRecord>();

  organizations.forEach(org => {
    if (org.abbreviation) {
      orgByAbbreviation.set(org.abbreviation.toUpperCase(), org);
    }
    orgByName.set(normalizeName(org.name), org);
  });

  // 4. Process each agency
  const results = {
    matched: 0,
    alreadyLinked: 0,
    created: 0,
    unmatched: [] as string[]
  };

  console.log('Processing agencies...\n');

  for (const agency of agencies) {
    // Skip if already linked
    if (agency.organization_id) {
      results.alreadyLinked++;
      console.log(`  ✓ [LINKED] ${agency.agency_name} → org #${agency.organization_id}`);
      continue;
    }

    let matchedOrg: OrgRecord | undefined;

    // Strategy 1: Exact mapping (highest priority)
    const exactMapping = EXACT_MAPPINGS[agency.agency_name];
    if (exactMapping) {
      matchedOrg = orgByAbbreviation.get(exactMapping.toUpperCase());
    }

    // Strategy 2: Extract abbreviation from name like "(DOD)"
    if (!matchedOrg) {
      const abbrev = extractAbbreviation(agency.agency_name);
      if (abbrev) {
        matchedOrg = orgByAbbreviation.get(abbrev.toUpperCase());
      }
    }

    // Strategy 3: Exact normalized name match
    if (!matchedOrg) {
      matchedOrg = orgByName.get(normalizeName(agency.agency_name));
    }

    // Strategy 4: Careful partial match - only for "Department of X" patterns
    if (!matchedOrg) {
      const normalizedAgency = normalizeName(agency.agency_name);
      // Only match if the agency name starts with "department of"
      if (normalizedAgency.startsWith('department of')) {
        for (const [normalizedOrgName, org] of orgByName.entries()) {
          if (org.level === 'department' && normalizedAgency.includes(normalizedOrgName)) {
            matchedOrg = org;
            break;
          }
        }
      }
    }

    if (matchedOrg) {
      // Update the agency record
      await sql`
        UPDATE agency_ai_usage
        SET organization_id = ${matchedOrg.id}
        WHERE id = ${agency.id}
      `;
      results.matched++;
      console.log(`  ✓ [MATCHED] ${agency.agency_name} → ${matchedOrg.abbreviation || matchedOrg.name} (#${matchedOrg.id})`);
    } else {
      results.unmatched.push(agency.agency_name);
      console.log(`  ✗ [UNMATCHED] ${agency.agency_name}`);
    }
  }

  // 4. Print summary
  console.log('\n' + '='.repeat(60));
  console.log('\n📈 SUMMARY\n');
  console.log(`  Already linked: ${results.alreadyLinked}`);
  console.log(`  Matched: ${results.matched}`);
  console.log(`  Created: ${results.created}`);
  console.log(`  Unmatched: ${results.unmatched.length}`);

  if (results.unmatched.length > 0) {
    console.log('\n⚠️  UNMATCHED AGENCIES (need manual mapping or creation):');
    results.unmatched.forEach(name => {
      console.log(`    - ${name}`);
    });
  }

  // 5. Show final state
  const finalAgencies = await sql`
    SELECT
      a.agency_name,
      o.name as org_name,
      o.abbreviation as org_abbrev
    FROM agency_ai_usage a
    LEFT JOIN federal_organizations o ON a.organization_id = o.id
    ORDER BY a.agency_name
  `;

  console.log('\n\n📋 FINAL MAPPING STATE:\n');
  for (const row of finalAgencies) {
    const orgInfo = row.org_name ? `→ ${row.org_abbrev || row.org_name}` : '→ [NOT LINKED]';
    console.log(`  ${row.agency_name} ${orgInfo}`);
  }
}

main().catch(console.error);

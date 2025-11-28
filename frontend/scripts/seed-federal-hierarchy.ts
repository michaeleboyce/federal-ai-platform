import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '.env.local' });

const sql = neon(process.env.DATABASE_URL!);

// Utility to create slug from name
function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

// Types
type OrgLevel = 'department' | 'independent' | 'sub_agency' | 'office' | 'component';

interface Organization {
  name: string;
  shortName?: string;
  abbreviation: string;
  level: OrgLevel;
  isCfoActAgency: boolean;
  isCabinetDepartment: boolean;
  website?: string;
  description?: string;
  children?: Organization[];
}

// ========================================
// CFO ACT AGENCIES DATA
// ========================================

const CFO_ACT_AGENCIES: Organization[] = [
  // ----------------------------------------
  // 15 CABINET DEPARTMENTS
  // ----------------------------------------
  {
    name: 'Department of Agriculture',
    abbreviation: 'USDA',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.usda.gov',
    description: 'Develops and executes federal policy on farming, agriculture, forestry, and food',
    children: [
      { name: 'Farm Service Agency', abbreviation: 'FSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Forest Service', abbreviation: 'FS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Food and Nutrition Service', abbreviation: 'FNS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Natural Resources Conservation Service', abbreviation: 'NRCS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Agricultural Research Service', abbreviation: 'ARS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Commerce',
    abbreviation: 'DOC',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.commerce.gov',
    description: 'Promotes economic growth and job creation',
    children: [
      { name: 'Census Bureau', abbreviation: 'CENSUS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Oceanic and Atmospheric Administration', abbreviation: 'NOAA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Patent and Trademark Office', abbreviation: 'USPTO', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Institute of Standards and Technology', abbreviation: 'NIST', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'International Trade Administration', abbreviation: 'ITA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Defense',
    abbreviation: 'DOD',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.defense.gov',
    description: 'Provides military forces needed to deter war and protect the security of the United States',
    children: [
      { name: 'Department of the Army', abbreviation: 'ARMY', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Department of the Navy', abbreviation: 'NAVY', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Department of the Air Force', abbreviation: 'USAF', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Defense Intelligence Agency', abbreviation: 'DIA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Security Agency', abbreviation: 'NSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Defense Logistics Agency', abbreviation: 'DLA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Defense Information Systems Agency', abbreviation: 'DISA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Education',
    abbreviation: 'ED',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.ed.gov',
    description: 'Promotes student achievement and preparation for global competitiveness',
    children: [
      { name: 'Office of Federal Student Aid', abbreviation: 'FSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Office of Civil Rights', abbreviation: 'OCR', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Energy',
    abbreviation: 'DOE',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.energy.gov',
    description: 'Advances energy, environmental, and nuclear security',
    children: [
      { name: 'National Nuclear Security Administration', abbreviation: 'NNSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Office of Science', abbreviation: 'SC', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Energy Information Administration', abbreviation: 'EIA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Health and Human Services',
    abbreviation: 'HHS',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.hhs.gov',
    description: 'Protects the health of all Americans and provides essential human services',
    children: [
      { name: 'Centers for Disease Control and Prevention', abbreviation: 'CDC', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Food and Drug Administration', abbreviation: 'FDA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Institutes of Health', abbreviation: 'NIH', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Centers for Medicare and Medicaid Services', abbreviation: 'CMS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Administration for Children and Families', abbreviation: 'ACF', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Indian Health Service', abbreviation: 'IHS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Homeland Security',
    abbreviation: 'DHS',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.dhs.gov',
    description: 'Secures the nation from threats',
    children: [
      { name: 'Customs and Border Protection', abbreviation: 'CBP', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Immigration and Customs Enforcement', abbreviation: 'ICE', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Transportation Security Administration', abbreviation: 'TSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Federal Emergency Management Agency', abbreviation: 'FEMA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Cybersecurity and Infrastructure Security Agency', abbreviation: 'CISA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Citizenship and Immigration Services', abbreviation: 'USCIS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Secret Service', abbreviation: 'USSS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Coast Guard', abbreviation: 'USCG', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Housing and Urban Development',
    abbreviation: 'HUD',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.hud.gov',
    description: 'Creates strong, sustainable, inclusive communities and quality affordable homes',
    children: [
      { name: 'Federal Housing Administration', abbreviation: 'FHA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Office of Fair Housing and Equal Opportunity', abbreviation: 'FHEO', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of the Interior',
    abbreviation: 'DOI',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.doi.gov',
    description: 'Protects and manages the Nation\'s natural resources and cultural heritage',
    children: [
      { name: 'Bureau of Land Management', abbreviation: 'BLM', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Park Service', abbreviation: 'NPS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Fish and Wildlife Service', abbreviation: 'FWS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Indian Affairs', abbreviation: 'BIA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Geological Survey', abbreviation: 'USGS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Reclamation', abbreviation: 'USBR', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Justice',
    abbreviation: 'DOJ',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.justice.gov',
    description: 'Enforces the law and defends the interests of the United States',
    children: [
      { name: 'Federal Bureau of Investigation', abbreviation: 'FBI', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Drug Enforcement Administration', abbreviation: 'DEA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Alcohol, Tobacco, Firearms and Explosives', abbreviation: 'ATF', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Marshals Service', abbreviation: 'USMS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Prisons', abbreviation: 'BOP', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Executive Office for Immigration Review', abbreviation: 'EOIR', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Labor',
    abbreviation: 'DOL',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.dol.gov',
    description: 'Fosters and promotes the welfare of job seekers, wage earners, and retirees',
    children: [
      { name: 'Occupational Safety and Health Administration', abbreviation: 'OSHA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Labor Statistics', abbreviation: 'BLS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Employment and Training Administration', abbreviation: 'ETA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Mine Safety and Health Administration', abbreviation: 'MSHA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of State',
    abbreviation: 'DOS',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.state.gov',
    description: 'Leads America\'s foreign policy through diplomacy, advocacy, and assistance',
    children: [
      { name: 'Bureau of Consular Affairs', abbreviation: 'CA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of Diplomatic Security', abbreviation: 'DS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Transportation',
    abbreviation: 'DOT',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.transportation.gov',
    description: 'Ensures fast, safe, efficient, accessible and convenient transportation',
    children: [
      { name: 'Federal Aviation Administration', abbreviation: 'FAA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Federal Highway Administration', abbreviation: 'FHWA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Federal Transit Administration', abbreviation: 'FTA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Federal Railroad Administration', abbreviation: 'FRA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Highway Traffic Safety Administration', abbreviation: 'NHTSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Federal Motor Carrier Safety Administration', abbreviation: 'FMCSA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of the Treasury',
    abbreviation: 'TREAS',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.treasury.gov',
    description: 'Maintains a strong economy and creates economic and job opportunities',
    children: [
      { name: 'Internal Revenue Service', abbreviation: 'IRS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Bureau of the Fiscal Service', abbreviation: 'BFS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Financial Crimes Enforcement Network', abbreviation: 'FinCEN', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Office of the Comptroller of the Currency', abbreviation: 'OCC', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'U.S. Mint', abbreviation: 'MINT', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Department of Veterans Affairs',
    abbreviation: 'VA',
    level: 'department',
    isCfoActAgency: true,
    isCabinetDepartment: true,
    website: 'https://www.va.gov',
    description: 'Provides patient care and federal benefits to veterans and their dependents',
    children: [
      { name: 'Veterans Health Administration', abbreviation: 'VHA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Veterans Benefits Administration', abbreviation: 'VBA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'National Cemetery Administration', abbreviation: 'NCA', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },

  // ----------------------------------------
  // 9 INDEPENDENT CFO ACT AGENCIES
  // ----------------------------------------
  {
    name: 'Environmental Protection Agency',
    abbreviation: 'EPA',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.epa.gov',
    description: 'Protects human health and the environment',
    children: [
      { name: 'Office of Air and Radiation', abbreviation: 'OAR', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Office of Water', abbreviation: 'OW', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'General Services Administration',
    abbreviation: 'GSA',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.gsa.gov',
    description: 'Supports the basic functioning of federal agencies',
    children: [
      { name: 'Federal Acquisition Service', abbreviation: 'FAS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Public Buildings Service', abbreviation: 'PBS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Technology Transformation Services', abbreviation: 'TTS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'National Aeronautics and Space Administration',
    abbreviation: 'NASA',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.nasa.gov',
    description: 'Drives advances in science, technology, aeronautics, and space exploration',
    children: [
      { name: 'Goddard Space Flight Center', abbreviation: 'GSFC', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Jet Propulsion Laboratory', abbreviation: 'JPL', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
      { name: 'Johnson Space Center', abbreviation: 'JSC', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'National Science Foundation',
    abbreviation: 'NSF',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.nsf.gov',
    description: 'Promotes the progress of science and funds research and education',
  },
  {
    name: 'Office of Personnel Management',
    abbreviation: 'OPM',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.opm.gov',
    description: 'Serves as the chief human resources agency for the Federal Government',
    children: [
      { name: 'Federal Investigative Services', abbreviation: 'FIS', level: 'sub_agency', isCfoActAgency: false, isCabinetDepartment: false },
    ],
  },
  {
    name: 'Small Business Administration',
    abbreviation: 'SBA',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.sba.gov',
    description: 'Aids, counsels, assists, and protects the interests of small business concerns',
  },
  {
    name: 'Social Security Administration',
    abbreviation: 'SSA',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.ssa.gov',
    description: 'Administers retirement, disability, and survivor benefits',
  },
  {
    name: 'U.S. Agency for International Development',
    abbreviation: 'USAID',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.usaid.gov',
    description: 'Administers civilian foreign aid and development assistance',
  },
  {
    name: 'Nuclear Regulatory Commission',
    abbreviation: 'NRC',
    level: 'independent',
    isCfoActAgency: true,
    isCabinetDepartment: false,
    website: 'https://www.nrc.gov',
    description: 'Regulates civilian use of nuclear materials',
  },
];

// ========================================
// DATABASE OPERATIONS
// ========================================

async function insertOrganization(
  org: Organization,
  parentId: number | null,
  depth: number,
  hierarchyPath: string,
  displayOrder: number
): Promise<number> {
  const slug = slugify(org.name);
  const newPath = parentId ? `${hierarchyPath}` : '/';

  const result = await sql`
    INSERT INTO federal_organizations (
      name, short_name, abbreviation, slug,
      parent_id, level, hierarchy_path, depth,
      is_cfo_act_agency, is_cabinet_department,
      is_active, display_order, description, website
    ) VALUES (
      ${org.name},
      ${org.shortName || null},
      ${org.abbreviation},
      ${slug},
      ${parentId},
      ${org.level},
      ${newPath},
      ${depth},
      ${org.isCfoActAgency},
      ${org.isCabinetDepartment},
      true,
      ${displayOrder},
      ${org.description || null},
      ${org.website || null}
    )
    ON CONFLICT (slug) DO UPDATE SET
      name = EXCLUDED.name,
      abbreviation = EXCLUDED.abbreviation,
      parent_id = EXCLUDED.parent_id,
      level = EXCLUDED.level,
      hierarchy_path = EXCLUDED.hierarchy_path,
      depth = EXCLUDED.depth,
      is_cfo_act_agency = EXCLUDED.is_cfo_act_agency,
      is_cabinet_department = EXCLUDED.is_cabinet_department,
      display_order = EXCLUDED.display_order,
      description = EXCLUDED.description,
      website = EXCLUDED.website,
      updated_at = NOW()
    RETURNING id
  `;

  const insertedId = result[0].id;

  // Update hierarchy_path with the actual ID
  const fullPath = parentId ? `${hierarchyPath}${insertedId}/` : `/${insertedId}/`;
  await sql`
    UPDATE federal_organizations
    SET hierarchy_path = ${fullPath}
    WHERE id = ${insertedId}
  `;

  return insertedId;
}

async function seedHierarchy() {
  console.log('🏛️  Seeding Federal Organization Hierarchy\n');
  console.log('='.repeat(50));

  let totalInserted = 0;
  let displayOrder = 0;

  for (const org of CFO_ACT_AGENCIES) {
    displayOrder++;
    console.log(`\n📁 ${org.name} (${org.abbreviation})`);

    // Insert parent organization
    const parentId = await insertOrganization(org, null, 0, '/', displayOrder);
    totalInserted++;
    console.log(`   ✓ Inserted (id: ${parentId})`);

    // Insert children if any
    if (org.children && org.children.length > 0) {
      let childOrder = 0;
      for (const child of org.children) {
        childOrder++;
        const childId = await insertOrganization(
          child,
          parentId,
          1,
          `/${parentId}/`,
          childOrder
        );
        totalInserted++;
        console.log(`   └─ ${child.abbreviation}: ${child.name} (id: ${childId})`);
      }
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log(`\n✅ Successfully seeded ${totalInserted} organizations`);

  // Print summary statistics
  const stats = await sql`
    SELECT
      level,
      COUNT(*) as count,
      SUM(CASE WHEN is_cfo_act_agency THEN 1 ELSE 0 END) as cfo_act_count,
      SUM(CASE WHEN is_cabinet_department THEN 1 ELSE 0 END) as cabinet_count
    FROM federal_organizations
    GROUP BY level
    ORDER BY level
  `;

  console.log('\n📊 Summary by Level:');
  stats.forEach((row: any) => {
    console.log(`   ${row.level}: ${row.count} organizations`);
    if (row.cfo_act_count > 0) {
      console.log(`      - CFO Act agencies: ${row.cfo_act_count}`);
    }
    if (row.cabinet_count > 0) {
      console.log(`      - Cabinet departments: ${row.cabinet_count}`);
    }
  });

  const totalOrgs = await sql`SELECT COUNT(*) as total FROM federal_organizations`;
  console.log(`\n📈 Total organizations in database: ${totalOrgs[0].total}`);
}

// Run the seeding
seedHierarchy().catch(console.error);

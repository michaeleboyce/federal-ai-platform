/**
 * SQLite query layer for the Federal AI Use Case Inventory dashboard.
 *
 * All functions run on the server (Server Components) and return typed rows
 * that can be passed directly into React props. The database is opened once
 * in read-only mode and kept warm for the lifetime of the Node process.
 *
 * Usage (in a Server Component):
 *
 *   import { getGlobalStats, getAgencies } from '@/lib/db';
 *   const stats = getGlobalStats();
 *
 * Constraints:
 *   - Every query uses a prepared statement (SQL is static; parameters are bound).
 *   - No function returns `any` — see `@/lib/types` for the row shapes.
 *   - Callers must not mutate the returned objects (better-sqlite3 gives plain
 *     objects, but they should be treated as read-only view-models).
 */

import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import type {
  Agency,
  AgencyMaturity,
  AgencyWithMaturity,
  BreakdownRow,
  BureauBreakdown,
  ConsolidatedUseCase,
  ConsolidatedWithTags,
  GlobalStats,
  HeatmapCell,
  Product,
  ProductDetail,
  ProductWithCounts,
  TemplateDetail,
  TemplateWithCounts,
  UseCase,
  UseCaseFilterInput,
  UseCaseTag,
  UseCaseTemplate,
  UseCaseWithTags,
  VendorShareRow,
  YoYRow,
} from "./types";

/**
 * Normalize the 30+ free-text variants of `use_cases.stage_of_development`
 * into the 4 canonical OMB M-25-21 buckets. Usage:
 *   SELECT ${STAGE_BUCKET_SQL} AS stage_bucket FROM use_cases uc ...
 * Returns one of: 'pre_deployment' | 'pilot' | 'deployed' | 'retired' | 'unknown'.
 * Declared near the top of the file so it's safely accessible from
 * `getGlobalStats` and other functions above the main query-builders (const
 * declarations are not hoisted, so putting it below caused a temporal-dead-
 * zone ReferenceError when the home page rendered).
 */
export const STAGE_BUCKET_SQL = `
  CASE
    WHEN uc.stage_of_development IS NULL OR TRIM(uc.stage_of_development) = ''
      THEN 'unknown'
    WHEN LOWER(uc.stage_of_development) LIKE '%retired%'
      THEN 'retired'
    WHEN LOWER(uc.stage_of_development) LIKE '%pilot%'
      THEN 'pilot'
    WHEN LOWER(uc.stage_of_development) LIKE '%deployed%'
      THEN 'deployed'
    WHEN LOWER(uc.stage_of_development) LIKE '%pre-deployment%'
      OR LOWER(uc.stage_of_development) LIKE '%pre deployment%'
      OR LOWER(uc.stage_of_development) LIKE '%development or acquisition%'
      THEN 'pre_deployment'
    ELSE 'unknown'
  END
`;

// -----------------------------------------------------------------------------
// Connection singleton
// -----------------------------------------------------------------------------

// Prefer an in-project copy of the DB so the file travels with the Next.js
// bundle on Vercel (where `process.cwd()` is the function root, not the repo
// root). Fall back to the parent-directory layout used during local ETL
// iteration where the dashboard lives next to the data/ folder.
const DB_PATH = (() => {
  const inProject = path.join(process.cwd(), "data", "federal_ai_inventory_2025.db");
  const parent = path.join(process.cwd(), "..", "data", "federal_ai_inventory_2025.db");
  if (fs.existsSync(inProject)) return inProject;
  if (fs.existsSync(parent)) return parent;
  // Final fallback: let better-sqlite3 raise the familiar "not found" error
  // against the in-project path so messages point at the right place.
  return inProject;
})();

// Cache the handle across hot-reloads in dev. Node's module cache already
// gives us per-process caching in production.
declare global {
  // eslint-disable-next-line no-var
  var __aiInventoryDb: Database.Database | undefined;
}

function getDb(): Database.Database {
  if (!globalThis.__aiInventoryDb) {
    const db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
    // Read-only connection: no journal mode change needed. A small cache
    // pragma keeps frequently-used pages warm without bloating RSS.
    db.pragma("cache_size = -32000"); // ~32 MB page cache
    globalThis.__aiInventoryDb = db;
  }
  return globalThis.__aiInventoryDb;
}

/** Expose a raw handle for ad-hoc scripts. Do not use from React trees. */
export function rawDb(): Database.Database {
  return getDb();
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

/**
 * Agencies that actually contributed data to the 2025 inventory are filtered
 * by the SQL literal `'FOUND_2025','FOUND_2024_ONLY'`. Everything else
 * (NOT_FOUND, EXEMPT, SITE_DOWN, ZERO_USE_CASES, etc.) is still queryable by
 * id/abbreviation via `getAgencyById` / `getAgencyByAbbr`.
 */

// -----------------------------------------------------------------------------
// Agencies
// -----------------------------------------------------------------------------

/**
 * All agencies that have any inventory data. Sorted by name. Use
 * `getAllAgenciesIncludingEmpty()` if you need every row regardless of status.
 */
export function getAgencies(): Agency[] {
  const stmt = getDb().prepare<[], Agency>(`
    SELECT *
      FROM agencies
     WHERE status IN ('FOUND_2025', 'FOUND_2024_ONLY')
     ORDER BY name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

/** Every row in the `agencies` table, including those with no data. */
export function getAllAgenciesIncludingEmpty(): Agency[] {
  const stmt = getDb().prepare<[], Agency>(`
    SELECT * FROM agencies ORDER BY name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

/** Look up a single agency by its abbreviation (e.g. "VA", "DHS"). */
export function getAgencyByAbbr(abbr: string): AgencyWithMaturity | null {
  const stmt = getDb().prepare<[string], Agency>(`
    SELECT * FROM agencies WHERE LOWER(abbreviation) = LOWER(?) LIMIT 1
  `);
  const agency = stmt.get(abbr);
  if (!agency) return null;
  const maturity = getMaturityForAgency(agency.id);
  return { ...agency, maturity };
}

/** Look up a single agency by numeric primary key. */
export function getAgencyById(id: number): AgencyWithMaturity | null {
  const stmt = getDb().prepare<[number], Agency>(
    `SELECT * FROM agencies WHERE id = ? LIMIT 1`,
  );
  const agency = stmt.get(id);
  if (!agency) return null;
  const maturity = getMaturityForAgency(agency.id);
  return { ...agency, maturity };
}

function getMaturityForAgency(agencyId: number): AgencyMaturity | null {
  const stmt = getDb().prepare<[number], AgencyMaturity>(
    `SELECT * FROM agency_ai_maturity WHERE agency_id = ? LIMIT 1`,
  );
  return stmt.get(agencyId) ?? null;
}

/** Every `agency_ai_maturity` row joined onto its parent agency. */
export function getAgencyMaturity(): AgencyWithMaturity[] {
  // We query the two tables in one shot and assemble into the shape
  // `AgencyWithMaturity` on the JS side. Two prepared statements are cheap.
  const agencies = getDb()
    .prepare<[], Agency>(
      `SELECT a.*
         FROM agencies a
         JOIN agency_ai_maturity m ON m.agency_id = a.id
        ORDER BY a.name COLLATE NOCASE ASC`,
    )
    .all();
  const maturityRows = getDb()
    .prepare<[], AgencyMaturity>(`SELECT * FROM agency_ai_maturity`)
    .all();
  const byAgency = new Map<number, AgencyMaturity>();
  for (const m of maturityRows) byAgency.set(m.agency_id, m);
  return agencies.map((a) => ({ ...a, maturity: byAgency.get(a.id) ?? null }));
}

// -----------------------------------------------------------------------------
// Global stats (for homepage / About page)
// -----------------------------------------------------------------------------

export function getGlobalStats(): GlobalStats {
  const db = getDb();
  const total_use_cases = (
    db.prepare(`SELECT COUNT(*) AS c FROM use_cases`).get() as { c: number }
  ).c;
  const total_consolidated = (
    db
      .prepare(`SELECT COUNT(*) AS c FROM consolidated_use_cases`)
      .get() as { c: number }
  ).c;
  const total_agencies = (
    db.prepare(`SELECT COUNT(*) AS c FROM agencies`).get() as { c: number }
  ).c;
  const total_agencies_with_data = (
    db
      .prepare(
        `SELECT COUNT(*) AS c FROM agencies WHERE status IN ('FOUND_2025','FOUND_2024_ONLY')`,
      )
      .get() as { c: number }
  ).c;
  const total_products = (
    db.prepare(`SELECT COUNT(*) AS c FROM products`).get() as { c: number }
  ).c;
  const total_templates = (
    db.prepare(`SELECT COUNT(*) AS c FROM use_case_templates`).get() as {
      c: number;
    }
  ).c;
  const total_coding_entries = (
    db
      .prepare(`SELECT COUNT(*) AS c FROM use_case_tags WHERE is_coding_tool = 1`)
      .get() as { c: number }
  ).c;
  const total_genai_entries = (
    db
      .prepare(
        `SELECT COUNT(*) AS c FROM use_case_tags WHERE is_generative_ai = 1`,
      )
      .get() as { c: number }
  ).c;
  const total_high_impact_entries = (
    db
      .prepare(
        `SELECT COUNT(*) AS c FROM use_case_tags WHERE high_impact_designation = 'high_impact'`,
      )
      .get() as { c: number }
  ).c;

  // Stage-bucket counts over canonical use_cases only. Consolidated rows
  // have no stage_of_development column so they're excluded from this mix.
  const stageRows = db
    .prepare<[], { bucket: string; c: number }>(
      `SELECT ${STAGE_BUCKET_SQL} AS bucket, COUNT(*) AS c FROM use_cases uc GROUP BY bucket`,
    )
    .all();
  const stage_bucket_counts: Record<string, number> = {
    pre_deployment: 0,
    pilot: 0,
    deployed: 0,
    retired: 0,
    unknown: 0,
  };
  for (const r of stageRows) stage_bucket_counts[r.bucket] = r.c;

  return {
    total_use_cases,
    total_consolidated,
    total_agencies,
    total_agencies_with_data,
    total_products,
    total_templates,
    total_coding_entries,
    total_genai_entries,
    total_high_impact_entries,
    stage_bucket_counts,
  };
}

// -----------------------------------------------------------------------------
// Use cases
// -----------------------------------------------------------------------------

const USE_CASE_SELECT = `
  SELECT uc.*,
         a.name AS agency_name,
         a.abbreviation AS agency_abbreviation,
         p.canonical_name AS product_name,
         t.short_name AS template_short_name
    FROM use_cases uc
    JOIN agencies a ON a.id = uc.agency_id
    LEFT JOIN products p ON p.id = uc.product_id
    LEFT JOIN use_case_templates t ON t.id = uc.template_id
`;

type JoinedUseCaseRow = UseCase & {
  agency_name: string;
  agency_abbreviation: string;
  product_name: string | null;
  template_short_name: string | null;
};

function attachTagsToUseCases(rows: JoinedUseCaseRow[]): UseCaseWithTags[] {
  if (rows.length === 0) return [];
  const db = getDb();
  const ids = rows.map((r) => r.id);
  const placeholders = ids.map(() => "?").join(",");
  const tags = db
    .prepare<number[], UseCaseTag>(
      `SELECT * FROM use_case_tags WHERE use_case_id IN (${placeholders})`,
    )
    .all(...ids);
  const byId = new Map<number, UseCaseTag>();
  for (const t of tags) {
    if (t.use_case_id != null) byId.set(t.use_case_id, t);
  }
  return rows.map((r) => ({ ...r, tags: byId.get(r.id) ?? null }));
}

/** All use cases for a single agency (joined with tags, product, template). */
export function getUseCasesForAgency(agencyId: number): UseCaseWithTags[] {
  const stmt = getDb().prepare<[number], JoinedUseCaseRow>(
    `${USE_CASE_SELECT} WHERE uc.agency_id = ? ORDER BY uc.use_case_name COLLATE NOCASE ASC`,
  );
  return attachTagsToUseCases(stmt.all(agencyId));
}

/** Fetch one use case by slug. Returns null if not found. */
export function getUseCaseBySlug(slug: string): UseCaseWithTags | null {
  const stmt = getDb().prepare<[string], JoinedUseCaseRow>(
    `${USE_CASE_SELECT} WHERE uc.slug = ? LIMIT 1`,
  );
  const row = stmt.get(slug);
  if (!row) return null;
  return attachTagsToUseCases([row])[0] ?? null;
}

/** Fetch one use case by numeric id. */
export function getUseCaseById(id: number): UseCaseWithTags | null {
  const stmt = getDb().prepare<[number], JoinedUseCaseRow>(
    `${USE_CASE_SELECT} WHERE uc.id = ? LIMIT 1`,
  );
  const row = stmt.get(id);
  if (!row) return null;
  return attachTagsToUseCases([row])[0] ?? null;
}

/**
 * Full-text / faceted search over use cases. All filters are optional and
 * combined with AND. Pagination via `limit` / `offset`.
 */
export function getUseCasesFiltered(
  filters: UseCaseFilterInput = {},
): { rows: UseCaseWithTags[]; total: number } {
  const where: string[] = [];
  const params: (string | number)[] = [];

  if (filters.agencyId != null) {
    where.push("uc.agency_id = ?");
    params.push(filters.agencyId);
  }
  if (filters.agencyAbbr) {
    where.push("LOWER(a.abbreviation) = LOWER(?)");
    params.push(filters.agencyAbbr);
  }
  if (filters.stage) {
    where.push("uc.stage_of_development = ?");
    params.push(filters.stage);
  }
  if (filters.stageBuckets && filters.stageBuckets.length > 0) {
    // Normalized OMB M-25-21 buckets. Raw column has 30+ formatting variants
    // (e.g. "a) Pre-deployment – The use case is in a development...",
    // "Pre-deployment", "a) Pre-deployment - ..."). Bucket via substring match.
    const bucketExprs = filters.stageBuckets.map(() => `${STAGE_BUCKET_SQL} = ?`);
    where.push(`(${bucketExprs.join(" OR ")})`);
    for (const b of filters.stageBuckets) params.push(b);
  }
  if (filters.aiClassification) {
    where.push("uc.ai_classification = ?");
    params.push(filters.aiClassification);
  }
  if (filters.isHighImpact) {
    where.push("uc.is_high_impact = ?");
    params.push(filters.isHighImpact);
  }
  if (filters.productId != null) {
    where.push("uc.product_id = ?");
    params.push(filters.productId);
  }
  if (filters.templateId != null) {
    where.push("uc.template_id = ?");
    params.push(filters.templateId);
  }
  if (filters.vendor) {
    where.push("LOWER(uc.vendor_name) LIKE LOWER(?)");
    params.push(`%${filters.vendor}%`);
  }
  if (filters.search) {
    where.push(
      "(LOWER(uc.use_case_name) LIKE LOWER(?) OR LOWER(uc.problem_statement) LIKE LOWER(?) OR LOWER(uc.system_outputs) LIKE LOWER(?) OR LOWER(COALESCE(uc.vendor_name,'')) LIKE LOWER(?))",
    );
    const s = `%${filters.search}%`;
    params.push(s, s, s, s);
  }

  // Multi-select filters (Agent 4 additions).
  if (filters.agencyIds && filters.agencyIds.length > 0) {
    where.push(
      `uc.agency_id IN (${filters.agencyIds.map(() => "?").join(",")})`,
    );
    params.push(...filters.agencyIds);
  }
  if (filters.agencyTypes && filters.agencyTypes.length > 0) {
    where.push(
      `a.agency_type IN (${filters.agencyTypes.map(() => "?").join(",")})`,
    );
    params.push(...filters.agencyTypes);
  }
  if (filters.productIds && filters.productIds.length > 0) {
    where.push(
      `uc.product_id IN (${filters.productIds.map(() => "?").join(",")})`,
    );
    params.push(...filters.productIds);
  }
  if (filters.templateIds && filters.templateIds.length > 0) {
    where.push(
      `uc.template_id IN (${filters.templateIds.map(() => "?").join(",")})`,
    );
    params.push(...filters.templateIds);
  }
  if (filters.bureaus && filters.bureaus.length > 0) {
    where.push(
      `uc.bureau_component IN (${filters.bureaus.map(() => "?").join(",")})`,
    );
    params.push(...filters.bureaus);
  }
  if (filters.maturityTiers && filters.maturityTiers.length > 0) {
    // Maturity tier lives on agency_ai_maturity; filter by joining via agency_id.
    where.push(
      `uc.agency_id IN (SELECT agency_id FROM agency_ai_maturity WHERE maturity_tier IN (${filters.maturityTiers.map(() => "?").join(",")}))`,
    );
    params.push(...filters.maturityTiers);
  }

  const joinTags =
    filters.entryType != null ||
    filters.deploymentScope != null ||
    filters.aiSophistication != null ||
    filters.isCodingTool != null ||
    filters.isGenAI != null ||
    (filters.entryTypes != null && filters.entryTypes.length > 0) ||
    (filters.deploymentScopes != null && filters.deploymentScopes.length > 0) ||
    (filters.aiSophistications != null &&
      filters.aiSophistications.length > 0) ||
    (filters.architectureTypes != null &&
      filters.architectureTypes.length > 0) ||
    (filters.useTypes != null && filters.useTypes.length > 0) ||
    (filters.highImpactDesignations != null &&
      filters.highImpactDesignations.length > 0) ||
    filters.isGeneralLLMAccess != null ||
    filters.isPublicFacing != null ||
    filters.hasATOorFedRAMP != null ||
    filters.hasMeaningfulRiskDocs != null;

  if (joinTags) {
    if (filters.entryType) {
      where.push("tag.entry_type = ?");
      params.push(filters.entryType);
    }
    if (filters.deploymentScope) {
      where.push("tag.deployment_scope = ?");
      params.push(filters.deploymentScope);
    }
    if (filters.aiSophistication) {
      where.push("tag.ai_sophistication = ?");
      params.push(filters.aiSophistication);
    }
    if (filters.isCodingTool === true) where.push("tag.is_coding_tool = 1");
    if (filters.isCodingTool === false) where.push("COALESCE(tag.is_coding_tool,0) = 0");
    if (filters.isGenAI === true) where.push("tag.is_generative_ai = 1");
    if (filters.isGenAI === false) where.push("COALESCE(tag.is_generative_ai,0) = 0");

    // Multi-value tag filters
    if (filters.entryTypes && filters.entryTypes.length > 0) {
      where.push(
        `tag.entry_type IN (${filters.entryTypes.map(() => "?").join(",")})`,
      );
      params.push(...filters.entryTypes);
    }
    if (filters.deploymentScopes && filters.deploymentScopes.length > 0) {
      where.push(
        `tag.deployment_scope IN (${filters.deploymentScopes.map(() => "?").join(",")})`,
      );
      params.push(...filters.deploymentScopes);
    }
    if (filters.aiSophistications && filters.aiSophistications.length > 0) {
      where.push(
        `tag.ai_sophistication IN (${filters.aiSophistications.map(() => "?").join(",")})`,
      );
      params.push(...filters.aiSophistications);
    }
    if (filters.architectureTypes && filters.architectureTypes.length > 0) {
      where.push(
        `tag.architecture_type IN (${filters.architectureTypes.map(() => "?").join(",")})`,
      );
      params.push(...filters.architectureTypes);
    }
    if (filters.useTypes && filters.useTypes.length > 0) {
      where.push(
        `tag.use_type IN (${filters.useTypes.map(() => "?").join(",")})`,
      );
      params.push(...filters.useTypes);
    }
    if (
      filters.highImpactDesignations &&
      filters.highImpactDesignations.length > 0
    ) {
      where.push(
        `tag.high_impact_designation IN (${filters.highImpactDesignations.map(() => "?").join(",")})`,
      );
      params.push(...filters.highImpactDesignations);
    }
    if (filters.isGeneralLLMAccess === true)
      where.push("tag.is_general_llm_access = 1");
    if (filters.isPublicFacing === true) where.push("tag.is_public_facing = 1");
    if (filters.hasATOorFedRAMP === true)
      where.push("tag.has_ato_or_fedramp = 1");
    if (filters.hasMeaningfulRiskDocs === true)
      where.push("tag.has_meaningful_risk_docs = 1");
  }

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";
  const tagJoin = joinTags
    ? "LEFT JOIN use_case_tags tag ON tag.use_case_id = uc.id"
    : "";

  const limit = Math.min(filters.limit ?? 100, 1000);
  const offset = filters.offset ?? 0;

  const sql = `
    ${USE_CASE_SELECT.replace("FROM use_cases uc", `FROM use_cases uc ${tagJoin}`)}
    ${whereSql}
    ORDER BY uc.use_case_name COLLATE NOCASE ASC
    LIMIT ? OFFSET ?
  `;
  const countSql = `
    SELECT COUNT(*) AS c
      FROM use_cases uc
      JOIN agencies a ON a.id = uc.agency_id
      ${tagJoin}
      ${whereSql}
  `;

  const rows = getDb()
    .prepare<(string | number)[], JoinedUseCaseRow>(sql)
    .all(...params, limit, offset);
  const total = (
    getDb()
      .prepare<(string | number)[], { c: number }>(countSql)
      .get(...params) ?? { c: 0 }
  ).c;

  return { rows: attachTagsToUseCases(rows), total };
}

// -----------------------------------------------------------------------------
// Consolidated use cases
// -----------------------------------------------------------------------------

export function getConsolidatedForAgency(
  agencyId: number,
): ConsolidatedWithTags[] {
  const db = getDb();
  const stmt = db.prepare<[number], ConsolidatedUseCase & { agency_name: string; agency_abbreviation: string }>(`
    SELECT c.*,
           a.name AS agency_name,
           a.abbreviation AS agency_abbreviation
      FROM consolidated_use_cases c
      JOIN agencies a ON a.id = c.agency_id
     WHERE c.agency_id = ?
     ORDER BY c.ai_use_case COLLATE NOCASE ASC
  `);
  const rows = stmt.all(agencyId);
  if (rows.length === 0) return [];
  const ids = rows.map((r) => r.id);
  const placeholders = ids.map(() => "?").join(",");
  const tags = db
    .prepare<number[], UseCaseTag>(
      `SELECT * FROM use_case_tags WHERE consolidated_use_case_id IN (${placeholders})`,
    )
    .all(...ids);
  const byId = new Map<number, UseCaseTag>();
  for (const t of tags) {
    if (t.consolidated_use_case_id != null)
      byId.set(t.consolidated_use_case_id, t);
  }
  return rows.map((r) => ({ ...r, tags: byId.get(r.id) ?? null }));
}

// -----------------------------------------------------------------------------
// Products
// -----------------------------------------------------------------------------

/** All products joined with derived use-case and agency counts. */
/**
 * All products with per-product usage counts. Counts span both
 * `use_cases` and `consolidated_use_cases` because products are linked from
 * both tables; restricting to `use_cases` alone undercounts the widely-used
 * Appendix-B / COTS products (e.g. Microsoft 365 Copilot, GitHub Copilot).
 */
export function getAllProducts(): ProductWithCounts[] {
  const stmt = getDb().prepare<[], ProductWithCounts>(`
    SELECT p.*,
           COALESCE(uc_counts.use_case_count, 0) AS use_case_count,
           COALESCE(uc_counts.agency_count, 0) AS agency_count
      FROM products p
      LEFT JOIN (
        SELECT product_id,
               COUNT(*) AS use_case_count,
               COUNT(DISTINCT agency_id) AS agency_count
          FROM (
            SELECT product_id, agency_id FROM use_cases
              WHERE product_id IS NOT NULL
            UNION ALL
            SELECT product_id, agency_id FROM consolidated_use_cases
              WHERE product_id IS NOT NULL
          )
         GROUP BY product_id
      ) uc_counts ON uc_counts.product_id = p.id
     ORDER BY use_case_count DESC, p.canonical_name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

/** Product detail with aliases + list of agencies that have deployed it. */
export function getProductById(id: number): ProductDetail | null {
  const db = getDb();
  const product = db
    .prepare<[number], Product>(`SELECT * FROM products WHERE id = ? LIMIT 1`)
    .get(id);
  if (!product) return null;

  const aliases = db
    .prepare<[number], { alias_text: string }>(
      `SELECT alias_text FROM product_aliases WHERE product_id = ? ORDER BY alias_text`,
    )
    .all(id)
    .map((r) => r.alias_text);

  // Union use_cases + consolidated_use_cases so the product page shows every
  // agency that linked to this product, not just those that filed an
  // individual-format row for it.
  const agencies = db
    .prepare<[number, number], { id: number; name: string; abbreviation: string; count: number }>(`
      SELECT a.id, a.name, a.abbreviation, SUM(n) AS count
        FROM (
          SELECT agency_id, COUNT(*) AS n FROM use_cases
            WHERE product_id = ? GROUP BY agency_id
          UNION ALL
          SELECT agency_id, COUNT(*) AS n FROM consolidated_use_cases
            WHERE product_id = ? GROUP BY agency_id
        ) sub
        JOIN agencies a ON a.id = sub.agency_id
       GROUP BY a.id
       ORDER BY count DESC, a.name COLLATE NOCASE ASC
    `)
    .all(id, id);

  const use_case_count = (
    db
      .prepare<[number, number], { c: number }>(
        `SELECT
           (SELECT COUNT(*) FROM use_cases WHERE product_id = ?)
           +
           (SELECT COUNT(*) FROM consolidated_use_cases WHERE product_id = ?)
           AS c`,
      )
      .get(id, id) ?? { c: 0 }
  ).c;

  return { ...product, aliases, agencies, use_case_count };
}

/** Top products by distinct-agency adoption. */
export function getTopProducts(n = 10): ProductWithCounts[] {
  return getAllProducts()
    .slice()
    .sort((a, b) => b.agency_count - a.agency_count)
    .slice(0, n);
}

/**
 * Every canonical product linked to the given use case via the
 * ``use_case_products`` join table (Phase 2 Agent D). Sorted strongest-
 * evidence first so callers can pick the first element as the primary
 * product if they only need one. Returns an empty array if no linkage exists.
 */
export function getProductsForUseCase(
  useCaseId: number,
): Array<Product & { evidence_text: string | null; confidence: string | null }> {
  const db = getDb();
  const stmt = db.prepare<
    [number],
    Product & { evidence_text: string | null; confidence: string | null }
  >(`
    SELECT p.*,
           ucp.evidence_text AS evidence_text,
           ucp.confidence    AS confidence
      FROM use_case_products ucp
      JOIN products p ON p.id = ucp.product_id
     WHERE ucp.use_case_id = ?
     ORDER BY
       CASE ucp.confidence WHEN 'strong' THEN 0 ELSE 1 END,
       p.canonical_name COLLATE NOCASE ASC
  `);
  return stmt.all(useCaseId);
}

// -----------------------------------------------------------------------------
// Templates
// -----------------------------------------------------------------------------

export function getAllTemplates(): TemplateWithCounts[] {
  // Templates are referenced from both use_cases and consolidated_use_cases;
  // count across both so the list view matches reality.
  const stmt = getDb().prepare<[], TemplateWithCounts>(`
    SELECT t.*,
           COALESCE(counts.use_case_count, 0) AS use_case_count,
           COALESCE(counts.agency_count, 0) AS agency_count
      FROM use_case_templates t
      LEFT JOIN (
        SELECT template_id,
               COUNT(*) AS use_case_count,
               COUNT(DISTINCT agency_id) AS agency_count
          FROM (
            SELECT template_id, agency_id FROM use_cases
              WHERE template_id IS NOT NULL
            UNION ALL
            SELECT template_id, agency_id FROM consolidated_use_cases
              WHERE template_id IS NOT NULL
          )
         GROUP BY template_id
      ) counts ON counts.template_id = t.id
     ORDER BY use_case_count DESC, t.short_name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

export function getTemplateById(id: number): TemplateDetail | null {
  const db = getDb();
  const template = db
    .prepare<[number], UseCaseTemplate>(
      `SELECT * FROM use_case_templates WHERE id = ? LIMIT 1`,
    )
    .get(id);
  if (!template) return null;

  // Templates can be referenced from either `use_cases` or
  // `consolidated_use_cases` (the Appendix B COTS table is the common case).
  // Both must be unioned so the stats on the template detail page reflect
  // actual usage — otherwise template_id references that only exist on the
  // consolidated side are silently dropped.
  const agencies = db
    .prepare<[number, number], { id: number; name: string; abbreviation: string; count: number }>(`
      SELECT a.id, a.name, a.abbreviation, SUM(n) AS count
        FROM (
          SELECT agency_id, COUNT(*) AS n FROM use_cases
            WHERE template_id = ? GROUP BY agency_id
          UNION ALL
          SELECT agency_id, COUNT(*) AS n FROM consolidated_use_cases
            WHERE template_id = ? GROUP BY agency_id
        ) sub
        JOIN agencies a ON a.id = sub.agency_id
       GROUP BY a.id
       ORDER BY count DESC, a.name COLLATE NOCASE ASC
    `)
    .all(id, id);

  const products = db
    .prepare<[number, number], { id: number; canonical_name: string; vendor: string | null; count: number }>(`
      SELECT p.id, p.canonical_name, p.vendor, SUM(n) AS count
        FROM (
          SELECT product_id, COUNT(*) AS n FROM use_cases
            WHERE template_id = ? AND product_id IS NOT NULL GROUP BY product_id
          UNION ALL
          SELECT product_id, COUNT(*) AS n FROM consolidated_use_cases
            WHERE template_id = ? AND product_id IS NOT NULL GROUP BY product_id
        ) sub
        JOIN products p ON p.id = sub.product_id
       GROUP BY p.id
       ORDER BY count DESC, p.canonical_name COLLATE NOCASE ASC
    `)
    .all(id, id);

  const use_case_count = (
    db
      .prepare<[number, number], { c: number }>(
        `SELECT
           (SELECT COUNT(*) FROM use_cases WHERE template_id = ?)
           +
           (SELECT COUNT(*) FROM consolidated_use_cases WHERE template_id = ?)
           AS c`,
      )
      .get(id, id) ?? { c: 0 }
  ).c;

  return { ...template, agencies, products, use_case_count };
}

// -----------------------------------------------------------------------------
// Per-agency breakdown helpers (for donut/stacked charts on agency pages)
// -----------------------------------------------------------------------------

export function getBureauBreakdown(agencyId: number): BureauBreakdown[] {
  const stmt = getDb().prepare<[number], BureauBreakdown>(`
    SELECT COALESCE(bureau_component, '(Unassigned)') AS label,
           bureau_component,
           COUNT(*) AS count
      FROM use_cases
     WHERE agency_id = ?
     GROUP BY bureau_component
     ORDER BY count DESC
  `);
  return stmt.all(agencyId);
}

/*
 * The per-agency breakdown helpers below union use_case_tags rows from BOTH
 * source tables (individual and consolidated) so the donuts on the agency
 * detail page reflect every entry the agency filed — not just the individual
 * ones. `use_case_tags` carries either `use_case_id` OR
 * `consolidated_use_case_id`, never both, so the CHECK constraint on the
 * table guarantees a clean union.
 */
export function getEntryTypeBreakdown(agencyId: number): BreakdownRow[] {
  const stmt = getDb().prepare<[number, number], BreakdownRow>(`
    SELECT COALESCE(entry_type, 'unknown') AS label, COUNT(*) AS count
      FROM (
        SELECT t.entry_type FROM use_case_tags t
          JOIN use_cases uc ON uc.id = t.use_case_id
         WHERE uc.agency_id = ?
        UNION ALL
        SELECT t.entry_type FROM use_case_tags t
          JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
         WHERE c.agency_id = ?
      )
     GROUP BY entry_type
     ORDER BY count DESC
  `);
  return stmt.all(agencyId, agencyId);
}

export function getAISophisticationBreakdown(
  agencyId: number,
): BreakdownRow[] {
  const stmt = getDb().prepare<[number, number], BreakdownRow>(`
    SELECT COALESCE(ai_sophistication, 'unknown') AS label, COUNT(*) AS count
      FROM (
        SELECT t.ai_sophistication FROM use_case_tags t
          JOIN use_cases uc ON uc.id = t.use_case_id
         WHERE uc.agency_id = ?
        UNION ALL
        SELECT t.ai_sophistication FROM use_case_tags t
          JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
         WHERE c.agency_id = ?
      )
     GROUP BY ai_sophistication
     ORDER BY count DESC
  `);
  return stmt.all(agencyId, agencyId);
}

export function getDeploymentScopeBreakdown(
  agencyId: number,
): BreakdownRow[] {
  const stmt = getDb().prepare<[number, number], BreakdownRow>(`
    SELECT COALESCE(deployment_scope, 'unknown') AS label, COUNT(*) AS count
      FROM (
        SELECT t.deployment_scope FROM use_case_tags t
          JOIN use_cases uc ON uc.id = t.use_case_id
         WHERE uc.agency_id = ?
        UNION ALL
        SELECT t.deployment_scope FROM use_case_tags t
          JOIN consolidated_use_cases c ON c.id = t.consolidated_use_case_id
         WHERE c.agency_id = ?
      )
     GROUP BY deployment_scope
     ORDER BY count DESC
  `);
  return stmt.all(agencyId, agencyId);
}

export function getProductsForAgency(
  agencyId: number,
): Array<{
  id: number;
  canonical_name: string;
  vendor: string | null;
  use_case_count: number;
}> {
  const stmt = getDb().prepare<
    [number, number],
    { id: number; canonical_name: string; vendor: string | null; use_case_count: number }
  >(`
    SELECT p.id, p.canonical_name, p.vendor, SUM(n) AS use_case_count
      FROM (
        SELECT product_id, COUNT(*) AS n FROM use_cases
          WHERE agency_id = ? AND product_id IS NOT NULL GROUP BY product_id
        UNION ALL
        SELECT product_id, COUNT(*) AS n FROM consolidated_use_cases
          WHERE agency_id = ? AND product_id IS NOT NULL GROUP BY product_id
      ) sub
      JOIN products p ON p.id = sub.product_id
     GROUP BY p.id
     ORDER BY use_case_count DESC, p.canonical_name COLLATE NOCASE ASC
  `);
  return stmt.all(agencyId, agencyId);
}

// -----------------------------------------------------------------------------
// Cross-cutting analytics
// -----------------------------------------------------------------------------

/** Year-over-year growth per agency (for analytics bar chart). */
export function getYoYGrowthData(): YoYRow[] {
  const stmt = getDb().prepare<[], YoYRow>(`
    SELECT a.id AS agency_id,
           a.name,
           a.abbreviation,
           m.year_over_year_growth,
           m.total_use_cases
      FROM agency_ai_maturity m
      JOIN agencies a ON a.id = m.agency_id
     WHERE m.year_over_year_growth IS NOT NULL
     ORDER BY m.year_over_year_growth DESC
  `);
  return stmt.all();
}

/** Vendor market share = products/use cases/agencies per vendor. */
export function getVendorMarketShare(): VendorShareRow[] {
  const stmt = getDb().prepare<[], VendorShareRow>(`
    SELECT p.vendor AS vendor,
           COUNT(DISTINCT p.id) AS product_count,
           COUNT(sub.product_id) AS use_case_count,
           COUNT(DISTINCT sub.agency_id) AS agency_count
      FROM products p
      LEFT JOIN (
        SELECT product_id, agency_id FROM use_cases
          WHERE product_id IS NOT NULL
        UNION ALL
        SELECT product_id, agency_id FROM consolidated_use_cases
          WHERE product_id IS NOT NULL
      ) sub ON sub.product_id = p.id
     WHERE p.vendor IS NOT NULL AND p.vendor <> ''
     GROUP BY p.vendor
     ORDER BY use_case_count DESC, agency_count DESC
  `);
  return stmt.all();
}

/** Product × agency heatmap cells (only non-zero combinations are returned). */
export function getProductAgencyHeatmap(): HeatmapCell[] {
  const stmt = getDb().prepare<[], HeatmapCell>(`
    SELECT p.id AS product_id,
           p.canonical_name AS product_name,
           a.id AS agency_id,
           a.abbreviation AS agency_abbreviation,
           COUNT(*) AS count
      FROM (
        SELECT product_id, agency_id FROM use_cases
          WHERE product_id IS NOT NULL
        UNION ALL
        SELECT product_id, agency_id FROM consolidated_use_cases
          WHERE product_id IS NOT NULL
      ) sub
      JOIN products p ON p.id = sub.product_id
      JOIN agencies a ON a.id = sub.agency_id
     GROUP BY p.id, a.id
     ORDER BY count DESC
  `);
  return stmt.all();
}

/** Agencies ranked by coding-tool use case count. */
export function getCodingToolAgencies(): Array<{
  agency_id: number;
  name: string;
  abbreviation: string;
  coding_tool_count: number;
}> {
  const stmt = getDb().prepare<
    [],
    { agency_id: number; name: string; abbreviation: string; coding_tool_count: number }
  >(`
    SELECT a.id AS agency_id,
           a.name,
           a.abbreviation,
           COALESCE(m.coding_tool_count, 0) AS coding_tool_count
      FROM agencies a
      LEFT JOIN agency_ai_maturity m ON m.agency_id = a.id
     WHERE a.status IN ('FOUND_2025','FOUND_2024_ONLY')
     ORDER BY coding_tool_count DESC, a.name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

/** Homepage: maturity-tier summary with member abbreviation lists. */
export function getMaturityTierSummary(): Array<{
  tier: string;
  count: number;
  agencies: Array<{ id: number; name: string; abbreviation: string }>;
}> {
  const db = getDb();
  const rows = db
    .prepare<
      [],
      { tier: string; id: number; name: string; abbreviation: string }
    >(`
      SELECT COALESCE(m.maturity_tier, 'none') AS tier,
             a.id AS id,
             a.name AS name,
             a.abbreviation AS abbreviation
        FROM agency_ai_maturity m
        JOIN agencies a ON a.id = m.agency_id
       ORDER BY a.abbreviation COLLATE NOCASE ASC
    `)
    .all();
  const order = ["leading", "progressing", "early", "minimal", "none"];
  const byTier = new Map<
    string,
    Array<{ id: number; name: string; abbreviation: string }>
  >();
  for (const t of order) byTier.set(t, []);
  for (const r of rows) {
    const key = byTier.has(r.tier) ? r.tier : "none";
    byTier.get(key)!.push({ id: r.id, name: r.name, abbreviation: r.abbreviation });
  }
  return order.map((tier) => ({
    tier,
    count: byTier.get(tier)?.length ?? 0,
    agencies: byTier.get(tier) ?? [],
  }));
}

/** Homepage: agency_type x maturity_tier pivot for the stacked bar chart. */
export function getAgencyTypeByTier(): Array<{
  agency_type: string;
  leading: number;
  progressing: number;
  early: number;
  minimal: number;
  none: number;
}> {
  const db = getDb();
  const rows = db
    .prepare<
      [],
      { agency_type: string | null; tier: string | null }
    >(`
      SELECT COALESCE(a.agency_type, 'OTHER') AS agency_type,
             COALESCE(m.maturity_tier, 'none') AS tier
        FROM agencies a
        JOIN agency_ai_maturity m ON m.agency_id = a.id
    `)
    .all();

  const buckets = new Map<
    string,
    { agency_type: string; leading: number; progressing: number; early: number; minimal: number; none: number }
  >();
  for (const r of rows) {
    const type = r.agency_type ?? "OTHER";
    if (!buckets.has(type)) {
      buckets.set(type, {
        agency_type: type,
        leading: 0,
        progressing: 0,
        early: 0,
        minimal: 0,
        none: 0,
      });
    }
    const b = buckets.get(type)!;
    const tierKey = r.tier ?? "none";
    if (
      tierKey === "leading" ||
      tierKey === "progressing" ||
      tierKey === "early" ||
      tierKey === "minimal" ||
      tierKey === "none"
    ) {
      b[tierKey] += 1;
    } else {
      b.none += 1;
    }
  }
  return Array.from(buckets.values()).sort((a, b) =>
    a.agency_type.localeCompare(b.agency_type),
  );
}

/** Homepage: five most-recently-modified agencies (ignores NULLs). */
export function getRecentlyModifiedAgencies(n = 5): Agency[] {
  const stmt = getDb().prepare<[number], Agency>(`
    SELECT *
      FROM agencies
     WHERE status IN ('FOUND_2025','FOUND_2024_ONLY')
       AND last_modified IS NOT NULL
     ORDER BY last_modified DESC
     LIMIT ?
  `);
  return stmt.all(n);
}

// -----------------------------------------------------------------------------
// Analytics page helpers (Agent 6)
// -----------------------------------------------------------------------------

/**
 * Dense product × agency matrix for the heatmap. Returns the top N products
 * (by total use case count) × top M agencies (by total use case count) with
 * sparse cells — the consumer fills in zeros for missing combinations.
 */
export function getProductAgencyMatrix(
  topProducts = 15,
  topAgencies = 20,
): {
  products: Array<{ id: number; canonical_name: string; vendor: string | null; total: number }>;
  agencies: Array<{ id: number; name: string; abbreviation: string; total: number }>;
  cells: Array<{ product_id: number; agency_id: number; count: number }>;
} {
  const db = getDb();

  // Heatmap must span both inventory tables — Copilot-style products that only
  // surface in the consolidated filings were being dropped otherwise.
  const products = db
    .prepare<[number], { id: number; canonical_name: string; vendor: string | null; total: number }>(`
      SELECT p.id, p.canonical_name, p.vendor, COUNT(sub.product_id) AS total
        FROM products p
        JOIN (
          SELECT product_id FROM use_cases WHERE product_id IS NOT NULL
          UNION ALL
          SELECT product_id FROM consolidated_use_cases WHERE product_id IS NOT NULL
        ) sub ON sub.product_id = p.id
       GROUP BY p.id
       ORDER BY total DESC, p.canonical_name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(topProducts);

  const agencies = db
    .prepare<[number], { id: number; name: string; abbreviation: string; total: number }>(`
      SELECT a.id, a.name, a.abbreviation, COUNT(sub.agency_id) AS total
        FROM agencies a
        JOIN (
          SELECT agency_id FROM use_cases
          UNION ALL
          SELECT agency_id FROM consolidated_use_cases
        ) sub ON sub.agency_id = a.id
       WHERE a.status IN ('FOUND_2025','FOUND_2024_ONLY')
       GROUP BY a.id
       ORDER BY total DESC, a.name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(topAgencies);

  if (products.length === 0 || agencies.length === 0) {
    return { products, agencies, cells: [] };
  }

  const productIds = products.map((p) => p.id);
  const agencyIds = agencies.map((a) => a.id);
  const pPh = productIds.map(() => "?").join(",");
  const aPh = agencyIds.map(() => "?").join(",");

  const cells = db
    .prepare<number[], { product_id: number; agency_id: number; count: number }>(`
      SELECT product_id, agency_id, COUNT(*) AS count
        FROM (
          SELECT product_id, agency_id FROM use_cases WHERE product_id IS NOT NULL
          UNION ALL
          SELECT product_id, agency_id FROM consolidated_use_cases WHERE product_id IS NOT NULL
        )
       WHERE product_id IN (${pPh})
         AND agency_id IN (${aPh})
       GROUP BY product_id, agency_id
    `)
    .all(...productIds, ...agencyIds);

  return { products, agencies, cells };
}

/** Distribution of tag.architecture_type across all entries (individual + consolidated). */
export function getArchitectureDistribution(): BreakdownRow[] {
  const stmt = getDb().prepare<[], BreakdownRow>(`
    SELECT COALESCE(architecture_type, 'unknown') AS label,
           COUNT(*) AS count
      FROM use_case_tags
     GROUP BY architecture_type
     ORDER BY count DESC
  `);
  return stmt.all();
}

/**
 * Vendor share restricted to general-LLM entries — i.e. the "which chatbot do
 * agency staff actually have access to" slice. Counts across both individual
 * and consolidated tag rows since most agency-wide LLM access is reported
 * on the consolidated side.
 */
export function getLLMVendorShare(): BreakdownRow[] {
  const stmt = getDb().prepare<[], BreakdownRow>(`
    SELECT CASE
             WHEN is_microsoft_copilot = 1 THEN 'Microsoft'
             WHEN is_openai = 1 THEN 'OpenAI'
             WHEN is_anthropic = 1 THEN 'Anthropic'
             WHEN is_google = 1 THEN 'Google'
             WHEN is_aws_ai = 1 THEN 'Amazon'
             ELSE 'Other'
           END AS label,
           COUNT(*) AS count
      FROM use_case_tags
     WHERE ai_sophistication = 'general_llm'
     GROUP BY label
     ORDER BY count DESC
  `);
  return stmt.all();
}

/**
 * For the entry-type-mix stacked bar. One row per agency (that has data),
 * columns are raw counts of each tag.entry_type. The client normalizes to %.
 */
export function getEntryTypeMixByAgency(): Array<{
  agency_id: number;
  name: string;
  abbreviation: string;
  total: number;
  custom_system: number;
  product_deployment: number;
  bespoke_application: number;
  generic_use_pattern: number;
  product_feature: number;
  unknown: number;
}> {
  const stmt = getDb().prepare<
    [],
    { agency_id: number; name: string; abbreviation: string; entry_type: string | null; count: number }
  >(`
    SELECT a.id AS agency_id,
           a.name,
           a.abbreviation,
           COALESCE(tag.entry_type, 'unknown') AS entry_type,
           COUNT(*) AS count
      FROM use_cases uc
      JOIN agencies a ON a.id = uc.agency_id
      LEFT JOIN use_case_tags tag ON tag.use_case_id = uc.id
     WHERE a.status IN ('FOUND_2025','FOUND_2024_ONLY')
     GROUP BY a.id, entry_type
  `);
  const rows = stmt.all();

  const KNOWN = new Set([
    "custom_system",
    "product_deployment",
    "bespoke_application",
    "generic_use_pattern",
    "product_feature",
  ]);

  const byAgency = new Map<
    number,
    {
      agency_id: number;
      name: string;
      abbreviation: string;
      total: number;
      custom_system: number;
      product_deployment: number;
      bespoke_application: number;
      generic_use_pattern: number;
      product_feature: number;
      unknown: number;
    }
  >();
  for (const r of rows) {
    if (!byAgency.has(r.agency_id)) {
      byAgency.set(r.agency_id, {
        agency_id: r.agency_id,
        name: r.name,
        abbreviation: r.abbreviation,
        total: 0,
        custom_system: 0,
        product_deployment: 0,
        bespoke_application: 0,
        generic_use_pattern: 0,
        product_feature: 0,
        unknown: 0,
      });
    }
    const agg = byAgency.get(r.agency_id)!;
    agg.total += r.count;
    const key = r.entry_type ?? "unknown";
    if (KNOWN.has(key)) {
      (agg as unknown as Record<string, number>)[key] += r.count;
    } else {
      agg.unknown += r.count;
    }
  }

  return Array.from(byAgency.values())
    .filter((a) => a.total > 0)
    .sort((a, b) => b.total - a.total);
}

/** Data for the insight callout cards at the top of the Analytics page. */
export function getAnalyticsInsights(): {
  cfo_act_total: number;
  cfo_act_with_enterprise_llm: number;
  github_copilot_agencies: number;
  top_product_id: number | null;
  top_product_name: string | null;
  top_product_agencies: number;
  zero_coding_agencies: number;
  distinct_products_total: number;
  nasa_yoy_growth: number | null;
} {
  const db = getDb();

  const cfo_act_total = (
    db
      .prepare<[], { c: number }>(
        `SELECT COUNT(*) AS c FROM agencies WHERE agency_type = 'CFO_ACT' AND status IN ('FOUND_2025','FOUND_2024_ONLY')`,
      )
      .get() ?? { c: 0 }
  ).c;

  const cfo_act_with_enterprise_llm = (
    db
      .prepare<[], { c: number }>(`
        SELECT COUNT(*) AS c
          FROM agencies a
          JOIN agency_ai_maturity m ON m.agency_id = a.id
         WHERE a.agency_type = 'CFO_ACT'
           AND a.status IN ('FOUND_2025','FOUND_2024_ONLY')
           AND m.has_enterprise_llm = 1
      `)
      .get() ?? { c: 0 }
  ).c;

  const github_copilot_agencies = (
    db
      .prepare<[], { c: number }>(`
        SELECT COUNT(DISTINCT uc.agency_id) AS c
          FROM use_cases uc
          JOIN use_case_tags tag ON tag.use_case_id = uc.id
         WHERE tag.is_github_copilot = 1
      `)
      .get() ?? { c: 0 }
  ).c;

  const topProductRow = db
    .prepare<
      [],
      { id: number; canonical_name: string; agency_count: number }
    >(`
      SELECT p.id,
             p.canonical_name,
             COUNT(DISTINCT uc.agency_id) AS agency_count
        FROM products p
        JOIN use_cases uc ON uc.product_id = p.id
       GROUP BY p.id
       ORDER BY agency_count DESC
       LIMIT 1
    `)
    .get();

  const zero_coding_agencies = (
    db
      .prepare<[], { c: number }>(`
        SELECT COUNT(*) AS c
          FROM agencies a
          JOIN agency_ai_maturity m ON m.agency_id = a.id
         WHERE a.status IN ('FOUND_2025','FOUND_2024_ONLY')
           AND COALESCE(m.coding_tool_count, 0) = 0
      `)
      .get() ?? { c: 0 }
  ).c;

  const distinct_products_total = (
    db
      .prepare<[], { c: number }>(
        `SELECT COUNT(DISTINCT product_id) AS c FROM use_cases WHERE product_id IS NOT NULL`,
      )
      .get() ?? { c: 0 }
  ).c;

  const nasaRow = db
    .prepare<
      [],
      { year_over_year_growth: number | null }
    >(`
      SELECT m.year_over_year_growth
        FROM agencies a
        JOIN agency_ai_maturity m ON m.agency_id = a.id
       WHERE a.abbreviation = 'NASA'
       LIMIT 1
    `)
    .get();

  return {
    cfo_act_total,
    cfo_act_with_enterprise_llm,
    github_copilot_agencies,
    top_product_id: topProductRow?.id ?? null,
    top_product_name: topProductRow?.canonical_name ?? null,
    top_product_agencies: topProductRow?.agency_count ?? 0,
    zero_coding_agencies,
    distinct_products_total,
    nasa_yoy_growth: nasaRow?.year_over_year_growth ?? null,
  };
}

/** Agencies with maturity rows — for the scatter plot (YoY growth vs volume). */
export function getMaturityScatterData(): Array<{
  agency_id: number;
  name: string;
  abbreviation: string;
  year_over_year_growth: number | null;
  total_use_cases: number | null;
  maturity_tier: string | null;
}> {
  const stmt = getDb().prepare<
    [],
    {
      agency_id: number;
      name: string;
      abbreviation: string;
      year_over_year_growth: number | null;
      total_use_cases: number | null;
      maturity_tier: string | null;
    }
  >(`
    SELECT a.id AS agency_id,
           a.name,
           a.abbreviation,
           m.year_over_year_growth,
           m.total_use_cases,
           m.maturity_tier
      FROM agencies a
      JOIN agency_ai_maturity m ON m.agency_id = a.id
     WHERE m.year_over_year_growth IS NOT NULL
       AND m.total_use_cases IS NOT NULL
  `);
  return stmt.all();
}

/** Agencies that have enterprise-wide LLM access. */
export function getEnterpriseLLMAgencies(): Array<{
  agency_id: number;
  name: string;
  abbreviation: string;
  general_llm_count: number;
  has_enterprise_llm: number | null;
}> {
  const stmt = getDb().prepare<
    [],
    {
      agency_id: number;
      name: string;
      abbreviation: string;
      general_llm_count: number;
      has_enterprise_llm: number | null;
    }
  >(`
    SELECT a.id AS agency_id,
           a.name,
           a.abbreviation,
           COALESCE(m.general_llm_count, 0) AS general_llm_count,
           m.has_enterprise_llm AS has_enterprise_llm
      FROM agencies a
      LEFT JOIN agency_ai_maturity m ON m.agency_id = a.id
     WHERE a.status IN ('FOUND_2025','FOUND_2024_ONLY')
     ORDER BY has_enterprise_llm DESC, general_llm_count DESC, a.name COLLATE NOCASE ASC
  `);
  return stmt.all();
}

// -----------------------------------------------------------------------------
// Agent 4 additions — consolidated-use-case detail, related use cases,
// and export support.
// -----------------------------------------------------------------------------

/** Fetch one consolidated use case by slug, with tags + agency/product/template joins. */
export function getConsolidatedBySlug(
  slug: string,
): ConsolidatedWithTags | null {
  const db = getDb();
  type Row = ConsolidatedUseCase & {
    agency_name: string;
    agency_abbreviation: string;
    product_name: string | null;
    template_short_name: string | null;
  };
  const row = db
    .prepare<[string], Row>(
      `SELECT c.*,
              a.name AS agency_name,
              a.abbreviation AS agency_abbreviation,
              p.canonical_name AS product_name,
              t.short_name AS template_short_name
         FROM consolidated_use_cases c
         JOIN agencies a ON a.id = c.agency_id
         LEFT JOIN products p ON p.id = c.product_id
         LEFT JOIN use_case_templates t ON t.id = c.template_id
        WHERE c.slug = ? LIMIT 1`,
    )
    .get(slug);
  if (!row) return null;
  const tag = db
    .prepare<[number], UseCaseTag>(
      `SELECT * FROM use_case_tags WHERE consolidated_use_case_id = ? LIMIT 1`,
    )
    .get(row.id);
  return { ...row, tags: tag ?? null };
}

/**
 * Resolve a slug to either an individual use case or a consolidated one.
 * Used by the detail page which accepts both under `/use-cases/[slug]`.
 */
export function getUseCaseOrConsolidatedBySlug(
  slug: string,
):
  | { kind: "use_case"; data: UseCaseWithTags }
  | { kind: "consolidated"; data: ConsolidatedWithTags }
  | null {
  const uc = getUseCaseBySlug(slug);
  if (uc) return { kind: "use_case", data: uc };
  const c = getConsolidatedBySlug(slug);
  if (c) return { kind: "consolidated", data: c };
  return null;
}

/** Small list of related use cases within the same agency, excluding the given id. */
export function getRelatedByAgency(
  agencyId: number,
  excludeId: number,
  limit = 5,
): Array<{ id: number; slug: string | null; use_case_name: string; agency_abbreviation: string }> {
  return getDb()
    .prepare<
      [number, number, number],
      { id: number; slug: string | null; use_case_name: string; agency_abbreviation: string }
    >(`
      SELECT uc.id, uc.slug, uc.use_case_name, a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
       WHERE uc.agency_id = ? AND uc.id <> ?
       ORDER BY uc.use_case_name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(agencyId, excludeId, limit);
}

/** Small list of related use cases that share the same product. */
export function getRelatedByProduct(
  productId: number,
  excludeId: number,
  limit = 5,
): Array<{
  id: number;
  slug: string | null;
  use_case_name: string;
  agency_abbreviation: string;
}> {
  return getDb()
    .prepare<
      [number, number, number],
      { id: number; slug: string | null; use_case_name: string; agency_abbreviation: string }
    >(`
      SELECT uc.id, uc.slug, uc.use_case_name, a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
       WHERE uc.product_id = ? AND uc.id <> ?
       ORDER BY uc.use_case_name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(productId, excludeId, limit);
}

/** Small list of related use cases that share the same template. */
export function getRelatedByTemplate(
  templateId: number,
  excludeId: number,
  limit = 5,
): Array<{
  id: number;
  slug: string | null;
  use_case_name: string;
  agency_abbreviation: string;
}> {
  return getDb()
    .prepare<
      [number, number, number],
      { id: number; slug: string | null; use_case_name: string; agency_abbreviation: string }
    >(`
      SELECT uc.id, uc.slug, uc.use_case_name, a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
       WHERE uc.template_id = ? AND uc.id <> ?
       ORDER BY uc.use_case_name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(templateId, excludeId, limit);
}

/**
 * Facet counts useful to the filter sidebar (lightweight — just enum lists
 * actually present in the DB so we don't show filters for missing values).
 * Returned as maps keyed by the column we filter on.
 */
export function getUseCaseFacets(): {
  stages: string[];
  aiClassifications: string[];
  highImpact: string[];
  agencyTypes: string[];
  tagEntryTypes: string[];
  tagDeploymentScopes: string[];
  tagAISophistications: string[];
  tagArchitectureTypes: string[];
  tagUseTypes: string[];
  tagHighImpactDesignations: string[];
} {
  const db = getDb();
  const distinct = (table: string, col: string) =>
    db
      .prepare<[], { v: string }>(
        `SELECT DISTINCT ${col} AS v FROM ${table} WHERE ${col} IS NOT NULL AND ${col} <> '' ORDER BY v COLLATE NOCASE ASC`,
      )
      .all()
      .map((r) => r.v);

  return {
    stages: distinct("use_cases", "stage_of_development"),
    aiClassifications: distinct("use_cases", "ai_classification"),
    highImpact: distinct("use_cases", "is_high_impact"),
    agencyTypes: distinct("agencies", "agency_type"),
    tagEntryTypes: distinct("use_case_tags", "entry_type"),
    tagDeploymentScopes: distinct("use_case_tags", "deployment_scope"),
    tagAISophistications: distinct("use_case_tags", "ai_sophistication"),
    tagArchitectureTypes: distinct("use_case_tags", "architecture_type"),
    tagUseTypes: distinct("use_case_tags", "use_type"),
    tagHighImpactDesignations: distinct("use_case_tags", "high_impact_designation"),
  };
}

/** Minimal agency listing for filter dropdowns (id + abbr + name only). */
export function getAgencyOptions(): Array<{
  id: number;
  name: string;
  abbreviation: string;
}> {
  return getDb()
    .prepare<[], { id: number; name: string; abbreviation: string }>(
      `SELECT id, name, abbreviation
         FROM agencies
        WHERE status IN ('FOUND_2025','FOUND_2024_ONLY')
        ORDER BY name COLLATE NOCASE ASC`,
    )
    .all();
}

/** Minimal product listing for filter dropdowns. */
export function getProductOptions(): Array<{
  id: number;
  canonical_name: string;
  vendor: string | null;
  use_case_count: number;
}> {
  return getDb()
    .prepare<
      [],
      { id: number; canonical_name: string; vendor: string | null; use_case_count: number }
    >(
      `SELECT p.id,
              p.canonical_name,
              p.vendor,
              (
                SELECT COUNT(*) FROM use_cases uc WHERE uc.product_id = p.id
              ) + (
                SELECT COUNT(*) FROM consolidated_use_cases c WHERE c.product_id = p.id
              ) AS use_case_count
         FROM products p
        ORDER BY use_case_count DESC, p.canonical_name COLLATE NOCASE ASC`,
    )
    .all();
}

// -----------------------------------------------------------------------------
// Product detail — auxiliary helpers (Agent 5)
// -----------------------------------------------------------------------------

/** Child products that declare the given id as their parent_product_id. */
export function getChildProducts(parentId: number): Product[] {
  const stmt = getDb().prepare<[number], Product>(
    `SELECT * FROM products WHERE parent_product_id = ? ORDER BY canonical_name COLLATE NOCASE ASC`,
  );
  return stmt.all(parentId);
}

/** All use cases linked to a given product (joined with agency/template names + tags). */
export function getUseCasesForProduct(productId: number): UseCaseWithTags[] {
  const stmt = getDb().prepare<[number], JoinedUseCaseRow>(
    `${USE_CASE_SELECT} WHERE uc.product_id = ? ORDER BY a.name COLLATE NOCASE ASC, uc.use_case_name COLLATE NOCASE ASC`,
  );
  return attachTagsToUseCases(stmt.all(productId));
}

/** Count of consolidated_use_cases rows linked to a product. */
export function getConsolidatedCountForProduct(productId: number): number {
  const row = getDb()
    .prepare<[number], { c: number }>(
      `SELECT COUNT(*) AS c FROM consolidated_use_cases WHERE product_id = ?`,
    )
    .get(productId);
  return row?.c ?? 0;
}

/** Other products by the same vendor (excluding the given id). */
export function getProductsByVendor(
  vendor: string,
  excludeId: number,
): ProductWithCounts[] {
  const stmt = getDb().prepare<[string, number], ProductWithCounts>(`
    SELECT p.*,
           COALESCE(uc_counts.use_case_count, 0) AS use_case_count,
           COALESCE(uc_counts.agency_count, 0) AS agency_count
      FROM products p
      LEFT JOIN (
        SELECT product_id,
               COUNT(*) AS use_case_count,
               COUNT(DISTINCT agency_id) AS agency_count
          FROM use_cases
         WHERE product_id IS NOT NULL
         GROUP BY product_id
      ) uc_counts ON uc_counts.product_id = p.id
     WHERE p.vendor = ? AND p.id <> ?
     ORDER BY use_case_count DESC, p.canonical_name COLLATE NOCASE ASC
  `);
  return stmt.all(vendor, excludeId);
}

/** id → canonical_name lookup (for "Part of: X" on child-product cards). */
export function getProductNamesById(): Record<number, string> {
  const rows = getDb()
    .prepare<[], { id: number; canonical_name: string }>(
      `SELECT id, canonical_name FROM products`,
    )
    .all();
  const out: Record<number, string> = {};
  for (const r of rows) out[r.id] = r.canonical_name;
  return out;
}

// -----------------------------------------------------------------------------
// Template detail — auxiliary helpers (Agent 5)
// -----------------------------------------------------------------------------

export interface TemplateEntryRow {
  use_case_id: number | null;
  use_case_name: string;
  slug: string | null;
  agency_id: number;
  agency_name: string;
  agency_abbreviation: string;
  product_id: number | null;
  product_name: string | null;
  vendor: string | null;
  commercial_examples: string | null;
  estimated_licenses_users: string | null;
}

/**
 * Per-entry rows for a template — combines use_cases and any consolidated
 * rows for the same agency/template that don't already appear in use_cases.
 */
export function getEntriesForTemplate(templateId: number): TemplateEntryRow[] {
  const stmt = getDb().prepare<[number, number], TemplateEntryRow>(`
    SELECT uc.id AS use_case_id,
           uc.use_case_name AS use_case_name,
           uc.slug AS slug,
           a.id AS agency_id,
           a.name AS agency_name,
           a.abbreviation AS agency_abbreviation,
           p.id AS product_id,
           p.canonical_name AS product_name,
           p.vendor AS vendor,
           c.commercial_examples AS commercial_examples,
           c.estimated_licenses_users AS estimated_licenses_users
      FROM use_cases uc
      JOIN agencies a ON a.id = uc.agency_id
      LEFT JOIN products p ON p.id = uc.product_id
      LEFT JOIN consolidated_use_cases c
             ON c.agency_id = uc.agency_id
            AND c.template_id = uc.template_id
     WHERE uc.template_id = ?

    UNION ALL

    SELECT NULL AS use_case_id,
           c.ai_use_case AS use_case_name,
           c.slug AS slug,
           a.id AS agency_id,
           a.name AS agency_name,
           a.abbreviation AS agency_abbreviation,
           p.id AS product_id,
           p.canonical_name AS product_name,
           p.vendor AS vendor,
           c.commercial_examples AS commercial_examples,
           c.estimated_licenses_users AS estimated_licenses_users
      FROM consolidated_use_cases c
      JOIN agencies a ON a.id = c.agency_id
      LEFT JOIN products p ON p.id = c.product_id
     WHERE c.template_id = ?
       AND NOT EXISTS (
         SELECT 1 FROM use_cases uc2
          WHERE uc2.template_id = c.template_id
            AND uc2.agency_id = c.agency_id
       )
     ORDER BY agency_name COLLATE NOCASE ASC
  `);
  return stmt.all(templateId, templateId);
}

// -----------------------------------------------------------------------------
// Agent 7 additions — comparison page, About page, command palette.
// -----------------------------------------------------------------------------

/**
 * Most recent `date_accessed` across all agencies — used as the "data last
 * updated" footer / About timestamp.
 */
let _lastUpdatedCache: string | null | undefined = undefined;
export function getLastUpdatedDate(): string | null {
  if (_lastUpdatedCache !== undefined) return _lastUpdatedCache;
  const row = getDb()
    .prepare<[], { d: string | null }>(
      `SELECT MAX(date_accessed) AS d FROM agencies WHERE date_accessed IS NOT NULL`,
    )
    .get();
  _lastUpdatedCache = row?.d ?? null;
  return _lastUpdatedCache;
}

/** Agencies with an `inventory_page_url`. Used by About page data-sources list. */
export function getAgencyInventoryLinks(): Array<{
  id: number;
  name: string;
  abbreviation: string;
  inventory_page_url: string | null;
  csv_download_url: string | null;
  date_accessed: string | null;
}> {
  return getDb()
    .prepare<
      [],
      {
        id: number;
        name: string;
        abbreviation: string;
        inventory_page_url: string | null;
        csv_download_url: string | null;
        date_accessed: string | null;
      }
    >(`
      SELECT id, name, abbreviation, inventory_page_url, csv_download_url, date_accessed
        FROM agencies
       WHERE inventory_page_url IS NOT NULL AND inventory_page_url <> ''
       ORDER BY name COLLATE NOCASE ASC
    `)
    .all();
}

/**
 * Full comparison payload for a single agency — everything the /compare grid
 * needs, in one round trip.
 */
export interface AgencyCompareData {
  id: number;
  name: string;
  abbreviation: string;
  agency_type: string | null;
  status: string | null;
  maturity_tier: string | null;
  total_use_cases: number;
  distinct_products_deployed: number;
  general_llm_count: number;
  coding_tool_count: number;
  agentic_ai_count: number;
  custom_system_count: number;
  pct_deployed: number | null;
  pct_high_impact: number | null;
  pct_with_risk_docs: number | null;
  year_over_year_growth: number | null;
  has_enterprise_llm: number | null;
  has_coding_assistants: number | null;
  entry_type_mix: {
    custom_system: number;
    product_deployment: number;
    bespoke_application: number;
    generic_use_pattern: number;
    product_feature: number;
    unknown: number;
  };
  ai_sophistication_mix: Array<{ label: string; count: number }>;
  top_products: Array<{
    id: number;
    canonical_name: string;
    vendor: string | null;
    use_case_count: number;
  }>;
}

export function getAgencyCompareData(
  abbr: string,
): AgencyCompareData | null {
  const agency = getAgencyByAbbr(abbr);
  if (!agency) return null;

  const m = agency.maturity;
  const entryRows = getEntryTypeBreakdown(agency.id);
  const entryMix = {
    custom_system: 0,
    product_deployment: 0,
    bespoke_application: 0,
    generic_use_pattern: 0,
    product_feature: 0,
    unknown: 0,
  };
  for (const r of entryRows) {
    const key = r.label as keyof typeof entryMix;
    if (key in entryMix) entryMix[key] += r.count;
    else entryMix.unknown += r.count;
  }
  const sophistication = getAISophisticationBreakdown(agency.id).map((r) => ({
    label: r.label,
    count: r.count,
  }));
  const topProducts = getProductsForAgency(agency.id).slice(0, 5);

  return {
    id: agency.id,
    name: agency.name,
    abbreviation: agency.abbreviation,
    agency_type: agency.agency_type,
    status: agency.status,
    maturity_tier: m?.maturity_tier ?? null,
    total_use_cases: m?.total_use_cases ?? 0,
    distinct_products_deployed: m?.distinct_products_deployed ?? 0,
    general_llm_count: m?.general_llm_count ?? 0,
    coding_tool_count: m?.coding_tool_count ?? 0,
    agentic_ai_count: m?.agentic_ai_count ?? 0,
    custom_system_count: m?.custom_system_count ?? 0,
    pct_deployed: m?.pct_deployed ?? null,
    pct_high_impact: m?.pct_high_impact ?? null,
    pct_with_risk_docs: m?.pct_with_risk_docs ?? null,
    year_over_year_growth: m?.year_over_year_growth ?? null,
    has_enterprise_llm: m?.has_enterprise_llm ?? null,
    has_coding_assistants: m?.has_coding_assistants ?? null,
    entry_type_mix: entryMix,
    ai_sophistication_mix: sophistication,
    top_products: topProducts,
  };
}

/**
 * Command palette payload — small lists of agencies, products, templates, and
 * a capped list of use cases. The limit keeps the initial bundle small; fuzzy
 * matching happens client-side through cmdk.
 */
export interface CommandPaletteIndex {
  agencies: Array<{ id: number; abbreviation: string; name: string }>;
  products: Array<{ id: number; canonical_name: string; vendor: string | null }>;
  templates: Array<{ id: number; short_name: string | null; template_text: string }>;
  useCases: Array<{
    id: number;
    slug: string | null;
    use_case_name: string;
    agency_abbreviation: string;
  }>;
}

const _paletteCache = new Map<number, CommandPaletteIndex>();
export function getCommandPaletteIndex(
  useCaseLimit = 500,
): CommandPaletteIndex {
  const cached = _paletteCache.get(useCaseLimit);
  if (cached) return cached;
  const db = getDb();
  const agencies = db
    .prepare<[], { id: number; abbreviation: string; name: string }>(`
      SELECT id, abbreviation, name
        FROM agencies
       WHERE status IN ('FOUND_2025','FOUND_2024_ONLY')
       ORDER BY name COLLATE NOCASE ASC
    `)
    .all();
  const products = db
    .prepare<[], { id: number; canonical_name: string; vendor: string | null }>(`
      SELECT id, canonical_name, vendor
        FROM products
       ORDER BY canonical_name COLLATE NOCASE ASC
    `)
    .all();
  const templates = db
    .prepare<[], { id: number; short_name: string | null; template_text: string }>(`
      SELECT id, short_name, template_text
        FROM use_case_templates
       ORDER BY short_name COLLATE NOCASE ASC
    `)
    .all();
  const useCases = db
    .prepare<
      [number],
      { id: number; slug: string | null; use_case_name: string; agency_abbreviation: string }
    >(`
      SELECT uc.id, uc.slug, uc.use_case_name, a.abbreviation AS agency_abbreviation
        FROM use_cases uc
        JOIN agencies a ON a.id = uc.agency_id
       WHERE uc.slug IS NOT NULL
       ORDER BY uc.use_case_name COLLATE NOCASE ASC
       LIMIT ?
    `)
    .all(useCaseLimit);

  const result = { agencies, products, templates, useCases };
  _paletteCache.set(useCaseLimit, result);
  return result;
}

// packages/database/src/repositories/ProductRepository.ts
import { db } from '../db-connection';
import { eq, and, sql, like, or, desc, asc } from 'drizzle-orm';
import { products, type ProductRecord, type NewProductRecord } from '../schema/products';
import { aiServiceAnalysis } from '../schema/ai-services';

export class ProductRepository {
  // Insert a new product record
  async insert(productData: NewProductRecord): Promise<ProductRecord> {
    const [product] = await db.insert(products).values(productData).returning();
    return product;
  }

  // Insert multiple products
  async insertMany(productsData: NewProductRecord[]): Promise<ProductRecord[]> {
    return await db.insert(products).values(productsData).returning();
  }

  // Update a product record by ID
  async update(productId: number, updateData: Partial<ProductRecord>): Promise<ProductRecord[]> {
    return await db
      .update(products)
      .set({ ...updateData, updatedAt: new Date() })
      .where(eq(products.id, productId))
      .returning();
  }

  // Update by FedRAMP ID
  async updateByFedrampId(fedrampId: string, updateData: Partial<ProductRecord>): Promise<ProductRecord[]> {
    return await db
      .update(products)
      .set({ ...updateData, updatedAt: new Date() })
      .where(eq(products.fedrampId, fedrampId))
      .returning();
  }

  // Retrieve a product by its ID
  async getById(productId: number): Promise<ProductRecord | undefined> {
    const results = await db.select().from(products).where(eq(products.id, productId));
    return results.length ? results[0] : undefined;
  }

  // Retrieve a product by FedRAMP ID
  async getByFedrampId(fedrampId: string): Promise<ProductRecord | undefined> {
    const results = await db.select().from(products).where(eq(products.fedrampId, fedrampId));
    return results.length ? results[0] : undefined;
  }

  // Delete a product record by ID
  async delete(productId: number): Promise<void> {
    await db.delete(products).where(eq(products.id, productId));
  }

  // Get all products
  async getAll(orderBy: 'provider' | 'offering' | 'date' = 'provider'): Promise<ProductRecord[]> {
    const orderColumn =
      orderBy === 'provider' ? products.cloudServiceProvider :
      orderBy === 'offering' ? products.cloudServiceOffering :
      products.fedrampAuthorizationDate;

    return await db.select().from(products).orderBy(asc(orderColumn));
  }

  // Search products by provider, offering, or description
  async search(searchTerm: string): Promise<ProductRecord[]> {
    const searchPattern = `%${searchTerm}%`;
    return await db
      .select()
      .from(products)
      .where(
        or(
          like(products.cloudServiceProvider, searchPattern),
          like(products.cloudServiceOffering, searchPattern),
          like(products.serviceDescription, searchPattern)
        )
      );
  }

  // Get products by provider
  async getByProvider(provider: string): Promise<ProductRecord[]> {
    return await db
      .select()
      .from(products)
      .where(eq(products.cloudServiceProvider, provider))
      .orderBy(asc(products.cloudServiceOffering));
  }

  // Get products by status
  async getByStatus(status: string): Promise<ProductRecord[]> {
    return await db
      .select()
      .from(products)
      .where(eq(products.status, status));
  }

  // Get product count
  async getCount(): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(products);
    return result[0].count;
  }

  // Get unique providers
  async getUniqueProviders(): Promise<string[]> {
    const result = await db
      .selectDistinct({ provider: products.cloudServiceProvider })
      .from(products)
      .where(sql`${products.cloudServiceProvider} IS NOT NULL`)
      .orderBy(asc(products.cloudServiceProvider));
    return result.map((r) => r.provider!);
  }

  // Upsert - insert if not exists, update if exists
  async upsert(productData: NewProductRecord): Promise<ProductRecord> {
    const existing = await this.getByFedrampId(productData.fedrampId);

    if (existing) {
      const [updated] = await this.updateByFedrampId(productData.fedrampId, productData);
      return updated;
    } else {
      return await this.insert(productData);
    }
  }

  // Prepared query for products by provider
  private preparedProductsByProvider = db
    .select()
    .from(products)
    .where(eq(products.cloudServiceProvider, sql.placeholder('provider')))
    .prepare('get_products_by_provider');

  async executePreparedProductsByProvider(provider: string): Promise<ProductRecord[]> {
    return await this.preparedProductsByProvider.execute({ provider });
  }

  // Get all products with AI service counts
  async getAllWithServiceCounts(): Promise<(ProductRecord & { aiServiceCount: number; aiServices: string[] })[]> {
    const result = await db.execute(sql`
      SELECT
        p.*,
        COALESCE(COUNT(DISTINCT a.id), 0)::int as ai_service_count,
        COALESCE(
          ARRAY_AGG(DISTINCT a.service_name) FILTER (WHERE a.service_name IS NOT NULL),
          ARRAY[]::text[]
        ) as ai_services
      FROM products p
      LEFT JOIN ai_service_analysis a ON p.fedramp_id = a.product_id
      GROUP BY p.id
      ORDER BY p.cloud_service_provider ASC
    `);

    return result.rows.map((row: Record<string, unknown>) => ({
      id: row.id as number,
      fedrampId: row.fedramp_id as string,
      cloudServiceProvider: row.cloud_service_provider as string | null,
      cloudServiceOffering: row.cloud_service_offering as string | null,
      serviceDescription: row.service_description as string | null,
      businessCategories: row.business_categories as string | null,
      serviceModel: row.service_model as string | null,
      status: row.status as string | null,
      independentAssessor: row.independent_assessor as string | null,
      authorizations: row.authorizations as string | null,
      reuse: row.reuse as string | null,
      parentAgency: row.parent_agency as string | null,
      subAgency: row.sub_agency as string | null,
      atoIssuanceDate: row.ato_issuance_date as string | null,
      fedrampAuthorizationDate: row.fedramp_authorization_date as string | null,
      annualAssessmentDate: row.annual_assessment_date as string | null,
      atoExpirationDate: row.ato_expiration_date as string | null,
      htmlScraped: row.html_scraped as boolean,
      htmlPath: row.html_path as string | null,
      createdAt: new Date(row.created_at as string),
      updatedAt: new Date(row.updated_at as string),
      aiServiceCount: row.ai_service_count as number,
      aiServices: (row.ai_services as string[]) || [],
    }));
  }
}

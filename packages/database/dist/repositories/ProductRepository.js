"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProductRepository = void 0;
// packages/database/src/repositories/ProductRepository.ts
const db_connection_1 = require("../db-connection");
const drizzle_orm_1 = require("drizzle-orm");
const products_1 = require("../schema/products");
class ProductRepository {
    // Insert a new product record
    async insert(productData) {
        const [product] = await db_connection_1.db.insert(products_1.products).values(productData).returning();
        return product;
    }
    // Insert multiple products
    async insertMany(productsData) {
        return await db_connection_1.db.insert(products_1.products).values(productsData).returning();
    }
    // Update a product record by ID
    async update(productId, updateData) {
        return await db_connection_1.db
            .update(products_1.products)
            .set({ ...updateData, updatedAt: new Date() })
            .where((0, drizzle_orm_1.eq)(products_1.products.id, productId))
            .returning();
    }
    // Update by FedRAMP ID
    async updateByFedrampId(fedrampId, updateData) {
        return await db_connection_1.db
            .update(products_1.products)
            .set({ ...updateData, updatedAt: new Date() })
            .where((0, drizzle_orm_1.eq)(products_1.products.fedrampId, fedrampId))
            .returning();
    }
    // Retrieve a product by its ID
    async getById(productId) {
        const results = await db_connection_1.db.select().from(products_1.products).where((0, drizzle_orm_1.eq)(products_1.products.id, productId));
        return results.length ? results[0] : undefined;
    }
    // Retrieve a product by FedRAMP ID
    async getByFedrampId(fedrampId) {
        const results = await db_connection_1.db.select().from(products_1.products).where((0, drizzle_orm_1.eq)(products_1.products.fedrampId, fedrampId));
        return results.length ? results[0] : undefined;
    }
    // Delete a product record by ID
    async delete(productId) {
        await db_connection_1.db.delete(products_1.products).where((0, drizzle_orm_1.eq)(products_1.products.id, productId));
    }
    // Get all products
    async getAll(orderBy = 'provider') {
        const orderColumn = orderBy === 'provider' ? products_1.products.cloudServiceProvider :
            orderBy === 'offering' ? products_1.products.cloudServiceOffering :
                products_1.products.fedrampAuthorizationDate;
        return await db_connection_1.db.select().from(products_1.products).orderBy((0, drizzle_orm_1.asc)(orderColumn));
    }
    // Search products by provider, offering, or description
    async search(searchTerm) {
        const searchPattern = `%${searchTerm}%`;
        return await db_connection_1.db
            .select()
            .from(products_1.products)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.like)(products_1.products.cloudServiceProvider, searchPattern), (0, drizzle_orm_1.like)(products_1.products.cloudServiceOffering, searchPattern), (0, drizzle_orm_1.like)(products_1.products.serviceDescription, searchPattern)));
    }
    // Get products by provider
    async getByProvider(provider) {
        return await db_connection_1.db
            .select()
            .from(products_1.products)
            .where((0, drizzle_orm_1.eq)(products_1.products.cloudServiceProvider, provider))
            .orderBy((0, drizzle_orm_1.asc)(products_1.products.cloudServiceOffering));
    }
    // Get products by status
    async getByStatus(status) {
        return await db_connection_1.db
            .select()
            .from(products_1.products)
            .where((0, drizzle_orm_1.eq)(products_1.products.status, status));
    }
    // Get product count
    async getCount() {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(products_1.products);
        return result[0].count;
    }
    // Get unique providers
    async getUniqueProviders() {
        const result = await db_connection_1.db
            .selectDistinct({ provider: products_1.products.cloudServiceProvider })
            .from(products_1.products)
            .where((0, drizzle_orm_1.sql) `${products_1.products.cloudServiceProvider} IS NOT NULL`)
            .orderBy((0, drizzle_orm_1.asc)(products_1.products.cloudServiceProvider));
        return result.map((r) => r.provider);
    }
    // Upsert - insert if not exists, update if exists
    async upsert(productData) {
        const existing = await this.getByFedrampId(productData.fedrampId);
        if (existing) {
            const [updated] = await this.updateByFedrampId(productData.fedrampId, productData);
            return updated;
        }
        else {
            return await this.insert(productData);
        }
    }
    // Prepared query for products by provider
    preparedProductsByProvider = db_connection_1.db
        .select()
        .from(products_1.products)
        .where((0, drizzle_orm_1.eq)(products_1.products.cloudServiceProvider, drizzle_orm_1.sql.placeholder('provider')))
        .prepare('get_products_by_provider');
    async executePreparedProductsByProvider(provider) {
        return await this.preparedProductsByProvider.execute({ provider });
    }
}
exports.ProductRepository = ProductRepository;
//# sourceMappingURL=ProductRepository.js.map
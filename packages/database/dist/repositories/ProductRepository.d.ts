import { type ProductRecord, type NewProductRecord } from '../schema/products';
export declare class ProductRepository {
    insert(productData: NewProductRecord): Promise<ProductRecord>;
    insertMany(productsData: NewProductRecord[]): Promise<ProductRecord[]>;
    update(productId: number, updateData: Partial<ProductRecord>): Promise<ProductRecord[]>;
    updateByFedrampId(fedrampId: string, updateData: Partial<ProductRecord>): Promise<ProductRecord[]>;
    getById(productId: number): Promise<ProductRecord | undefined>;
    getByFedrampId(fedrampId: string): Promise<ProductRecord | undefined>;
    delete(productId: number): Promise<void>;
    getAll(orderBy?: 'provider' | 'offering' | 'date'): Promise<ProductRecord[]>;
    search(searchTerm: string): Promise<ProductRecord[]>;
    getByProvider(provider: string): Promise<ProductRecord[]>;
    getByStatus(status: string): Promise<ProductRecord[]>;
    getCount(): Promise<number>;
    getUniqueProviders(): Promise<string[]>;
    upsert(productData: NewProductRecord): Promise<ProductRecord>;
    private preparedProductsByProvider;
    executePreparedProductsByProvider(provider: string): Promise<ProductRecord[]>;
}
//# sourceMappingURL=ProductRepository.d.ts.map
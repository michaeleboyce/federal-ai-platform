import { type AIServiceAnalysisRecord, type NewAIServiceAnalysisRecord, type ProductAIAnalysisRunRecord, type NewProductAIAnalysisRunRecord } from '../schema/ai-services';
export declare class AIServiceRepository {
    insertAnalysis(analysisData: NewAIServiceAnalysisRecord): Promise<AIServiceAnalysisRecord>;
    insertManyAnalyses(analysesData: NewAIServiceAnalysisRecord[]): Promise<AIServiceAnalysisRecord[]>;
    getAnalysisById(id: number): Promise<AIServiceAnalysisRecord | undefined>;
    getAnalysesByProductId(productId: string): Promise<AIServiceAnalysisRecord[]>;
    getAllAIServices(): Promise<AIServiceAnalysisRecord[]>;
    getByAIType(type: 'ai' | 'genai' | 'llm'): Promise<AIServiceAnalysisRecord[]>;
    getByProvider(provider: string): Promise<AIServiceAnalysisRecord[]>;
    getStats(): Promise<{
        totalServices: number;
        aiCount: number;
        genaiCount: number;
        llmCount: number;
        uniqueProducts: number;
        uniqueProviders: number;
    }>;
    deleteByProductId(productId: string): Promise<void>;
    clearAll(): Promise<void>;
    recordAnalysisRun(runData: NewProductAIAnalysisRunRecord): Promise<ProductAIAnalysisRunRecord>;
    getLastAnalysisRun(productId: string): Promise<ProductAIAnalysisRunRecord | undefined>;
    getAnalysisRunStats(): Promise<{
        productsAnalyzed: number;
        lastRun: Date | null;
        totalServicesFound: number;
    }>;
    getAllAnalysisRuns(): Promise<ProductAIAnalysisRunRecord[]>;
    private preparedAnalysesByProduct;
    executePreparedAnalysesByProduct(productId: string): Promise<AIServiceAnalysisRecord[]>;
}
//# sourceMappingURL=AIServiceRepository.d.ts.map
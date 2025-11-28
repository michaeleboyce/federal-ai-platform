import { type AIUseCaseRecord, type NewAIUseCaseRecord, type AIUseCaseDetailRecord, type NewAIUseCaseDetailRecord, type UseCaseFedrampMatchRecord, type NewUseCaseFedrampMatchRecord } from '../schema/use-cases';
export declare class UseCaseRepository {
    insertUseCase(useCaseData: NewAIUseCaseRecord): Promise<AIUseCaseRecord>;
    insertManyUseCases(useCasesData: NewAIUseCaseRecord[]): Promise<AIUseCaseRecord[]>;
    updateUseCase(useCaseId: number, updateData: Partial<AIUseCaseRecord>): Promise<AIUseCaseRecord[]>;
    getUseCaseById(useCaseId: number): Promise<AIUseCaseRecord | undefined>;
    getUseCaseBySlug(slug: string): Promise<AIUseCaseRecord | undefined>;
    getAllUseCases(): Promise<AIUseCaseRecord[]>;
    getUseCasesByAgency(agency: string): Promise<AIUseCaseRecord[]>;
    getUseCasesByDomain(domain: string): Promise<AIUseCaseRecord[]>;
    getGenAIUseCases(): Promise<AIUseCaseRecord[]>;
    getLLMUseCases(): Promise<AIUseCaseRecord[]>;
    getChatbotUseCases(): Promise<AIUseCaseRecord[]>;
    searchUseCases(searchTerm: string): Promise<AIUseCaseRecord[]>;
    getUseCaseStats(): Promise<{
        totalUseCases: number;
        uniqueAgencies: number;
        genaiCount: number;
        llmCount: number;
        chatbotCount: number;
        classicMlCount: number;
        uniqueDomains: number;
    }>;
    deleteUseCase(useCaseId: number): Promise<void>;
    insertUseCaseDetails(detailsData: NewAIUseCaseDetailRecord): Promise<AIUseCaseDetailRecord>;
    getUseCaseDetails(useCaseId: number): Promise<AIUseCaseDetailRecord | undefined>;
    updateUseCaseDetails(useCaseId: number, updateData: Partial<AIUseCaseDetailRecord>): Promise<AIUseCaseDetailRecord[]>;
    deleteUseCaseDetails(useCaseId: number): Promise<void>;
    insertMatch(matchData: NewUseCaseFedrampMatchRecord): Promise<UseCaseFedrampMatchRecord>;
    insertManyMatches(matchesData: NewUseCaseFedrampMatchRecord[]): Promise<UseCaseFedrampMatchRecord[]>;
    getMatchesByUseCase(useCaseId: number): Promise<UseCaseFedrampMatchRecord[]>;
    getMatchesByConfidence(useCaseId: number, confidence: 'high' | 'medium' | 'low'): Promise<UseCaseFedrampMatchRecord[]>;
    getMatchesByProduct(productId: string): Promise<UseCaseFedrampMatchRecord[]>;
    deleteMatchesByUseCase(useCaseId: number): Promise<void>;
    deleteMatch(matchId: number): Promise<void>;
    private preparedUseCasesByAgency;
    executePreparedUseCasesByAgency(agency: string): Promise<AIUseCaseRecord[]>;
}
//# sourceMappingURL=UseCaseRepository.d.ts.map
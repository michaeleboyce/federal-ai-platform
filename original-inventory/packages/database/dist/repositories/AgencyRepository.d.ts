import { type AgencyAIUsageRecord, type NewAgencyAIUsageRecord, type AgencyServiceMatchRecord, type NewAgencyServiceMatchRecord } from '../schema/agencies';
export declare class AgencyRepository {
    insertUsage(usageData: NewAgencyAIUsageRecord): Promise<AgencyAIUsageRecord>;
    insertManyUsages(usagesData: NewAgencyAIUsageRecord[]): Promise<AgencyAIUsageRecord[]>;
    updateUsage(agencyId: number, updateData: Partial<AgencyAIUsageRecord>): Promise<AgencyAIUsageRecord[]>;
    getUsageById(agencyId: number): Promise<AgencyAIUsageRecord | undefined>;
    getUsageBySlug(slug: string): Promise<AgencyAIUsageRecord | undefined>;
    getAllUsages(): Promise<AgencyAIUsageRecord[]>;
    getUsagesByCategory(category: 'staff_llm' | 'specialized'): Promise<AgencyAIUsageRecord[]>;
    getAgenciesWithStaffLLM(): Promise<AgencyAIUsageRecord[]>;
    getAgenciesWithCodingAssistant(): Promise<AgencyAIUsageRecord[]>;
    searchUsages(searchTerm: string): Promise<AgencyAIUsageRecord[]>;
    getUniqueAgencies(): Promise<string[]>;
    getUsageCount(): Promise<number>;
    deleteUsage(agencyId: number): Promise<void>;
    clearAllUsages(): Promise<void>;
    insertMatch(matchData: NewAgencyServiceMatchRecord): Promise<AgencyServiceMatchRecord>;
    insertManyMatches(matchesData: NewAgencyServiceMatchRecord[]): Promise<AgencyServiceMatchRecord[]>;
    getMatchesByAgency(agencyId: number): Promise<AgencyServiceMatchRecord[]>;
    getMatchesByConfidence(agencyId: number, confidence: 'high' | 'medium' | 'low'): Promise<AgencyServiceMatchRecord[]>;
    getMatchesByProduct(productId: string): Promise<AgencyServiceMatchRecord[]>;
    deleteMatchesByAgency(agencyId: number): Promise<void>;
    deleteMatch(matchId: number): Promise<void>;
    clearAllMatches(): Promise<void>;
    getMatchCountByAgency(agencyId: number): Promise<number>;
    private preparedMatchesByAgency;
    executePreparedMatchesByAgency(agencyId: number): Promise<AgencyServiceMatchRecord[]>;
}
//# sourceMappingURL=AgencyRepository.d.ts.map
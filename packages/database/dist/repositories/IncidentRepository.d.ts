import { type IncidentRecord, type NewIncidentRecord, type ReportRecord, type NewReportRecord } from '../schema/incidents';
import { type EntityRecord, type NewEntityRecord, type IncidentEntityRecord, type NewIncidentEntityRecord } from '../schema/entities';
import { type IncidentSecurityRecord, type NewIncidentSecurityRecord, type ClassificationRecord, type NewClassificationRecord } from '../schema/incident-security';
export declare class IncidentRepository {
    insertIncident(incidentData: NewIncidentRecord): Promise<IncidentRecord>;
    insertManyIncidents(incidentsData: NewIncidentRecord[]): Promise<IncidentRecord[]>;
    getIncidentById(id: number): Promise<IncidentRecord | undefined>;
    getIncidentByIncidentId(incidentId: number): Promise<IncidentRecord | undefined>;
    getAllIncidents(limit?: number): Promise<IncidentRecord[]>;
    searchIncidents(searchTerm: string, limit?: number): Promise<IncidentRecord[]>;
    getIncidentCount(): Promise<number>;
    deleteIncident(id: number): Promise<void>;
    insertReport(reportData: NewReportRecord): Promise<ReportRecord>;
    insertManyReports(reportsData: NewReportRecord[]): Promise<ReportRecord[]>;
    getReportsByIncidentId(incidentId: number, limit?: number): Promise<ReportRecord[]>;
    getReportCount(): Promise<number>;
    insertEntity(entityData: NewEntityRecord): Promise<EntityRecord>;
    insertManyEntities(entitiesData: NewEntityRecord[]): Promise<EntityRecord[]>;
    getEntityByEntityId(entityId: string): Promise<EntityRecord | undefined>;
    getAllEntities(): Promise<EntityRecord[]>;
    getEntityCount(): Promise<number>;
    insertIncidentEntity(data: NewIncidentEntityRecord): Promise<IncidentEntityRecord>;
    insertManyIncidentEntities(data: NewIncidentEntityRecord[]): Promise<IncidentEntityRecord[]>;
    getEntitiesForIncident(incidentId: number): Promise<{
        id: number;
        incidentId: number;
        entityId: string;
        role: string;
        entityName: string | null;
    }[]>;
    getIncidentsForEntity(entityId: string): Promise<IncidentRecord[]>;
    insertSecurity(securityData: NewIncidentSecurityRecord): Promise<IncidentSecurityRecord>;
    insertManySecurity(data: NewIncidentSecurityRecord[]): Promise<IncidentSecurityRecord[]>;
    getSecurityByIncidentId(incidentId: number): Promise<IncidentSecurityRecord | undefined>;
    getIncidentsWithDataLeaks(): Promise<IncidentSecurityRecord[]>;
    getIncidentsWithCyberAttacks(): Promise<IncidentSecurityRecord[]>;
    getLLMIncidents(): Promise<IncidentSecurityRecord[]>;
    insertClassification(data: NewClassificationRecord): Promise<ClassificationRecord>;
    getClassificationsByIncidentId(incidentId: number): Promise<ClassificationRecord[]>;
    getStats(): Promise<{
        totalIncidents: number;
        totalReports: number;
        totalEntities: number;
        confirmedDataLeaks: number;
        suspectedDataLeaks: number;
        confirmedCyberAttacks: number;
        suspectedCyberAttacks: number;
        llmIncidents: number;
        mostRecentDate: string | null;
    }>;
    getIncidentWithDetails(incidentId: number): Promise<{
        incident: IncidentRecord | undefined;
        security: IncidentSecurityRecord | undefined;
        entities: {
            id: number;
            incidentId: number;
            entityId: string;
            role: string;
            entityName: string | null;
        }[];
        reports: ReportRecord[];
        classifications: ClassificationRecord[];
    }>;
}
//# sourceMappingURL=IncidentRepository.d.ts.map
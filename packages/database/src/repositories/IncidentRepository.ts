// packages/database/src/repositories/IncidentRepository.ts
import { db } from '../db-connection';
import { eq, and, sql, like, or, desc, asc, isNotNull } from 'drizzle-orm';
import {
  incidents,
  reports,
  type IncidentRecord,
  type NewIncidentRecord,
  type ReportRecord,
  type NewReportRecord
} from '../schema/incidents';
import {
  entities,
  incidentEntities,
  type EntityRecord,
  type NewEntityRecord,
  type IncidentEntityRecord,
  type NewIncidentEntityRecord
} from '../schema/entities';
import {
  incidentSecurity,
  classifications,
  taxa,
  type IncidentSecurityRecord,
  type NewIncidentSecurityRecord,
  type ClassificationRecord,
  type NewClassificationRecord
} from '../schema/incident-security';

export class IncidentRepository {
  // ============ INCIDENTS ============

  // Insert a new incident
  async insertIncident(incidentData: NewIncidentRecord): Promise<IncidentRecord> {
    const [incident] = await db.insert(incidents).values(incidentData).returning();
    return incident;
  }

  // Insert multiple incidents
  async insertManyIncidents(incidentsData: NewIncidentRecord[]): Promise<IncidentRecord[]> {
    if (incidentsData.length === 0) return [];
    return await db.insert(incidents).values(incidentsData).returning();
  }

  // Get incident by ID
  async getIncidentById(id: number): Promise<IncidentRecord | undefined> {
    const results = await db.select().from(incidents).where(eq(incidents.id, id));
    return results.length ? results[0] : undefined;
  }

  // Get incident by incident_id (the AIID unique identifier)
  async getIncidentByIncidentId(incidentId: number): Promise<IncidentRecord | undefined> {
    const results = await db.select().from(incidents).where(eq(incidents.incidentId, incidentId));
    return results.length ? results[0] : undefined;
  }

  // Get all incidents
  async getAllIncidents(limit: number = 1000): Promise<IncidentRecord[]> {
    return await db
      .select()
      .from(incidents)
      .orderBy(desc(incidents.incidentId))
      .limit(limit);
  }

  // Search incidents by title or description
  async searchIncidents(searchTerm: string, limit: number = 100): Promise<IncidentRecord[]> {
    const searchPattern = `%${searchTerm}%`;
    return await db
      .select()
      .from(incidents)
      .where(
        or(
          like(incidents.title, searchPattern),
          like(incidents.description, searchPattern)
        )
      )
      .orderBy(desc(incidents.incidentId))
      .limit(limit);
  }

  // Get incident count
  async getIncidentCount(): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidents);
    return result[0].count;
  }

  // Delete incident
  async deleteIncident(id: number): Promise<void> {
    await db.delete(incidents).where(eq(incidents.id, id));
  }

  // ============ REPORTS ============

  // Insert a report
  async insertReport(reportData: NewReportRecord): Promise<ReportRecord> {
    const [report] = await db.insert(reports).values(reportData).returning();
    return report;
  }

  // Insert multiple reports
  async insertManyReports(reportsData: NewReportRecord[]): Promise<ReportRecord[]> {
    if (reportsData.length === 0) return [];
    return await db.insert(reports).values(reportsData).returning();
  }

  // Get reports by incident
  async getReportsByIncidentId(incidentId: number, limit: number = 10): Promise<ReportRecord[]> {
    return await db
      .select()
      .from(reports)
      .where(eq(reports.incidentId, incidentId))
      .limit(limit);
  }

  // Get report count
  async getReportCount(): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(reports);
    return result[0].count;
  }

  // ============ ENTITIES ============

  // Insert an entity
  async insertEntity(entityData: NewEntityRecord): Promise<EntityRecord> {
    const [entity] = await db.insert(entities).values(entityData).returning();
    return entity;
  }

  // Insert multiple entities
  async insertManyEntities(entitiesData: NewEntityRecord[]): Promise<EntityRecord[]> {
    if (entitiesData.length === 0) return [];
    return await db.insert(entities).values(entitiesData).returning();
  }

  // Get entity by ID
  async getEntityByEntityId(entityId: string): Promise<EntityRecord | undefined> {
    const results = await db.select().from(entities).where(eq(entities.entityId, entityId));
    return results.length ? results[0] : undefined;
  }

  // Get all entities
  async getAllEntities(): Promise<EntityRecord[]> {
    return await db.select().from(entities).orderBy(asc(entities.name));
  }

  // Get entity count
  async getEntityCount(): Promise<number> {
    const result = await db
      .select({ count: sql<number>`count(*)` })
      .from(entities);
    return result[0].count;
  }

  // ============ INCIDENT-ENTITY RELATIONSHIPS ============

  // Insert incident-entity relationship
  async insertIncidentEntity(data: NewIncidentEntityRecord): Promise<IncidentEntityRecord> {
    const [record] = await db.insert(incidentEntities).values(data).returning();
    return record;
  }

  // Insert multiple relationships
  async insertManyIncidentEntities(data: NewIncidentEntityRecord[]): Promise<IncidentEntityRecord[]> {
    if (data.length === 0) return [];
    return await db.insert(incidentEntities).values(data).returning();
  }

  // Get entities for an incident
  async getEntitiesForIncident(incidentId: number): Promise<{ id: number; incidentId: number; entityId: string; role: string; entityName: string | null }[]> {
    const results = await db
      .select({
        id: incidentEntities.id,
        incidentId: incidentEntities.incidentId,
        entityId: incidentEntities.entityId,
        role: incidentEntities.role,
        entityName: entities.name,
      })
      .from(incidentEntities)
      .leftJoin(entities, eq(incidentEntities.entityId, entities.entityId))
      .where(eq(incidentEntities.incidentId, incidentId));
    return results;
  }

  // Get incidents for an entity
  async getIncidentsForEntity(entityId: string): Promise<IncidentRecord[]> {
    const incidentIds = await db
      .select({ incidentId: incidentEntities.incidentId })
      .from(incidentEntities)
      .where(eq(incidentEntities.entityId, entityId));

    if (incidentIds.length === 0) return [];

    return await db
      .select()
      .from(incidents)
      .where(sql`${incidents.incidentId} IN (${incidentIds.map(r => r.incidentId).join(',')})`);
  }

  // ============ SECURITY DATA ============

  // Insert security data
  async insertSecurity(securityData: NewIncidentSecurityRecord): Promise<IncidentSecurityRecord> {
    const [record] = await db.insert(incidentSecurity).values(securityData).returning();
    return record;
  }

  // Insert multiple security records
  async insertManySecurity(data: NewIncidentSecurityRecord[]): Promise<IncidentSecurityRecord[]> {
    if (data.length === 0) return [];
    return await db.insert(incidentSecurity).values(data).returning();
  }

  // Get security data for incident
  async getSecurityByIncidentId(incidentId: number): Promise<IncidentSecurityRecord | undefined> {
    const results = await db
      .select()
      .from(incidentSecurity)
      .where(eq(incidentSecurity.incidentId, incidentId));
    return results.length ? results[0] : undefined;
  }

  // Get incidents with data leaks
  async getIncidentsWithDataLeaks(): Promise<IncidentSecurityRecord[]> {
    return await db
      .select()
      .from(incidentSecurity)
      .where(
        or(
          eq(incidentSecurity.securityDataLeakPresence, 'confirmed'),
          eq(incidentSecurity.securityDataLeakPresence, 'suspected')
        )
      );
  }

  // Get incidents with cyber attacks
  async getIncidentsWithCyberAttacks(): Promise<IncidentSecurityRecord[]> {
    return await db
      .select()
      .from(incidentSecurity)
      .where(
        or(
          eq(incidentSecurity.cyberAttackFlag, 'confirmed_attack'),
          eq(incidentSecurity.cyberAttackFlag, 'suspected_attack')
        )
      );
  }

  // Get incidents involving LLMs
  async getLLMIncidents(): Promise<IncidentSecurityRecord[]> {
    return await db
      .select()
      .from(incidentSecurity)
      .where(eq(incidentSecurity.llmOrChatbotInvolved, true));
  }

  // ============ CLASSIFICATIONS ============

  // Insert classification
  async insertClassification(data: NewClassificationRecord): Promise<ClassificationRecord> {
    const [record] = await db.insert(classifications).values(data).returning();
    return record;
  }

  // Get classifications for incident
  async getClassificationsByIncidentId(incidentId: number): Promise<ClassificationRecord[]> {
    return await db
      .select()
      .from(classifications)
      .where(eq(classifications.incidentId, incidentId));
  }

  // ============ STATISTICS ============

  // Get comprehensive stats
  async getStats(): Promise<{
    totalIncidents: number;
    totalReports: number;
    totalEntities: number;
    confirmedDataLeaks: number;
    suspectedDataLeaks: number;
    confirmedCyberAttacks: number;
    suspectedCyberAttacks: number;
    llmIncidents: number;
    mostRecentDate: string | null;
  }> {
    const [incidentCount] = await db.select({ count: sql<number>`count(*)` }).from(incidents);
    const [reportCount] = await db.select({ count: sql<number>`count(*)` }).from(reports);
    const [entityCount] = await db.select({ count: sql<number>`count(*)` }).from(entities);

    const [confirmedLeaks] = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidentSecurity)
      .where(eq(incidentSecurity.securityDataLeakPresence, 'confirmed'));

    const [suspectedLeaks] = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidentSecurity)
      .where(eq(incidentSecurity.securityDataLeakPresence, 'suspected'));

    const [confirmedAttacks] = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidentSecurity)
      .where(eq(incidentSecurity.cyberAttackFlag, 'confirmed_attack'));

    const [suspectedAttacks] = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidentSecurity)
      .where(eq(incidentSecurity.cyberAttackFlag, 'suspected_attack'));

    const [llmCount] = await db
      .select({ count: sql<number>`count(*)` })
      .from(incidentSecurity)
      .where(eq(incidentSecurity.llmOrChatbotInvolved, true));

    const [mostRecent] = await db
      .select({ date: incidents.date })
      .from(incidents)
      .where(isNotNull(incidents.date))
      .orderBy(desc(incidents.date))
      .limit(1);

    return {
      totalIncidents: incidentCount.count,
      totalReports: reportCount.count,
      totalEntities: entityCount.count,
      confirmedDataLeaks: confirmedLeaks.count,
      suspectedDataLeaks: suspectedLeaks.count,
      confirmedCyberAttacks: confirmedAttacks.count,
      suspectedCyberAttacks: suspectedAttacks.count,
      llmIncidents: llmCount.count,
      mostRecentDate: mostRecent?.date || null,
    };
  }

  // Get incident with all related data
  async getIncidentWithDetails(incidentId: number): Promise<{
    incident: IncidentRecord | undefined;
    security: IncidentSecurityRecord | undefined;
    entities: { id: number; incidentId: number; entityId: string; role: string; entityName: string | null }[];
    reports: ReportRecord[];
    classifications: ClassificationRecord[];
  }> {
    const incident = await this.getIncidentByIncidentId(incidentId);
    const security = incident ? await this.getSecurityByIncidentId(incidentId) : undefined;
    const incidentEntitiesList = incident ? await this.getEntitiesForIncident(incidentId) : [];
    const reportsList = incident ? await this.getReportsByIncidentId(incidentId) : [];
    const classificationsList = incident ? await this.getClassificationsByIncidentId(incidentId) : [];

    return {
      incident,
      security,
      entities: incidentEntitiesList,
      reports: reportsList,
      classifications: classificationsList,
    };
  }
}

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IncidentRepository = void 0;
// packages/database/src/repositories/IncidentRepository.ts
const db_connection_1 = require("../db-connection");
const drizzle_orm_1 = require("drizzle-orm");
const incidents_1 = require("../schema/incidents");
const entities_1 = require("../schema/entities");
const incident_security_1 = require("../schema/incident-security");
class IncidentRepository {
    // ============ INCIDENTS ============
    // Insert a new incident
    async insertIncident(incidentData) {
        const [incident] = await db_connection_1.db.insert(incidents_1.incidents).values(incidentData).returning();
        return incident;
    }
    // Insert multiple incidents
    async insertManyIncidents(incidentsData) {
        if (incidentsData.length === 0)
            return [];
        return await db_connection_1.db.insert(incidents_1.incidents).values(incidentsData).returning();
    }
    // Get incident by ID
    async getIncidentById(id) {
        const results = await db_connection_1.db.select().from(incidents_1.incidents).where((0, drizzle_orm_1.eq)(incidents_1.incidents.id, id));
        return results.length ? results[0] : undefined;
    }
    // Get incident by incident_id (the AIID unique identifier)
    async getIncidentByIncidentId(incidentId) {
        const results = await db_connection_1.db.select().from(incidents_1.incidents).where((0, drizzle_orm_1.eq)(incidents_1.incidents.incidentId, incidentId));
        return results.length ? results[0] : undefined;
    }
    // Get all incidents
    async getAllIncidents(limit = 1000) {
        return await db_connection_1.db
            .select()
            .from(incidents_1.incidents)
            .orderBy((0, drizzle_orm_1.desc)(incidents_1.incidents.incidentId))
            .limit(limit);
    }
    // Search incidents by title or description
    async searchIncidents(searchTerm, limit = 100) {
        const searchPattern = `%${searchTerm}%`;
        return await db_connection_1.db
            .select()
            .from(incidents_1.incidents)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.like)(incidents_1.incidents.title, searchPattern), (0, drizzle_orm_1.like)(incidents_1.incidents.description, searchPattern)))
            .orderBy((0, drizzle_orm_1.desc)(incidents_1.incidents.incidentId))
            .limit(limit);
    }
    // Get incident count
    async getIncidentCount() {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incidents_1.incidents);
        return result[0].count;
    }
    // Delete incident
    async deleteIncident(id) {
        await db_connection_1.db.delete(incidents_1.incidents).where((0, drizzle_orm_1.eq)(incidents_1.incidents.id, id));
    }
    // ============ REPORTS ============
    // Insert a report
    async insertReport(reportData) {
        const [report] = await db_connection_1.db.insert(incidents_1.reports).values(reportData).returning();
        return report;
    }
    // Insert multiple reports
    async insertManyReports(reportsData) {
        if (reportsData.length === 0)
            return [];
        return await db_connection_1.db.insert(incidents_1.reports).values(reportsData).returning();
    }
    // Get reports by incident
    async getReportsByIncidentId(incidentId, limit = 10) {
        return await db_connection_1.db
            .select()
            .from(incidents_1.reports)
            .where((0, drizzle_orm_1.eq)(incidents_1.reports.incidentId, incidentId))
            .limit(limit);
    }
    // Get report count
    async getReportCount() {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incidents_1.reports);
        return result[0].count;
    }
    // ============ ENTITIES ============
    // Insert an entity
    async insertEntity(entityData) {
        const [entity] = await db_connection_1.db.insert(entities_1.entities).values(entityData).returning();
        return entity;
    }
    // Insert multiple entities
    async insertManyEntities(entitiesData) {
        if (entitiesData.length === 0)
            return [];
        return await db_connection_1.db.insert(entities_1.entities).values(entitiesData).returning();
    }
    // Get entity by ID
    async getEntityByEntityId(entityId) {
        const results = await db_connection_1.db.select().from(entities_1.entities).where((0, drizzle_orm_1.eq)(entities_1.entities.entityId, entityId));
        return results.length ? results[0] : undefined;
    }
    // Get all entities
    async getAllEntities() {
        return await db_connection_1.db.select().from(entities_1.entities).orderBy((0, drizzle_orm_1.asc)(entities_1.entities.name));
    }
    // Get entity count
    async getEntityCount() {
        const result = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(entities_1.entities);
        return result[0].count;
    }
    // ============ INCIDENT-ENTITY RELATIONSHIPS ============
    // Insert incident-entity relationship
    async insertIncidentEntity(data) {
        const [record] = await db_connection_1.db.insert(entities_1.incidentEntities).values(data).returning();
        return record;
    }
    // Insert multiple relationships
    async insertManyIncidentEntities(data) {
        if (data.length === 0)
            return [];
        return await db_connection_1.db.insert(entities_1.incidentEntities).values(data).returning();
    }
    // Get entities for an incident
    async getEntitiesForIncident(incidentId) {
        const results = await db_connection_1.db
            .select({
            id: entities_1.incidentEntities.id,
            incidentId: entities_1.incidentEntities.incidentId,
            entityId: entities_1.incidentEntities.entityId,
            role: entities_1.incidentEntities.role,
            entityName: entities_1.entities.name,
        })
            .from(entities_1.incidentEntities)
            .leftJoin(entities_1.entities, (0, drizzle_orm_1.eq)(entities_1.incidentEntities.entityId, entities_1.entities.entityId))
            .where((0, drizzle_orm_1.eq)(entities_1.incidentEntities.incidentId, incidentId));
        return results;
    }
    // Get incidents for an entity
    async getIncidentsForEntity(entityId) {
        const incidentIds = await db_connection_1.db
            .select({ incidentId: entities_1.incidentEntities.incidentId })
            .from(entities_1.incidentEntities)
            .where((0, drizzle_orm_1.eq)(entities_1.incidentEntities.entityId, entityId));
        if (incidentIds.length === 0)
            return [];
        return await db_connection_1.db
            .select()
            .from(incidents_1.incidents)
            .where((0, drizzle_orm_1.sql) `${incidents_1.incidents.incidentId} IN (${incidentIds.map(r => r.incidentId).join(',')})`);
    }
    // ============ SECURITY DATA ============
    // Insert security data
    async insertSecurity(securityData) {
        const [record] = await db_connection_1.db.insert(incident_security_1.incidentSecurity).values(securityData).returning();
        return record;
    }
    // Insert multiple security records
    async insertManySecurity(data) {
        if (data.length === 0)
            return [];
        return await db_connection_1.db.insert(incident_security_1.incidentSecurity).values(data).returning();
    }
    // Get security data for incident
    async getSecurityByIncidentId(incidentId) {
        const results = await db_connection_1.db
            .select()
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.incidentId, incidentId));
        return results.length ? results[0] : undefined;
    }
    // Get incidents with data leaks
    async getIncidentsWithDataLeaks() {
        return await db_connection_1.db
            .select()
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.securityDataLeakPresence, 'confirmed'), (0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.securityDataLeakPresence, 'suspected')));
    }
    // Get incidents with cyber attacks
    async getIncidentsWithCyberAttacks() {
        return await db_connection_1.db
            .select()
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.or)((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.cyberAttackFlag, 'confirmed_attack'), (0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.cyberAttackFlag, 'suspected_attack')));
    }
    // Get incidents involving LLMs
    async getLLMIncidents() {
        return await db_connection_1.db
            .select()
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.llmOrChatbotInvolved, true));
    }
    // ============ CLASSIFICATIONS ============
    // Insert classification
    async insertClassification(data) {
        const [record] = await db_connection_1.db.insert(incident_security_1.classifications).values(data).returning();
        return record;
    }
    // Get classifications for incident
    async getClassificationsByIncidentId(incidentId) {
        return await db_connection_1.db
            .select()
            .from(incident_security_1.classifications)
            .where((0, drizzle_orm_1.eq)(incident_security_1.classifications.incidentId, incidentId));
    }
    // ============ STATISTICS ============
    // Get comprehensive stats
    async getStats() {
        const [incidentCount] = await db_connection_1.db.select({ count: (0, drizzle_orm_1.sql) `count(*)` }).from(incidents_1.incidents);
        const [reportCount] = await db_connection_1.db.select({ count: (0, drizzle_orm_1.sql) `count(*)` }).from(incidents_1.reports);
        const [entityCount] = await db_connection_1.db.select({ count: (0, drizzle_orm_1.sql) `count(*)` }).from(entities_1.entities);
        const [confirmedLeaks] = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.securityDataLeakPresence, 'confirmed'));
        const [suspectedLeaks] = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.securityDataLeakPresence, 'suspected'));
        const [confirmedAttacks] = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.cyberAttackFlag, 'confirmed_attack'));
        const [suspectedAttacks] = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.cyberAttackFlag, 'suspected_attack'));
        const [llmCount] = await db_connection_1.db
            .select({ count: (0, drizzle_orm_1.sql) `count(*)` })
            .from(incident_security_1.incidentSecurity)
            .where((0, drizzle_orm_1.eq)(incident_security_1.incidentSecurity.llmOrChatbotInvolved, true));
        const [mostRecent] = await db_connection_1.db
            .select({ date: incidents_1.incidents.date })
            .from(incidents_1.incidents)
            .where((0, drizzle_orm_1.isNotNull)(incidents_1.incidents.date))
            .orderBy((0, drizzle_orm_1.desc)(incidents_1.incidents.date))
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
    async getIncidentWithDetails(incidentId) {
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
exports.IncidentRepository = IncidentRepository;
//# sourceMappingURL=IncidentRepository.js.map
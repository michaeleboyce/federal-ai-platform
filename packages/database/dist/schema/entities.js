"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.incidentEntities = exports.entities = exports.entityRoleEnum = void 0;
// packages/database/src/schema/entities.ts
const pg_core_1 = require("drizzle-orm/pg-core");
// Enum for entity roles in incidents
exports.entityRoleEnum = (0, pg_core_1.pgEnum)("entity_role", ["deployer", "developer", "harmed"]);
// Entities table (organizations, people involved in incidents)
exports.entities = (0, pg_core_1.pgTable)("entities", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    entityId: (0, pg_core_1.text)("entity_id").notNull().unique(), // Normalized slug
    name: (0, pg_core_1.text)("name").notNull(),
});
// Junction table for incident-entity relationships
exports.incidentEntities = (0, pg_core_1.pgTable)("incident_entities", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    incidentId: (0, pg_core_1.integer)("incident_id").notNull(),
    entityId: (0, pg_core_1.text)("entity_id").notNull(),
    role: (0, pg_core_1.text)("role").notNull(), // 'deployer', 'developer', 'harmed'
});
//# sourceMappingURL=entities.js.map
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.reports = exports.incidents = void 0;
// packages/database/src/schema/incidents.ts
const pg_core_1 = require("drizzle-orm/pg-core");
// Main incidents table
exports.incidents = (0, pg_core_1.pgTable)("incidents", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    incidentId: (0, pg_core_1.integer)("incident_id").notNull().unique(),
    title: (0, pg_core_1.text)("title").notNull(),
    description: (0, pg_core_1.text)("description"),
    date: (0, pg_core_1.text)("date"), // ISO date string
    deployers: (0, pg_core_1.jsonb)("deployers").$type(), // Array of deployer names
    developers: (0, pg_core_1.jsonb)("developers").$type(), // Array of developer names
    harmedParties: (0, pg_core_1.jsonb)("harmed_parties").$type(), // Array of harmed party names
    reportCount: (0, pg_core_1.integer)("report_count").default(0),
    createdAt: (0, pg_core_1.timestamp)("created_at", { withTimezone: true }).notNull().defaultNow(),
});
// Reports table
exports.reports = (0, pg_core_1.pgTable)("reports", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    reportNumber: (0, pg_core_1.integer)("report_number").notNull().unique(),
    incidentId: (0, pg_core_1.integer)("incident_id"),
    title: (0, pg_core_1.text)("title"),
    text: (0, pg_core_1.text)("text"),
    url: (0, pg_core_1.text)("url"),
    sourceDomain: (0, pg_core_1.text)("source_domain"),
    authors: (0, pg_core_1.jsonb)("authors").$type(), // Array of author names
    datePublished: (0, pg_core_1.text)("date_published"),
    dateDownloaded: (0, pg_core_1.text)("date_downloaded"),
    dateModified: (0, pg_core_1.text)("date_modified"),
    dateSubmitted: (0, pg_core_1.text)("date_submitted"),
    language: (0, pg_core_1.text)("language"),
    imageUrl: (0, pg_core_1.text)("image_url"),
    tags: (0, pg_core_1.jsonb)("tags").$type(),
});
//# sourceMappingURL=incidents.js.map
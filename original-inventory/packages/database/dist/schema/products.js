"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.products = exports.productStatusEnum = exports.serviceModelEnum = void 0;
// packages/database/src/schema/products.ts
const pg_core_1 = require("drizzle-orm/pg-core");
// Enums for products
exports.serviceModelEnum = (0, pg_core_1.pgEnum)("service_model", ["SaaS", "PaaS", "IaaS", "Other"]);
exports.productStatusEnum = (0, pg_core_1.pgEnum)("product_status", [
    "FedRAMP Authorized",
    "FedRAMP Ready",
    "In Process",
    "FedRAMP Connect",
    "Compliant"
]);
exports.products = (0, pg_core_1.pgTable)("products", {
    id: (0, pg_core_1.serial)("id").primaryKey(),
    fedrampId: (0, pg_core_1.text)("fedramp_id").notNull().unique(),
    cloudServiceProvider: (0, pg_core_1.text)("cloud_service_provider"),
    cloudServiceOffering: (0, pg_core_1.text)("cloud_service_offering"),
    serviceDescription: (0, pg_core_1.text)("service_description"),
    businessCategories: (0, pg_core_1.text)("business_categories"),
    serviceModel: (0, pg_core_1.text)("service_model"),
    status: (0, pg_core_1.text)("status"),
    independentAssessor: (0, pg_core_1.text)("independent_assessor"),
    authorizations: (0, pg_core_1.text)("authorizations"),
    reuse: (0, pg_core_1.text)("reuse"),
    parentAgency: (0, pg_core_1.text)("parent_agency"),
    subAgency: (0, pg_core_1.text)("sub_agency"),
    atoIssuanceDate: (0, pg_core_1.text)("ato_issuance_date"),
    fedrampAuthorizationDate: (0, pg_core_1.text)("fedramp_authorization_date"),
    annualAssessmentDate: (0, pg_core_1.text)("annual_assessment_date"),
    atoExpirationDate: (0, pg_core_1.text)("ato_expiration_date"),
    htmlScraped: (0, pg_core_1.boolean)("html_scraped").notNull().default(false),
    htmlPath: (0, pg_core_1.text)("html_path"),
    createdAt: (0, pg_core_1.timestamp)("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: (0, pg_core_1.timestamp)("updated_at", { withTimezone: true }).notNull().defaultNow(),
});
//# sourceMappingURL=products.js.map
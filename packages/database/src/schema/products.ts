// packages/database/src/schema/products.ts
import { serial, text, boolean, timestamp, pgTable, pgEnum } from "drizzle-orm/pg-core";

// Enums for products
export const serviceModelEnum = pgEnum("service_model", ["SaaS", "PaaS", "IaaS", "Other"]);
export const productStatusEnum = pgEnum("product_status", [
  "FedRAMP Authorized",
  "FedRAMP Ready",
  "In Process",
  "FedRAMP Connect",
  "Compliant"
]);

export const products = pgTable("products", {
  id: serial("id").primaryKey(),
  fedrampId: text("fedramp_id").notNull().unique(),
  cloudServiceProvider: text("cloud_service_provider"),
  cloudServiceOffering: text("cloud_service_offering"),
  serviceDescription: text("service_description"),
  businessCategories: text("business_categories"),
  serviceModel: text("service_model"),
  status: text("status"),
  independentAssessor: text("independent_assessor"),
  authorizations: text("authorizations"),
  reuse: text("reuse"),
  parentAgency: text("parent_agency"),
  subAgency: text("sub_agency"),
  atoIssuanceDate: text("ato_issuance_date"),
  fedrampAuthorizationDate: text("fedramp_authorization_date"),
  annualAssessmentDate: text("annual_assessment_date"),
  atoExpirationDate: text("ato_expiration_date"),
  htmlScraped: boolean("html_scraped").notNull().default(false),
  htmlPath: text("html_path"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export type ProductRecord = typeof products.$inferSelect;
export type NewProductRecord = typeof products.$inferInsert;

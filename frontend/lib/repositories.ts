// Frontend repository exports
// Import repositories from the database package
import { ProductRepository, AIServiceRepository, AgencyRepository, UseCaseRepository } from '@federal-ai-platform/database/repositories';

// Export singletons for use in API routes and server components
export const productRepo = new ProductRepository();
export const aiServiceRepo = new AIServiceRepository();
export const agencyRepo = new AgencyRepository();
export const useCaseRepo = new UseCaseRepository();

// Re-export repository classes for custom instantiation if needed
export { ProductRepository, AIServiceRepository, AgencyRepository, UseCaseRepository };

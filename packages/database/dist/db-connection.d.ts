import * as schema from "./schema";
export declare const db: import("drizzle-orm/neon-http").NeonHttpDatabase<typeof schema> & {
    $client: import("@neondatabase/serverless").NeonQueryFunction<false, false>;
};
//# sourceMappingURL=db-connection.d.ts.map
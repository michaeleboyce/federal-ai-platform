import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // better-sqlite3 is a native addon and must not be bundled into the RSC graph.
  serverExternalPackages: ["better-sqlite3"],
};

export default nextConfig;

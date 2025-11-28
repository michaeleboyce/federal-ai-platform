import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Experimental features to improve React 19 compatibility
  experimental: {
    // Using PPR can help with static generation issues
  },
  // Skip static generation for error pages that cause issues
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;

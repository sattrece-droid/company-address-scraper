import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // API proxy configuration
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*",
        },
      ],
    };
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_ADSENSE_ID: process.env.NEXT_PUBLIC_ADSENSE_ID || "",
  },

  // Image optimization
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

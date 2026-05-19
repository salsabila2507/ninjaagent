import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  env: {
    // Environment variables will be loaded from .env file
  },
};

export default nextConfig;
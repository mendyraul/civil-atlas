import path from 'node:path';
import type { NextConfig } from 'next';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
if (process.env.VERCEL === '1' && process.env.NEXT_PUBLIC_DEMO_MODE !== 'true' && !apiBaseUrl) {
  throw new Error(
    'NEXT_PUBLIC_API_BASE_URL must be configured in Vercel when NEXT_PUBLIC_DEMO_MODE=false.',
  );
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ['127.0.0.1'],
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;

import type { NextConfig } from "next";
import { withSentryConfig } from '@sentry/nextjs';

const nextConfig: NextConfig = {
  eslint: {
    // Allow production builds to complete even if there are ESLint errors
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow production builds to complete even if there are TypeScript errors
    // Only use during development - fix errors before production deployment
    ignoreBuildErrors: true,
  },
  // Enable instrumentation for Sentry
  experimental: {
    instrumentationHook: true,
  },
};

// Wrap the config with Sentry for error monitoring
export default withSentryConfig(nextConfig, {
  // Sentry build-time configuration
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // Only upload source maps in production
  silent: process.env.NODE_ENV !== 'production',

  // Upload source maps during build
  widenClientFileUpload: true,

  // Automatically annotate React components for better error messages
  reactComponentAnnotation: {
    enabled: true,
  },

  // Hide Sentry build output unless there's an error
  hideSourceMaps: true,

  // Disable Sentry CLI telemetry
  telemetry: false,
});

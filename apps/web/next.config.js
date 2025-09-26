/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    transpilePackages: ['@lynx/shared'],
  },
  webpack: (config) => {
    // Handle Three.js and other WebGL libraries
    config.externals = [...(config.externals || []), { canvas: 'canvas' }];
    return config;
  },
  images: {
    domains: ['upload.wikimedia.org', 'arxiv.org'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

module.exports = nextConfig;

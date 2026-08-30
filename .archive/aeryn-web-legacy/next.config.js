/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  poweredByHeader: false,
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/:path+',
          destination: '/',
        },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
};

module.exports = nextConfig;

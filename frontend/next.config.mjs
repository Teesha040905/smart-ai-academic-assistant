/** @type {import('next').NextConfig} */

// Where the Next.js server proxies /api/v1/* when the browser calls a relative API URL.
// Local dev / ngrok: the backend on this machine. Docker compose: http://api:8000.
// On Vercel, set NEXT_PUBLIC_API_URL to the Render backend URL instead (browser calls it directly).
const backendUrl = (process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

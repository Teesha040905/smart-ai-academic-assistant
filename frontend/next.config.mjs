/** @type {import('next').NextConfig} */

// Where the Next.js server proxies /api/v1/* when the browser calls a relative API URL.
// Local dev / ngrok: the backend on this machine. Docker compose: http://api:8000.
// On Vercel, set NEXT_PUBLIC_API_URL to the Render backend URL instead (browser calls it directly).
const backendUrl = (process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const isDev = process.env.NODE_ENV !== "production";

// Origin of the API the browser talks to (absolute NEXT_PUBLIC_API_URL), for the CSP below.
function apiOrigin() {
  try {
    const url = new URL(process.env.NEXT_PUBLIC_API_URL || "");
    return url.protocol === "https:" || url.protocol === "http:" ? url.origin : "";
  } catch {
    return ""; // relative URL ("/api/v1") -> same origin, covered by 'self'
  }
}

const csp = [
  "default-src 'self'",
  // Next.js injects small inline bootstrap scripts; dev mode also needs eval for hot reload
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  `connect-src 'self' ${apiOrigin()} https://api.emailjs.com${isDev ? " ws: http://localhost:8000 http://127.0.0.1:8000" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
]
  .join("; ")
  .replace(/\s+/g, " ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
];

const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
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

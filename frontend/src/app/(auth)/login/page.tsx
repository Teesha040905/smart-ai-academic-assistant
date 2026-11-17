"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Caveat } from "next/font/google";
import { useAuth } from "@/lib/auth";
import { LoginBroIllustration } from "@/components/landing/LoginBroIllustration";

const caveat = Caveat({
  subsets: ["latin"],
  weight: ["600", "700"],
  display: "swap",
});

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("demo@student.edu");
  const [password, setPassword] = useState("DemoPass123!");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full w-full grid lg:grid-cols-2 overflow-hidden bg-[#043634]">
      {/* Left Column: Dark Hero Showcase */}
      <div className="relative hidden lg:flex flex-col justify-between items-center text-center overflow-hidden bg-[#043634] p-8 xl:p-12 text-white">
        {/* Glow Effects */}
        <div className="pointer-events-none absolute -right-20 top-10 h-[400px] w-[400px] rounded-full bg-teal-400/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-10 h-[300px] w-[300px] rounded-full bg-emerald-500/10 blur-3xl" />

        {/* Top Logo */}
        <div className="relative z-10 shrink-0">
          <Link href="/" className="inline-flex items-center justify-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full border border-teal-300/30 bg-teal-400/15 text-teal-200 shadow-inner">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3z" />
                <path d="M5 13.18V17c0 1.66 3.13 3 7 3s7-1.34 7-3v-3.82" opacity=".7" />
              </svg>
            </span>
            <span className="font-serif text-xl font-bold tracking-tight xl:text-2xl text-white">
              Smart Academic
            </span>
          </Link>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 my-auto flex flex-col items-center justify-center text-center py-4">
          <p className="flex items-center justify-center gap-3 text-xs font-semibold uppercase tracking-[0.22em] text-[#d4a574]">
            <span className="inline-block h-px w-6 bg-[#d4a574]" />
            Your AI Academic Companion
            <span className="inline-block h-px w-6 bg-[#d4a574]" />
          </p>

          <h1 className="mt-3 font-serif text-2xl lg:text-3xl xl:text-4xl font-bold leading-tight tracking-tight text-white text-center">
            Unlock Your Full Academic{" "}
            <span className={`${caveat.className} relative inline-block text-[1.18em] font-bold text-[#5eead4]`}>
              Potential.
              <svg
                className="absolute -bottom-1.5 left-0 w-full"
                viewBox="0 0 80 8"
                fill="none"
                aria-hidden
              >
                <path
                  d="M2 5c18-3 35 2 50-1 8-1.5 18-1 26 1"
                  stroke="#5eead4"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            </span>
          </h1>

          <p className="mt-3 max-w-md text-sm xl:text-base leading-relaxed text-white/80 text-center mx-auto">
            Personalized study plans, AI notes tutoring, weak topic analysis, and exam readiness tracking.
          </p>

          {/* Login-bro SVG Graphic */}
          <div className="mt-5 w-full max-w-[400px] xl:max-w-[440px] mx-auto origin-center flex items-center justify-center">
            <LoginBroIllustration />
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 shrink-0 text-xs text-white/50 font-medium text-center">
          © {new Date().getFullYear()} Smart Academic Inc. All rights reserved.
        </div>
      </div>

      {/* Right Column: Light Sign-in Form */}
      <div className="relative flex h-full w-full items-center justify-center overflow-hidden bg-[#f8fafc] p-4 sm:p-6 lg:p-8">
        {/* Subtle Decorative Background Circles */}
        <div className="pointer-events-none absolute right-0 top-0 h-48 w-48 text-teal-900/5">
          <svg viewBox="0 0 200 200" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="200" cy="0" r="160" />
            <circle cx="200" cy="0" r="120" />
            <circle cx="200" cy="0" r="80" />
          </svg>
        </div>
        <div className="pointer-events-none absolute bottom-0 right-0 h-64 w-64 text-teal-900/5">
          <svg viewBox="0 0 200 200" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="200" cy="200" r="180" />
            <circle cx="200" cy="200" r="130" />
            <circle cx="200" cy="200" r="80" />
          </svg>
        </div>

        {/* Floating Card */}
        <div className="relative z-10 w-full max-w-[420px] rounded-3xl border border-slate-100 bg-white p-6 sm:p-9 shadow-xl shadow-slate-900/5">
          <div className="mb-6">
            <h2 className="font-serif text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Hello!</h2>
            <p className="mt-1 text-sm text-slate-500">Sign in to continue to Smart Academic</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="relative">
              <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path d="M3 7l9 6 9-6" />
                </svg>
              </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email Address"
                required
                className="w-full rounded-full border border-slate-200 bg-slate-50/50 py-3 pl-11 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-teal-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
            </div>

            {/* Password Field with Eye Toggle */}
            <div className="relative">
              <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <rect x="5" y="11" width="14" height="10" rx="2" />
                  <path d="M8 11V7a4 4 0 018 0v4" />
                </svg>
              </span>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="w-full rounded-full border border-slate-200 bg-slate-50/50 py-3 pl-11 pr-16 text-sm text-slate-900 placeholder:text-slate-400 focus:border-teal-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 z-30 flex items-center justify-center rounded-full bg-slate-100 px-2 py-1 text-slate-600 hover:bg-slate-200 hover:text-slate-900 focus:outline-none transition-colors border border-slate-200/80 shadow-xs"
                title={showPassword ? "Hide password" : "Show password"}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg className="h-4 w-4 text-teal-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" strokeWidth="2.2" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>

            {/* Options Row */}
            <div className="flex items-center justify-between text-xs pt-0.5">
              <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span>Remember me</span>
              </label>
              <Link href="#" className="font-semibold text-teal-600 hover:text-teal-700">
                Forgot Password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-teal-600 to-emerald-500 py-3.5 text-sm font-semibold text-white shadow-md shadow-teal-600/20 transition hover:from-teal-700 hover:to-emerald-600 disabled:opacity-50"
            >
              {loading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Login</span>
                  <span className="text-base">→</span>
                </>
              )}
            </button>

            {/* Error banner */}
            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-600">
                {error}
              </div>
            )}
          </form>

          {/* Sign Up Link */}
          <div className="mt-8 text-center text-xs sm:text-sm text-slate-600">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-semibold text-teal-600 hover:text-teal-700">
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

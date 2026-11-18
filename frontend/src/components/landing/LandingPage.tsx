"use client";

import Link from "next/link";
import Image from "next/image";
import { caveat } from "@/lib/fonts";
import { useAuth } from "@/lib/auth";
import { DashboardMockup } from "./DashboardMockup";

const NAV = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#about", label: "About" },
];

const FEATURES = [
  {
    title: "AI Tutor",
    body: "Ask questions and get personalized answers from your uploaded materials.",
    href: "/tutor",
    icon: "tutor",
  },
  {
    title: "Personalized Planner",
    body: "Get study plans based on your exams, topics, and goals.",
    href: "/planner",
    icon: "planner",
  },
  {
    title: "Smart Quizzes",
    body: "Practice with topic-wise quizzes and track your progress in real time.",
    href: "/quizzes",
    icon: "quiz",
  },
  {
    title: "Performance Insights",
    body: "See your strengths, weaknesses, and get smart recommendations.",
    href: "/performance",
    icon: "perf",
  },
];

function FeatureIcon({ name }: { name: string }) {
  const common = "h-6 w-6";
  if (name === "tutor") {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="5" y="8" width="14" height="10" rx="3" />
        <circle cx="9" cy="13" r="1" fill="currentColor" />
        <circle cx="15" cy="13" r="1" fill="currentColor" />
        <path d="M9 3v3M15 3v3M12 18v3" />
      </svg>
    );
  }
  if (name === "planner") {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M3 10h18M8 3v4M16 3v4" />
      </svg>
    );
  }
  if (name === "quiz") {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M8 6h11M8 12h11M8 18h8" />
        <path d="M4 6.5l1 1 2-2M4 12.5l1 1 2-2" />
      </svg>
    );
  }
  return (
    <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
    </svg>
  );
}

export function LandingPage() {
  const { user, loading } = useAuth();
  const signedIn = !loading && !!user;
  const primaryHref = signedIn ? "/dashboard" : "/login";
  const primaryLabel = signedIn ? "Open dashboard →" : "Start studying →";

  return (
    <div className="landing-v2 min-h-screen overflow-x-hidden text-slate-900">
      {/* Nav */}
      <header className="landing-v2-nav absolute inset-x-0 top-0 z-30">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <Image src="/logo.jpg" alt="Smart Academic Assistant Logo" width={36} height={36} className="rounded-lg object-contain" />
            <span className="font-serif text-lg font-semibold tracking-tight sm:text-xl">
              Smart Academic
            </span>
          </Link>

          <nav className="hidden items-center gap-7 text-sm text-slate-700 md:flex">
            {NAV.map((item) => (
              <a key={item.href} href={item.href} className="transition hover:text-slate-900">
                {item.label}
              </a>
            ))}
          </nav>

          <Link
            href={signedIn ? "/dashboard" : "/login"}
            className="inline-flex items-center rounded-full bg-[#0f766e] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#115e59]"
          >
            {signedIn ? "Dashboard →" : "Get Started →"}
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden px-5 pb-16 pt-28 sm:px-8 sm:pb-24 sm:pt-32">
        <div className="landing-v2-glow pointer-events-none absolute -right-20 top-10 h-[420px] w-[420px] rounded-full bg-teal-400/15 blur-3xl" />
        <div className="landing-v2-glow-delay pointer-events-none absolute bottom-0 left-10 h-[280px] w-[280px] rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.05fr_1fr] lg:gap-8">
          <div className="landing-fade-up max-w-xl">
            <p className="flex items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#d4a574]">
              <span className="inline-block h-px w-7 bg-[#d4a574]" />
              Your AI study companion
            </p>

            <h1 className="mt-5 font-serif text-[2.35rem] font-semibold leading-[1.12] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.35rem]">
              Study smarter.
              <br />
              Learn with{" "}
              <span className={`${caveat.className} relative inline-block text-[1.15em] font-bold text-[#0f766e]`}>
                your
                <svg
                  className="absolute -bottom-1 left-0 w-full"
                  viewBox="0 0 80 8"
                  fill="none"
                  aria-hidden
                >
                  <path
                    d="M2 5c18-3 35 2 50-1 8-1.5 18-1 26 1"
                    stroke="#d4a574"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </span>{" "}
              own AI.
            </h1>

            <p className="mt-5 max-w-md text-base leading-relaxed text-slate-700 sm:text-lg">
              Your personal AI study companion for subjects, exams, and weak topics.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href={primaryHref}
                className="inline-flex items-center rounded-full bg-[#0f766e] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#115e59]"
              >
                {primaryLabel}
              </Link>
              <a
                href="#features"
                className="inline-flex items-center rounded-full border border-[#0f766e] px-6 py-3 text-sm font-semibold text-[#0f766e] transition hover:bg-[#0f766e]/10"
              >
                Explore features
              </a>
            </div>
          </div>

          <div className="landing-fade-up relative mx-auto w-full max-w-xl lg:max-w-none" style={{ animationDelay: "0.15s" }}>
            <DashboardMockup />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative px-5 py-20 sm:px-8 sm:py-24">
        <div className="mx-auto max-w-6xl text-center">
          <p className="flex items-center justify-center gap-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#d4a574]">
            <span className="inline-block h-px w-7 bg-[#d4a574]" />
            Powerful features
          </p>
          <h2 className="mt-4 font-serif text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl">
            Everything you need to study
            <br className="hidden sm:block" /> with confidence
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-600 sm:text-base">
            From AI-powered learning to personalized study plans, Smart Academic brings all your
            study tools together in one place.
          </p>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-5">
            {FEATURES.map((feature, i) => (
              <article
                key={feature.title}
                className="landing-feature-card group flex flex-col rounded-2xl border border-transparent bg-[#0f766e] p-6 text-left shadow-lg hover:-translate-y-1"
                style={{ animationDelay: `${0.08 * i}s` }}
              >
                <span className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-full bg-white/20 text-white shadow-sm">
                  <FeatureIcon name={feature.icon} />
                </span>
                <h3 className="font-serif text-xl font-semibold text-white">{feature.title}</h3>
                <p className="mt-3 flex-1 text-sm leading-relaxed text-teal-50">{feature.body}</p>
                <Link
                  href={signedIn ? feature.href : "/login"}
                  className="mt-6 inline-flex text-sm font-semibold text-teal-200 transition group-hover:text-white"
                >
                  Learn more →
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="px-5 py-16 sm:px-8 sm:py-20">
        <div className="mx-auto max-w-6xl">
          <p className="flex items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#d4a574]">
            <span className="inline-block h-px w-7 bg-[#d4a574]" />
            How it works
          </p>
          <h2 className="mt-3 font-serif text-3xl font-semibold sm:text-4xl">
            A continuous learning loop
          </h2>
          <ol className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Upload & ask", "Ground answers in your own notes and PDFs."],
              ["Practice", "Generate quizzes and flashcards from weak topics."],
              ["Track", "See progress, streaks, and exam readiness."],
              ["Adapt", "Plans and recommendations update with you."],
            ].map(([title, body], i) => (
              <li key={title} className="border-t border-[#d4a574]/35 pt-4">
                <span className="text-xs font-semibold text-[#d4a574]">0{i + 1}</span>
                <h3 className="mt-2 font-serif text-xl font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-600">{body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* About */}
      <section id="about" className="px-5 py-20 sm:px-8 sm:py-24 bg-white shadow-sm border-t border-slate-200 mt-10">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center mb-16">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#d4a574]">Our Philosophy</p>
            <h2 className="mt-3 font-serif text-3xl font-semibold sm:text-4xl">Built for real academic workflows</h2>
            <p className="mt-4 text-sm leading-relaxed text-slate-700 sm:text-base">
              Smart Academic connects your subjects, materials, quizzes, and exam dates into one
              intelligent assistant. We believe in studying smarter, not harder.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* Box 1 */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 hover:bg-slate-50 transition-colors">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/20 text-teal-700">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              </div>
              <h3 className="font-serif text-xl font-semibold mb-2">Science-Backed Learning</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                We leverage proven cognitive science techniques like Active Recall and Spaced Repetition to help you learn 2x faster and retain knowledge longer than passive reading.
              </p>
            </div>

            {/* Box 2 */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 hover:bg-slate-50 transition-colors">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-700">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              </div>
              <h3 className="font-serif text-xl font-semibold mb-2">Who is this for?</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Whether you are a university student juggling multiple courses, a self-taught programmer, or a high schooler prepping for exams, this platform adapts to your academic goals.
              </p>
            </div>

            {/* Box 3 */}
            <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 hover:bg-slate-50 transition-colors sm:col-span-2 lg:col-span-1">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/20 text-amber-700">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <h3 className="font-serif text-xl font-semibold mb-2">Data Privacy First</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Your study materials, notes, and academic data are strictly yours. We process your documents securely to generate AI insights, keeping your personal intellectual property safe.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer mark */}
      <footer className="px-5 pb-14 pt-10 text-center sm:px-8">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="relative flex w-full items-center justify-center">
            <span className="absolute inset-x-0 top-1/2 h-px bg-[#d4a574]/50" />
            <span className="relative z-10 bg-[#043634] px-4 text-[#d4a574]">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M4 5c3 0 5.5 1 8 3 2.5-2 5-3 8-3v12c-3 0-5.5 1-8 3-2.5-2-5-3-8-3V5z" />
              </svg>
            </span>
          </div>
          <p className="mt-5 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
            Learn · Practice · Improve
          </p>
        </div>
      </footer>
    </div>
  );
}

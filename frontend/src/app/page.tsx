"use client";

import { useAuth } from "@/lib/auth";
import { LandingPage } from "@/components/landing/LandingPage";
import { LoadingState } from "@/components/ui/StateViews";

export default function HomePage() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white text-slate-900">
        <LoadingState label="Loading…" />
      </div>
    );
  }

  return <LandingPage />;
}

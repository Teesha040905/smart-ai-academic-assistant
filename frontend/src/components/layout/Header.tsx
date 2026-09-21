"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

export function Header({ title }: { title?: string }) {
  const { user, logout } = useAuth();
  const { toggle, resolved } = useTheme();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-slate-200/80 bg-background/90 px-4 backdrop-blur dark:border-slate-800 lg:px-6">
      <div className="min-w-0">
        {title ? (
          <h1 className="truncate font-serif text-lg font-semibold text-slate-900 dark:text-slate-50">
            {title}
          </h1>
        ) : (
          <p className="truncate text-sm text-muted">
            Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Link
          href="/search"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Search"
        >
          <Icon name="search" />
        </Link>
        <button
          type="button"
          onClick={toggle}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          aria-label="Toggle theme"
        >
          <Icon name={resolved === "dark" ? "sun" : "moon"} />
        </button>
        <Button variant="ghost" size="sm" onClick={() => logout()}>
          <Icon name="logout" className="h-4 w-4" />
          <span className="hidden sm:inline">Sign out</span>
        </Button>
      </div>
    </header>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { mainNav } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { Icon } from "@/components/ui/Icon";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden h-full w-64 shrink-0 flex-col border-r border-slate-200/80 bg-sidebar dark:border-slate-800 lg:flex">
      <div className="border-b border-slate-200/80 px-5 py-5 dark:border-slate-800">
        <Link href="/dashboard" className="block">
          <p className="font-serif text-xl font-semibold text-slate-900 dark:text-slate-50">
            Smart Academic
          </p>
          <p className="text-xs text-muted">AI study assistant</p>
        </Link>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
        {mainNav.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-teal-50 text-teal-900 dark:bg-teal-950/60 dark:text-teal-100"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/80"
              )}
            >
              <Icon name={item.icon} className={active ? "text-teal-700 dark:text-teal-300" : ""} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

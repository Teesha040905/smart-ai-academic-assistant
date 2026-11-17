"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { mainNav } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { Icon } from "@/components/ui/Icon";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={cn("hidden h-full shrink-0 flex-col border-r border-slate-200/80 bg-sidebar dark:border-slate-800 lg:flex transition-all duration-300 relative", collapsed ? "w-20" : "w-64")}>
      
      <div className={cn("border-b border-slate-200/80 py-3 dark:border-slate-800 flex items-center h-[73px]", collapsed ? "justify-center flex-col gap-1 px-0" : "px-3 justify-between")}>
        <Link href="/dashboard" className={cn("flex items-center gap-2", collapsed && "justify-center")}>
          <Image src="/logo.jpg" alt="Logo" width={collapsed ? 28 : 36} height={collapsed ? 28 : 36} className="rounded-lg object-contain transition-all" />
          {!collapsed && (
            <div className="whitespace-nowrap overflow-hidden">
              <p className="font-serif text-base font-semibold leading-tight text-slate-900 dark:text-slate-50">Smart Academic</p>
              <p className="text-xs text-muted">AI study assistant</p>
            </div>
          )}
        </Link>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "flex items-center justify-center rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:text-slate-400 dark:hover:text-slate-100 transition-colors",
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <Icon name="sidebar" className="h-5 w-5" />
        </button>
      </div>
      
      <nav className="flex-1 space-y-0.5 overflow-y-auto p-3 overflow-x-hidden">
        {mainNav.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center rounded-lg py-2 text-sm font-medium transition-colors whitespace-nowrap",
                collapsed ? "justify-center px-0" : "gap-3 px-3",
                active
                  ? "bg-[#043634] text-white shadow-md dark:bg-[#5eead4] dark:text-[#043634]"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/80"
              )}
            >
              <Icon name={item.icon} className={active ? "text-teal-400 dark:text-[#043634]" : ""} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      
      <div className="border-t border-slate-200/80 p-3 dark:border-slate-800 shrink-0 space-y-1 overflow-x-hidden">
        <Link
          href="/settings"
          title={collapsed ? "Settings" : undefined}
          className={cn(
            "flex items-center rounded-lg py-2 text-sm font-medium transition-colors whitespace-nowrap",
            collapsed ? "justify-center px-0" : "gap-3 px-3",
            pathname.startsWith("/settings")
              ? "bg-[#043634] text-white shadow-md dark:bg-[#5eead4] dark:text-[#043634]"
              : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/80"
          )}
        >
          <Icon name="gear" className={pathname.startsWith("/settings") ? "text-teal-400 dark:text-[#043634]" : ""} />
          {!collapsed && <span>Settings</span>}
        </Link>
      </div>
    </aside>
  );
}

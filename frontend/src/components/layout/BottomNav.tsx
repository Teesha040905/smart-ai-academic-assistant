"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { mobileNav } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { Icon } from "@/components/ui/Icon";

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200/80 bg-background/95 backdrop-blur lg:hidden dark:border-slate-800">
      <div className="mx-auto grid max-w-lg grid-cols-5 gap-1 px-2 py-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        {mobileNav.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 rounded-lg px-1 py-1.5 text-[10px] font-medium",
                active ? "text-teal-700 dark:text-teal-300" : "text-muted"
              )}
            >
              <Icon name={item.icon} className="h-5 w-5" />
              <span>{item.shortLabel || item.label.split(" ")[0]}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

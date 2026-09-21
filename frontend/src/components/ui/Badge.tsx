import { cn } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "teal" | "amber" | "red" | "green";
  className?: string;
}) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
    teal: "bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200",
    amber: "bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-100",
    red: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-200",
    green: "bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

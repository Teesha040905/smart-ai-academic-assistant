import { cn } from "@/lib/utils";

const paths: Record<string, string> = {
  grid: "M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z",
  book: "M4 5a2 2 0 012-2h11v16H6a2 2 0 00-2 2V5zm2 0v14h9V5H6z",
  folder: "M4 6h6l2 2h8v10a2 2 0 01-2 2H4V6z",
  chat: "M4 5h16v10H8l-4 4V5z",
  calendar: "M7 3v2H5v16h14V5h-2V3H7zm2 4h6v2H9V7z",
  check: "M5 5h14v14H5V5zm3 3l2 2 4-4 2 2-6 6-4-4 2-2z",
  cards: "M5 5h10v8H5V5zm2 10h10v4H7v-4z",
  chart: "M5 19V9h3v10H5zm5 0V5h3v14h-3zm5 0v-7h3v7h-3z",
  map: "M12 2l8 4v14l-8-4-8 4V6l8-4zm0 4.2L8 8.5v10.3l4-2v-10.6zm2 0v10.6l4 2V8.5l-4-2.3z",
  spark: "M12 2l2 6h6l-5 4 2 6-5-4-5 4 2-6-5-4h6l2-6z",
  bell: "M12 3a5 5 0 00-5 5v3l-2 2v1h14v-1l-2-2V8a5 5 0 00-5-5zm-2 16a2 2 0 004 0",
  search: "M10 4a6 6 0 104.47 10.03l3.5 3.5 1.4-1.4-3.5-3.5A6 6 0 0010 4zm0 2a4 4 0 110 8 4 4 0 010-8z",
  user: "M12 12a5 5 0 100-10 5 5 0 000 10zm-7 9a7 7 0 0114 0H5z",
  gear: "M12 8a4 4 0 110 8 4 4 0 010-8zm8.5 4l1.5 1-1.2 2.6 1.7 1-1 1.7-2.6-1.2-1 1.5-1.7-1-1.2 2.6-1.7-1-1-1.7 2.6-1.2 1-1.5-1.7-1 1.2-2.6-1.7-1 1-1.7 2.6 1.2 1-1.5z",
  menu: "M4 7h16v2H4V7zm0 5h16v2H4v-2zm0 5h16v2H4v-2z",
  sun: "M12 4V2m0 20v-2M4 12H2m20 0h-2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5M12 8a4 4 0 100 8 4 4 0 000-8z",
  moon: "M21 14.5A8.5 8.5 0 1112.5 3a6.5 6.5 0 009.5 11.5z",
  logout: "M10 4H5v16h5M14 12H8m6 0l-3-3m3 3l-3 3",
  "arrow-up": "M12 19V5M5 12l7-7 7 7",
  "chevron-left": "M15 18l-6-6 6-6",
  "chevron-right": "M9 18l6-6-6-6",
  "sidebar": "M5 3a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2H5zm4 0v18",
  download: "M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2",
  trash: "M4 7h16M10 11v6m4-6v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3",
  document: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
};

export function Icon({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const d = paths[name] ?? paths.grid;
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("h-5 w-5 shrink-0", className)}
      aria-hidden
    >
      <path d={d} />
    </svg>
  );
}

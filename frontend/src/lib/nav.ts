export interface NavItem {
  href: string;
  label: string;
  shortLabel?: string;
  icon: string;
  mobile?: boolean;
}

export const mainNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: "grid", mobile: true },
  { href: "/subjects", label: "Subjects", icon: "book", mobile: true },
  { href: "/materials", label: "Materials", icon: "folder" },
  { href: "/tutor", label: "AI Tutor", icon: "chat", mobile: true },
  { href: "/planner", label: "Planner", icon: "calendar", mobile: true },
  { href: "/quizzes", label: "Quizzes", icon: "check" },
  { href: "/flashcards", label: "Flashcards", icon: "cards" },
  { href: "/performance", label: "Performance", icon: "chart" },
  { href: "/knowledge-map", label: "Knowledge Map", icon: "map" },
  { href: "/recommendations", label: "Recommendations", icon: "spark" },
  { href: "/notifications", label: "Notifications", icon: "bell" },
  { href: "/search", label: "Search", icon: "search", mobile: true },
  { href: "/profile", label: "Profile", icon: "user" },
  { href: "/settings", label: "Settings", icon: "gear" },
];

export const mobileNav = mainNav.filter((item) => item.mobile);

import localFont from "next/font/local";

// Fonts are bundled with the app (Latin subset, SIL Open Font License) instead of being
// downloaded from Google Fonts during every build, which made builds fail intermittently.

export const dmSans = localFont({
  src: [
    { path: "../fonts/dm-sans-latin.woff2", weight: "100 1000", style: "normal" },
    { path: "../fonts/dm-sans-latin-italic.woff2", weight: "100 1000", style: "italic" },
  ],
  variable: "--font-sans",
  display: "swap",
});

export const sourceSerif = localFont({
  src: [
    { path: "../fonts/source-serif-4-latin.woff2", weight: "200 900", style: "normal" },
    { path: "../fonts/source-serif-4-latin-italic.woff2", weight: "200 900", style: "italic" },
  ],
  variable: "--font-serif",
  display: "swap",
});

export const caveat = localFont({
  src: [{ path: "../fonts/caveat-latin.woff2", weight: "400 700", style: "normal" }],
  display: "swap",
});

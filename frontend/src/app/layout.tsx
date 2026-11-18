import type { Metadata, Viewport } from "next";
import { dmSans, sourceSerif } from "@/lib/fonts";
import { Providers } from "@/components/providers";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#043634",
};

export const metadata: Metadata = {
  title: "Smart Academic — AI Academic Assistant",
  description:
    "Personalized AI study companion for subjects, exams, quizzes, and adaptive plans grounded in your materials.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${dmSans.variable} ${sourceSerif.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

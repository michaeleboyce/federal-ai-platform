import type { Metadata } from "next";
import { Instrument_Serif, Fraunces, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { SiteFooter } from "@/components/footer";
import { CommandPalette } from "@/components/command-palette";
import { Dateline } from "@/components/dateline";
import { getCommandPaletteIndex, getLastUpdatedDate } from "@/lib/db";

/* Editorial display serif — hero & section titles. Used upright and italic. */
const instrumentSerif = Instrument_Serif({
  variable: "--font-display",
  weight: ["400"],
  style: ["normal", "italic"],
  subsets: ["latin"],
});

/* Variable body serif with optical sizing — book-length reading. */
const fraunces = Fraunces({
  variable: "--font-body",
  subsets: ["latin"],
  axes: ["SOFT", "opsz"],
});

/* Serial numbers, codes, agency abbreviations, numeric data. */
const jetbrains = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Federal AI Use Case Inventory 2025",
  description:
    "Dashboard for the 2025 Federal AI Use Case Inventory — agencies, use cases, products, and templates mandated by OMB M-25-21.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const paletteIndex = getCommandPaletteIndex();
  const lastUpdated = getLastUpdatedDate();

  return (
    <html
      lang="en"
      className={`${instrumentSerif.variable} ${fraunces.variable} ${jetbrains.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground paper-grain">
        <Dateline lastUpdated={lastUpdated} />
        <Navigation />
        <main className="flex flex-1 flex-col">{children}</main>
        <SiteFooter lastUpdated={lastUpdated} />
        <CommandPalette index={paletteIndex} />
      </body>
    </html>
  );
}

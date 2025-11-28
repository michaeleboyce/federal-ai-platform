import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Federal AI Platform",
  description: "Browse and explore federal AI services, use cases, and incidents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-cream text-charcoal font-sans">{children}</body>
    </html>
  );
}

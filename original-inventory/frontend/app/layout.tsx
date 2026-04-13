import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FedRAMP Marketplace Browser",
  description: "Browse and search FedRAMP authorized cloud services",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlgoFlow",
  description: "A multi-agent coding interview mentor powered by Google ADK"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

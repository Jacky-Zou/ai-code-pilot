import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AICodePilot",
  description: "LLM Agent based AI codebase understanding and development assistant"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

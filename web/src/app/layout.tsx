import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Promethicc AI — Your AI Expert Panel",
  description:
    "Five specialized AI experts — Code, Engineering, Agriculture, Medicine, and Law — at your fingertips. Free offline mode, premium online mode with web search and RAG.",
  keywords: [
    "AI",
    "expert",
    "code",
    "engineering",
    "agriculture",
    "medicine",
    "law",
    "chatbot",
  ],
};

/**
 * Root layout — applies Inter font, dark background, and auth provider.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="min-h-screen bg-[#0a0a1a] font-sans text-gray-200 antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

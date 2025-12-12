import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "ML Inventory Agent | Dashboard",
  description: "AI-powered demand shift detection and non-moving inventory identification",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" data-scroll-behavior="smooth">
      <body
        className={`${plusJakarta.variable} ${spaceGrotesk.variable} antialiased min-h-screen`}
        style={{ fontFamily: "var(--font-plus-jakarta), system-ui, sans-serif" }}
      >
        {/* Animated Background */}
        <div className="animated-bg">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
          <div className="orb orb-4" />
          <div className="mesh-gradient" />
          <div className="grid-pattern" />
        </div>
        
        {children}
      </body>
    </html>
  );
}

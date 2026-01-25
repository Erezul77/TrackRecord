// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { MobileNav } from "@/components/MobileNav";
import { LanguageSelector } from "@/components/LanguageSelector";
import { AuthButton } from "@/components/AuthButton";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TrackRecord | Accountability for Pundits",
  description: "Tracking predictions and financial performance of world pundits.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={cn(inter.className, "bg-white min-h-screen text-black")}>
        {/* Clean B&W Header */}
        <header className="bg-white border-b border-neutral-200 sticky top-0 z-50">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <img 
                src="/TrackRecord_Logo1.png" 
                alt="TrackRecord" 
                className="h-8 sm:h-10 w-auto"
              />
              <span className="text-lg sm:text-xl font-black tracking-tighter text-black">TRACKRECORD</span>
            </Link>
            
            {/* Desktop Nav - Clean B&W */}
            <nav className="hidden md:flex items-center gap-8">
              <Link href="/" className="text-sm font-semibold text-neutral-600 hover:text-black transition-colors">Leaderboard</Link>
              <Link href="/predictions" className="text-sm font-semibold text-neutral-600 hover:text-black transition-colors">Predictions</Link>
              <Link href="/compete" className="text-sm font-semibold text-amber-600 hover:text-amber-700 transition-colors">Compete</Link>
              <Link href="/submit" className="text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors">+ Submit</Link>
              <Link href="/resolve" className="text-sm font-semibold text-neutral-600 hover:text-black transition-colors">Resolve</Link>
              <Link href="/admin" className="text-sm font-semibold text-neutral-400 hover:text-black transition-colors">Admin</Link>
            </nav>

            <div className="flex items-center gap-2 sm:gap-4">
              <AuthButton />
              <LanguageSelector />
              <span className="hidden sm:block text-[10px] font-bold text-neutral-400 uppercase tracking-widest border border-neutral-300 px-2 py-0.5 rounded">Beta</span>
              {/* Mobile Nav */}
              <MobileNav />
            </div>
          </div>
        </header>
        <main className="bg-neutral-50">
          {children}
        </main>
        {/* Clean Black Footer */}
        <footer className="bg-black text-neutral-400 py-16 mt-0">
          <div className="container mx-auto px-4 grid md:grid-cols-4 gap-12">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <img 
                  src="/TrackRecord_Logo1.png" 
                  alt="TrackRecord" 
                  className="h-8 w-auto brightness-0 invert"
                />
                <span className="text-xl font-black tracking-tighter text-white">TRACKRECORD</span>
              </div>
              <p className="text-sm leading-relaxed max-w-sm text-neutral-500">
                The accountability layer for public predictions. We track what people say will happen, and keep score.
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4 uppercase tracking-widest text-xs">Resources</h4>
              <ul className="space-y-3 text-sm">
                <li><Link href="/methodology" className="text-neutral-400 hover:text-white transition-colors">Methodology</Link></li>
                <li><Link href="/api-docs" className="text-neutral-400 hover:text-white transition-colors">API</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4 uppercase tracking-widest text-xs">Legal</h4>
              <ul className="space-y-3 text-sm">
                <li><Link href="/privacy" className="text-neutral-400 hover:text-white transition-colors">Privacy</Link></li>
                <li><Link href="/terms" className="text-neutral-400 hover:text-white transition-colors">Terms</Link></li>
                <li><Link href="/disclaimer" className="text-neutral-400 hover:text-white transition-colors">Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="container mx-auto px-4 border-t border-neutral-800 mt-12 pt-8 text-xs text-center text-neutral-600">
            © 2026 TrackRecord. All rights reserved.
          </div>
        </footer>
      </body>
    </html>
  );
}

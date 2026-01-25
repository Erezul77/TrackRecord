// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { MobileNav } from "@/components/MobileNav";

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
      <body className={cn(inter.className, "bg-slate-50 min-h-screen")}>
        <header className="bg-white border-b sticky top-0 z-50">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <img 
                src="/TrackRecord_Logo1.png" 
                alt="TrackRecord" 
                className="h-8 sm:h-10 w-auto"
              />
              <span className="text-lg sm:text-xl font-black tracking-tighter text-slate-900">TRACKRECORD</span>
            </Link>
            
            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-8">
              <Link href="/" className="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors">Leaderboard</Link>
              <Link href="/predictions" className="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors">Predictions</Link>
              <Link href="/compete" className="text-sm font-bold text-yellow-600 hover:text-yellow-700 transition-colors">🏆 Compete</Link>
              <Link href="/submit" className="text-sm font-bold text-emerald-600 hover:text-emerald-700 transition-colors">+ Submit</Link>
              <Link href="/resolve" className="text-sm font-bold text-emerald-600 hover:text-emerald-700 transition-colors">⚖️ Resolve</Link>
              <Link href="/admin" className="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors">Admin</Link>
            </nav>

            <div className="flex items-center gap-4">
              <span className="hidden sm:block text-xs font-bold text-slate-400 uppercase tracking-wider">Beta</span>
              {/* Mobile Nav */}
              <MobileNav />
            </div>
          </div>
        </header>
        <main>
          {children}
        </main>
        <footer className="bg-slate-900 text-slate-400 py-12 mt-20">
          <div className="container mx-auto px-4 grid md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <img 
                  src="/TrackRecord_Logo1.png" 
                  alt="TrackRecord" 
                  className="h-8 w-auto brightness-0 invert"
                />
                <span className="text-xl font-black tracking-tighter text-white">TRACKRECORD</span>
              </div>
              <p className="text-sm leading-relaxed max-w-sm">
                The accountability layer for public predictions. We track pundits across Twitter, podcasts, and articles, matching their claims to prediction markets.
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4 uppercase tracking-widest text-xs">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/methodology" className="hover:text-white">Methodology</Link></li>
                <li><Link href="/api-docs" className="hover:text-white">API Documentation</Link></li>
                <li><Link href="/polymarket" className="hover:text-white">Polymarket Integration</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4 uppercase tracking-widest text-xs">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/disclaimer" className="hover:text-white">Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="container mx-auto px-4 border-t border-slate-800 mt-12 pt-8 text-xs text-center">
            © 2026 TrackRecord. All rights reserved. Created by Erez Ashkenazi & Lior Gabzo.
          </div>
        </footer>
      </body>
    </html>
  );
}

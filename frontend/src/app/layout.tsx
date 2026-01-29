// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { MobileNav } from "@/components/MobileNav";
import { AuthButton } from "@/components/AuthButton";
import { ThemeToggle } from "@/components/ThemeToggle";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TrackRecord | Accountability for Pundits",
  description: "Tracking predictions and financial performance of world pundits.",
  icons: {
    icon: "/TrackRecord_Logo_White.png",
    shortcut: "/TrackRecord_Logo_White.png",
    apple: "/TrackRecord_Logo_White.png",
  },
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(inter.className, "bg-white dark:bg-black min-h-screen text-black dark:text-white transition-colors")}>
        {/* Clean B&W Header */}
        <header className="bg-white dark:bg-black border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50 transition-colors">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <img 
                src="/TrackRecord_Logo1.png" 
                alt="TrackRecord" 
                className="h-8 sm:h-10 w-auto dark:invert"
              />
              <span className="text-lg sm:text-xl font-black tracking-tighter text-black dark:text-white">TRACKRECORD</span>
            </Link>
            
            {/* Desktop Nav - Clean B&W */}
            <nav className="hidden md:flex items-center gap-8">
              <Link href="/" className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors">Leaderboard</Link>
              <Link href="/predictions" className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors">Predictions</Link>
              <Link href="/compete" className="text-sm font-semibold text-amber-600 hover:text-amber-700 transition-colors">Compete</Link>
              <Link href="/submit" className="text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors">+ Submit</Link>
              <Link href="/apply" className="text-sm font-semibold text-green-600 hover:text-green-700 transition-colors">Apply</Link>
              <Link href="/resolve" className="text-sm font-semibold text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors">Resolve</Link>
              <Link href="/admin" className="text-sm font-semibold text-neutral-400 hover:text-black dark:hover:text-white transition-colors">Admin</Link>
            </nav>

            <div className="flex items-center gap-1 sm:gap-3">
              <ThemeToggle />
              <AuthButton />
              <span className="hidden sm:block text-[10px] font-bold text-neutral-400 uppercase tracking-widest border border-neutral-300 dark:border-neutral-700 px-2 py-0.5 rounded">Beta</span>
              {/* Mobile Nav */}
              <MobileNav />
            </div>
          </div>
        </header>
        <main className="bg-neutral-50 dark:bg-neutral-950 transition-colors">
          {children}
        </main>
        {/* Clean Black Footer - inverts in dark mode */}
        <footer className="bg-black dark:bg-white text-neutral-400 dark:text-neutral-600 py-16 mt-0 transition-colors">
          <div className="container mx-auto px-4 grid md:grid-cols-4 gap-12">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <img 
                  src="/TrackRecord_Logo1.png" 
                  alt="TrackRecord" 
                  className="h-8 w-auto brightness-0 invert dark:invert-0"
                />
                <span className="text-xl font-black tracking-tighter text-white dark:text-black">TRACKRECORD</span>
              </div>
              <p className="text-sm leading-relaxed max-w-sm text-neutral-500">
                The accountability layer for public predictions. We track what people say will happen, and keep score.
              </p>
            </div>
            <div>
              <h4 className="text-white dark:text-black font-bold mb-4 uppercase tracking-widest text-xs">Resources</h4>
              <ul className="space-y-3 text-sm">
                <li><Link href="/methodology" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Methodology</Link></li>
                <li><a href="https://api.trackrecord.life/docs" target="_blank" rel="noopener noreferrer" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">API</a></li>
                <li><Link href="/apply" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Apply to be Tracked</Link></li>
                <li><Link href="/submit" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Submit a Prediction</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white dark:text-black font-bold mb-4 uppercase tracking-widest text-xs">Legal</h4>
              <ul className="space-y-3 text-sm">
                <li><Link href="/privacy" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Privacy</Link></li>
                <li><Link href="/terms" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Terms</Link></li>
                <li><Link href="/disclaimer" className="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-colors">Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="container mx-auto px-4 border-t border-neutral-800 dark:border-neutral-200 mt-12 pt-8 text-xs text-center text-neutral-600 dark:text-neutral-400">
            © 2026 TrackRecord. All rights reserved.
          </div>
        </footer>
      </body>
    </html>
  );
}

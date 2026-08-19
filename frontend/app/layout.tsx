import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "LearnOS", template: "%s · LearnOS" },
  description: "Your AI-powered learning operating system.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: `(function(){try{var t=localStorage.getItem('learnos-theme');if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.classList.toggle('dark',t==='dark');document.documentElement.style.colorScheme=t}catch(e){}})()` }} /></head><body>{children}</body></html>;
}

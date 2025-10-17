import type React from 'react';
import type { Metadata } from 'next';
import { Poppins } from 'next/font/google';
import './globals.css';

const _poppins = Poppins({
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'LLM-Based-Curriculum-Analyzer',
  description:
    "Analyze curriculum handouts and question papers using LLMs to gain insights into topic coverage and Bloom's taxonomy alignment.",
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en'>
      <body className={`font-sans antialiased`}>{children}</body>
    </html>
  );
}

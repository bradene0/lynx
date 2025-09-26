import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'LYNX - Linked Knowledge Network Explorer',
  description: 'Explore knowledge as a zoomable galaxy. Discover connections between concepts through semantic search and visualization.',
  keywords: ['knowledge graph', 'semantic search', 'visualization', 'research', 'discovery'],
  authors: [{ name: 'LYNX Team' }],
  openGraph: {
    title: 'LYNX - Linked Knowledge Network Explorer',
    description: 'Explore knowledge as a zoomable galaxy',
    type: 'website',
    siteName: 'LYNX',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'LYNX - Linked Knowledge Network Explorer',
    description: 'Explore knowledge as a zoomable galaxy',
  },
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#1a1a2e',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}

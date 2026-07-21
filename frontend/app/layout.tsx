import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Civil Atlas',
  description: 'Time-enabled historical civilization atlas prototype',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

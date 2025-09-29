// Layout component for the NASA Space Weather Dashboard

import React from 'react';
import Head from 'next/head';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

export default function Layout({ children, title = 'NASA Space Weather Dashboard' }: LayoutProps) {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="NASA Space Weather Forecaster - Real-time space weather monitoring and alerts" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-space-gradient">
        <main>{children}</main>
      </div>
    </>
  );
}
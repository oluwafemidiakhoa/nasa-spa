// Next.js App component with global providers

import type { AppProps } from 'next/app';
import { SWRConfig } from 'swr';
import '@/styles/globals.css';

// SWR global configuration
const swrConfig = {
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  refreshInterval: 0,
  dedupingInterval: 5000,
  errorRetryCount: 3,
  onError: (error: any) => {
    console.error('SWR Error:', error);
  }
};

export default function App({ Component, pageProps }: AppProps) {
  return (
    <SWRConfig value={swrConfig}>
      <Component {...pageProps} />
    </SWRConfig>
  );
}
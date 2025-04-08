import React from 'react';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { CssBaseline } from '@mui/material';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { ThemeProvider, NotificationProvider } from '../contexts';
import { ErrorBoundary } from '../components/ui';
import { queryClient } from '../utils/reactQuery';

import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>LLMNightRun</title>
        <meta name="description" content="멀티 LLM 통합 자동화 플랫폼" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <CssBaseline />
          <NotificationProvider>
            <ErrorBoundary>
              <Component {...pageProps} />
            </ErrorBoundary>
          </NotificationProvider>
        </ThemeProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </>
  );
}

export default MyApp;

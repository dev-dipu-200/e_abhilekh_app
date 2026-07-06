import type { Metadata } from 'next'
import './globals.css'
import { AppProviders } from '@/components/providers/AppProviders'
import { AuthProvider } from '@/context/AuthContext'
import { LanguageProvider } from '@/context/LanguageContext'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

export const metadata: Metadata = {
  title: 'E-Abhilekh - Document Management',
  description: 'Document management and AI-assisted drafting platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Manrope:wght@400..800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ fontFamily: 'Manrope, system-ui, sans-serif' }} data-theme="sunrise">
        <AppProviders>
          <AuthProvider>
            <LanguageProvider>
              {children}
            </LanguageProvider>
            <ToastContainer position="top-right" autoClose={1000} hideProgressBar />
          </AuthProvider>
        </AppProviders>
      </body>
    </html>
  )
}

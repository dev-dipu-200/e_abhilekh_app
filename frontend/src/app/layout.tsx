import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/context/AuthContext'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

export const metadata: Metadata = {
  title: 'E-Abhilekh - Document Management',
  description: 'Document management and AI-assisted drafting platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
        <AuthProvider>
          {children}
          <ToastContainer position="top-right" autoClose={1000} hideProgressBar />
        </AuthProvider>
      </body>
    </html>
  )
}

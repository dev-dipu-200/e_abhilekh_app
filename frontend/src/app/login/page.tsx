'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { noLeadingSpace } from '@/lib/utils'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#081a3d] via-[#102a56] to-[#1b3b6b] relative overflow-hidden flex flex-col justify-center items-center">

      {/* Background Blur */}
      <div className="absolute left-0 top-0 h-80 w-80 rounded-full bg-orange-400/20 blur-[120px]" />
      <div className="absolute right-0 bottom-0 h-96 w-96 rounded-full bg-sky-400/10 blur-[150px]" />

      {/* Government Header */}
      <div className="mb-16 pt-8 flex items-center">
        <div className="text-center text-white">
          <img
            src="/gov-logo.png"
            className="mx-auto w-10"
            alt=""
          />

          <h2 className="font-semibold text-sm">
            Government of Uttar Pradesh
          </h2>

          <p className="text-xs opacity-70">
            उत्तर प्रदेश सरकार
          </p>
        </div>
      </div>

      {/* Login Card */}
      <div className="flex justify-center items-center">

        <div className="w-[380px] rounded-2xl bg-white shadow-2xl px-8 py-6">

          {/* Logo */}
          <div className="flex gap-3">

            <div className="h-11 w-11 rounded-xl bg-orange-500 flex items-center justify-center">

              <img
                src="/logo.png"
                className="w-6"
                alt=""
              />

            </div>

            <div>

              <h1 className="text-2xl font-bold text-slate-900">
                e-Abhilekh
              </h1>

              <p className="text-sm text-gray-500">
                Digital File Governance | Digital Governance Portal
              </p>

            </div>

          </div>

          <hr className="my-4" />

          <p className="text-gray-500 text-sm mb-4">
            Sign in to access the government digital file governance workspace.
          </p>

          <form onSubmit={handleSubmit}>
            {/* Username */}
            <div>
              <label className="text-xs tracking-widest font-semibold text-gray-500 uppercase">
                Employee ID / Username / Email
              </label>

              <input
                type="email"
                className="mt-2 w-full rounded-lg border p-3 outline-none focus:ring-2 focus:ring-orange-500"
                placeholder="Username or official email"
                value={email}
                onChange={(e) => setEmail(noLeadingSpace(e.target.value))}
              />
            </div>

            {/* Password */}
            <div className="mt-4">
              <label className="text-xs tracking-widest font-semibold text-gray-500 uppercase">
                Password
              </label>

              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="mt-2 w-full rounded-lg border p-3 pr-12 outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(noLeadingSpace(e.target.value))}
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-6 h-5 w-5 text-gray-400 cursor-pointer"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="flex justify-end mt-2">
              <button type="button" className="text-sm font-semibold hover:text-orange-500">
                Forgot password?
              </button>
            </div>

            {/* Button */}
            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full rounded-lg bg-[#0f274d] py-3 text-white font-semibold hover:bg-[#163764] transition disabled:opacity-50"
            >
              {loading ? 'SIGNING IN...' : 'SIGN IN TO SYSTEM'}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center text-xs text-gray-400">
            <p>
              NIC | National Informatics Centre | Government of India
            </p>

            <p className="mt-2 font-semibold text-red-500">
              Authorized access only. All activity is monitored and logged.
            </p>
          </div>

        </div>

      </div>

    </main>
  )
}

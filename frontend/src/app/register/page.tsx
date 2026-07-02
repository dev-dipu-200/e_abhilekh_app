'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button, Input } from '@/components/ui'
import { FileUp, Eye, EyeOff } from 'lucide-react'
import { toast } from '@/lib/toast'
import { noLeadingSpace } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/admin/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), username: username.trim(), password, full_name: fullName?.trim() || null }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ message: 'Registration failed' }))
        toast(err.message || 'Registration failed', 'error')
        return
      }
      toast('Registration successful! Redirecting to login...', 'success')
      setTimeout(() => router.push('/login'), 2000)
    } catch (err: any) {
      toast(err.message || 'Registration failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-50 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 bg-primary-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-primary-200">
              <FileUp className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Create account</h1>
            <p className="text-sm text-gray-500 mt-1">Register for E-Abhilekh</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
              <Input id="fullName" label="Full Name" type="text" value={fullName} onChange={(e) => setFullName(noLeadingSpace(e.target.value))} placeholder="John Doe" />
              <Input id="email" label="Email" type="email" value={email} onChange={(e) => setEmail(noLeadingSpace(e.target.value))} placeholder="admin@example.com" required />
              <Input id="username" label="Username" type="text" value={username} onChange={(e) => setUsername(noLeadingSpace(e.target.value))} placeholder="johndoe" required />
              <div className="relative">
                <Input id="password" label="Password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(noLeadingSpace(e.target.value))} placeholder="Enter your password" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-[34px] text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            <Button type="submit" className="w-full" size="lg" loading={loading}>
              Register
            </Button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{' '}
            <Link href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Sign in
            </Link>
          </p>

          <p className="text-center text-xs text-gray-400 mt-6">
            &copy; {new Date().getFullYear()} E-Abhilekh. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}

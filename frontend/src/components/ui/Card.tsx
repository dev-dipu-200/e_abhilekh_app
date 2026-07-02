import { ReactNode } from 'react'
import clsx from 'clsx'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: boolean
}

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={clsx('bg-white rounded-xl shadow-sm border border-gray-200', padding && 'p-6', className)}>
      {children}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number | string
  icon: ReactNode
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
}

const iconColors = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-green-50 text-green-600',
  yellow: 'bg-yellow-50 text-yellow-600',
  red: 'bg-red-50 text-red-600',
  purple: 'bg-purple-50 text-purple-600',
}

export function StatCard({ label, value, icon, color = 'blue' }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className={clsx('p-3 rounded-xl', iconColors[color])}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
      </div>
    </div>
  )
}

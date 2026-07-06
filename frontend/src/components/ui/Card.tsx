import { ReactNode } from 'react'
import clsx from 'clsx'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: boolean
}

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={clsx('card', padding && 'p-6', className)}>
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
  blue: 'bg-primary-50 text-primary-600',
  green: 'bg-green-50 text-green-600',
  yellow: 'bg-yellow-50 text-yellow-600',
  red: 'bg-red-50 text-red-600',
  purple: 'bg-primary-100 text-primary-700',
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

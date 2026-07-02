import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

interface SpinnerProps {
  size?: number
  className?: string
}

export function Spinner({ size = 24, className }: SpinnerProps) {
  return <Loader2 className={clsx('animate-spin text-primary-600', className)} size={size} />
}

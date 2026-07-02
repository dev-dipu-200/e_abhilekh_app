import { toast as notify } from 'react-toastify'

export function toast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  notify(message, { type })
}

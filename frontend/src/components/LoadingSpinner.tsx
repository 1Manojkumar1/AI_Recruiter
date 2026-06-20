import { FiLoader } from 'react-icons/fi'

interface LoadingSpinnerProps {
  text?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
}

export default function LoadingSpinner({ text, size = 'md' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <FiLoader className={`${sizeClasses[size]} text-primary-500 animate-spin`} />
      {text && (
        <div className="text-center">
          <p className="text-sm font-medium text-gray-700">{text}</p>
          <div className="mt-2 flex items-center gap-2">
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      )}
    </div>
  )
}

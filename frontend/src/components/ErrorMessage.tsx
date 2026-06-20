import { FiAlertCircle, FiX } from 'react-icons/fi'

interface ErrorMessageProps {
  message: string
  onDismiss?: () => void
}

export default function ErrorMessage({ message, onDismiss }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
      <FiAlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm text-red-800 font-medium">Error</p>
        <p className="text-sm text-red-700 mt-1">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-600 transition-colors"
        >
          <FiX className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

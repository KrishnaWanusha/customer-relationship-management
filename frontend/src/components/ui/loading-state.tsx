import { Loader2 } from "lucide-react"
import { cn } from "@/utils"

export interface SpinnerProps {
  size?: "sm" | "md" | "lg"
  className?: string
}

export function Spinner({ size = "md", className }: SpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-10 w-10",
  }

  return (
    <Loader2
      className={cn("animate-spin text-primary", sizeClasses[size], className)}
    />
  )
}

export interface LoadingStateProps {
  message?: string
  className?: string
}

export function LoadingState({
  message = "Loading...",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center",
        className,
      )}
    >
      <Spinner size="lg" className="mb-4" />
      <p className="text-sm text-muted-foreground font-medium">{message}</p>
    </div>
  )
}

export function FullPageLoading({
  message = "Initializing...",
}: {
  message?: string
}) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
      <Spinner size="lg" className="h-12 w-12 mb-4 text-primary" />
      <p className="text-sm font-medium text-muted-foreground tracking-wide">
        {message}
      </p>
    </div>
  )
}

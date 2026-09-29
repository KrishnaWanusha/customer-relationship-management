import { Link } from "react-router-dom"
import { Button } from "@/components"

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <h1 className="text-5xl font-black tracking-tight text-primary">404</h1>
      <h2 className="text-xl font-semibold text-foreground">Page Not Found</h2>
      <p className="text-sm text-muted-foreground max-w-sm">
        The page you are looking for does not exist or may have been moved.
      </p>
      <Link to="/dashboard">
        <Button variant="default">Return to Dashboard</Button>
      </Link>
    </div>
  )
}

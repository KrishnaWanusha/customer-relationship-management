import { Link } from "react-router-dom"
import { Button } from "@/components"

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <h1 className="text-4xl font-bold tracking-tight">404</h1>
      <p className="text-muted-foreground">The page you are looking for does not exist.</p>
      <Link to="/">
        <Button variant="outline">Return Home</Button>
      </Link>
    </div>
  )
}

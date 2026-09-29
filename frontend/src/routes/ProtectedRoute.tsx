import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks"
import { FullPageLoading } from "@/components"
import type { UserRole } from "@/types"

export interface ProtectedRouteProps {
  allowedRoles?: UserRole[]
  children?: React.ReactNode
}

export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <FullPageLoading message="Verifying authentication..." />
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <h2 className="text-xl font-bold text-destructive mb-2">Access Denied</h2>
        <p className="text-muted-foreground max-w-md">
          Your role ({user.role}) does not have permission to access this resource.
        </p>
      </div>
    )
  }

  return children ? <>{children}</> : <Outlet />
}

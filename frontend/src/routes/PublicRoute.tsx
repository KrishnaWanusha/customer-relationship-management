import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks"
import { FullPageLoading } from "@/components"

export function PublicRoute({ children }: { children?: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ||
    "/dashboard"

  if (isLoading) {
    return <FullPageLoading message="Loading..." />
  }

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  return children ? <>{children}</> : <Outlet />
}

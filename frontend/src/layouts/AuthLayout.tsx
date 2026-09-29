import { Outlet } from "react-router-dom"

export function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-muted/40 text-foreground">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="h-12 w-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl shadow-md mb-3">
            CRM
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Enterprise CRM</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Multi-Tenant Customer Relationship Management
          </p>
        </div>

        <Outlet />

        <div className="mt-8 text-center text-xs text-muted-foreground">
          Secure, isolated multi-tenant architecture
        </div>
      </div>
    </div>
  )
}

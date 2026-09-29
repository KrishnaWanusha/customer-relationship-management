import { useAuth } from "@/hooks"
import { Building2, Users, History, Shield } from "lucide-react"
import { Link } from "react-router-dom"
import { Badge, buttonVariants } from "@/components"
import { cn } from "@/utils"

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Welcome back, {user?.first_name || "User"}!
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Organization:{" "}
            <span className="font-semibold text-foreground">
              {user?.organization?.name || "Default Organization"}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="px-3 py-1">
            <Shield className="h-3.5 w-3.5 mr-1" />
            Role: {user?.role}
          </Badge>
        </div>
      </div>

      {/* Quick summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground">Companies</h3>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Building2 className="h-5 w-5" />
            </div>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Manage your organization&apos;s corporate accounts, logos, and
            details.
          </p>
          <Link
            to="/companies"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            View Companies
          </Link>
        </div>

        <div className="p-6 rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-foreground">Contacts</h3>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Track business contacts, communication channels, and relationships.
          </p>
          <Link
            to="/contacts"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            View Contacts
          </Link>
        </div>

        {user?.can_view_activity_logs && (
          <div className="p-6 rounded-xl border border-border bg-card shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-foreground">Activity Logs</h3>
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <History className="h-5 w-5" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Review audit logs of all company and contact mutations.
            </p>
            <Link
              to="/activity-logs"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
            >
              View Logs
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

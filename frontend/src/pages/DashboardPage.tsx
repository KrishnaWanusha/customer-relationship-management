import { useState, useEffect, useCallback, useMemo } from "react"
import { Link } from "react-router-dom"
import {
  Building2,
  Users,
  History,
  Shield,
  ArrowRight,
  RefreshCw,
  Clock,
  Sparkles,
  ExternalLink,
} from "lucide-react"
import {
  Badge,
  Button,
  buttonVariants,
  LoadingState,
  ErrorState,
} from "@/components"
import { companiesService, contactsService, activityLogsService } from "@/api"
import { useAuth } from "@/hooks"
import { formatDateTime, cn } from "@/utils"
import type { ActivityLog } from "@/types"

interface DashboardMetrics {
  companiesCount: number
  contactsCount: number
  activityLogsCount: number
}

export function DashboardPage() {
  const { user } = useAuth()

  const [metrics, setMetrics] = useState<DashboardMetrics>({
    companiesCount: 0,
    contactsCount: 0,
    activityLogsCount: 0,
  })
  const [recentLogs, setRecentLogs] = useState<ActivityLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const canViewLogs = Boolean(
    user?.can_view_activity_logs ??
    (user?.role === "ADMIN" || user?.role === "MANAGER"),
  )

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const companiesPromise = companiesService.getCompanies({ page_size: 1 })
      const contactsPromise = contactsService.getContacts({ page_size: 1 })
      const logsPromise = canViewLogs
        ? activityLogsService.getActivityLogs({ page_size: 5 })
        : Promise.resolve(null)

      const [companiesRes, contactsRes, logsRes] = await Promise.all([
        companiesPromise,
        contactsPromise,
        logsPromise,
      ])

      setMetrics({
        companiesCount:
          companiesRes.data.pagination?.count ??
          companiesRes.data.results.length,
        contactsCount:
          contactsRes.data.pagination?.count ?? contactsRes.data.results.length,
        activityLogsCount: logsRes?.data.pagination?.count ?? 0,
      })

      if (logsRes?.data.results) {
        setRecentLogs(logsRes.data.results)
      }
    } catch {
      setError("Unable to load organization dashboard metrics.")
    } finally {
      setIsLoading(false)
    }
  }, [canViewLogs])

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const handleRetry = useCallback(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const roleVariant = useMemo(() => {
    switch (user?.role) {
      case "ADMIN":
        return "destructive"
      case "MANAGER":
        return "warning"
      default:
        return "secondary"
    }
  }, [user?.role])

  const getActionBadgeVariant = useCallback(
    (action: string): "success" | "warning" | "destructive" | "secondary" => {
      switch (action) {
        case "CREATE":
          return "success"
        case "UPDATE":
          return "warning"
        case "DELETE":
          return "destructive"
        default:
          return "secondary"
      }
    },
    [],
  )

  const userPermissionsSummary = useMemo(() => {
    switch (user?.role) {
      case "ADMIN":
        return "Full Administrative Control (CRUD, Deletion & Audit Trail)"
      case "MANAGER":
        return "Management Access (Create, Update & Audit Trail)"
      case "STAFF":
        return "Standard Operational Access (Create & Edit Contacts/Companies)"
      default:
        return "CRM Access"
    }
  }, [user?.role])

  if (isLoading) {
    return <LoadingState message="Loading organization dashboard..." />
  }

  if (error) {
    return (
      <ErrorState
        title="Dashboard Error"
        message={error}
        onRetry={handleRetry}
      />
    )
  }

  return (
    <div className="space-y-8">
      {/* Welcome & Organization Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Welcome back, {user?.first_name || "Team Member"}!
            </h1>
            <Badge variant={roleVariant} className="px-2.5 py-0.5 text-xs">
              <Shield className="h-3 w-3 mr-1" />
              {user?.role}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Organization:{" "}
            <span className="font-semibold text-foreground">
              {user?.organization?.name || "CRM Tenant"}
            </span>{" "}
            • {userPermissionsSummary}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
            className="text-xs"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
          <Link to="/companies" className={cn(buttonVariants({ size: "sm" }))}>
            <Building2 className="h-3.5 w-3.5 mr-1.5" />
            Manage CRM
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Companies Metric Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between hover:border-primary/40 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Active Companies
            </span>
            <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
              <Building2 className="h-5 w-5" />
            </div>
          </div>
          <div className="space-y-1 mb-4">
            <div className="text-3xl font-extrabold tracking-tight text-foreground">
              {metrics.companiesCount}
            </div>
            <p className="text-xs text-muted-foreground">
              Client & partner organizations on file
            </p>
          </div>
          <div className="pt-4 border-t border-border flex items-center justify-between">
            <Link
              to="/companies"
              className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
            >
              View all companies
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* Contacts Metric Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between hover:border-primary/40 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Client Contacts
            </span>
            <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <div className="space-y-1 mb-4">
            <div className="text-3xl font-extrabold tracking-tight text-foreground">
              {metrics.contactsCount}
            </div>
            <p className="text-xs text-muted-foreground">
              Directory of business representatives
            </p>
          </div>
          <div className="pt-4 border-t border-border flex items-center justify-between">
            <Link
              to="/contacts"
              className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
            >
              Browse contact directory
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* Activity or Tenant Plan Metric Card */}
        {canViewLogs ? (
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between hover:border-primary/40 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Audit Trail Events
              </span>
              <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
                <History className="h-5 w-5" />
              </div>
            </div>
            <div className="space-y-1 mb-4">
              <div className="text-3xl font-extrabold tracking-tight text-foreground">
                {metrics.activityLogsCount}
              </div>
              <p className="text-xs text-muted-foreground">
                Recorded mutations & operations
              </p>
            </div>
            <div className="pt-4 border-t border-border flex items-center justify-between">
              <Link
                to="/activity-logs"
                className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
              >
                Inspect activity log
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Tenant Isolation
              </span>
              <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
            </div>
            <div className="space-y-1 mb-4">
              <div className="text-base font-bold text-foreground">
                {user?.organization?.name || "Enterprise"}
              </div>
              <p className="text-xs text-muted-foreground">
                Server-enforced multi-tenant partition active
              </p>
            </div>
            <div className="pt-4 border-t border-border flex items-center text-xs text-muted-foreground">
              <span>Security enforced via backend policies</span>
            </div>
          </div>
        )}
      </div>

      {/* Organization Details & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Links & Shortcuts Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-foreground tracking-tight">
            Quick Actions
          </h2>
          <p className="text-xs text-muted-foreground">
            Frequently used operations for account management
          </p>

          <div className="space-y-2 pt-2">
            <Link
              to="/companies"
              className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors text-sm font-medium"
            >
              <div className="flex items-center gap-2.5">
                <Building2 className="h-4 w-4 text-primary" />
                <span>Companies List</span>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </Link>

            <Link
              to="/contacts"
              className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors text-sm font-medium"
            >
              <div className="flex items-center gap-2.5">
                <Users className="h-4 w-4 text-primary" />
                <span>Contacts Directory</span>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </Link>

            {canViewLogs && (
              <Link
                to="/activity-logs"
                className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors text-sm font-medium"
              >
                <div className="flex items-center gap-2.5">
                  <History className="h-4 w-4 text-primary" />
                  <span>Audit Trail</span>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            )}
          </div>
        </div>

        {/* Recent Organization Activity Feed */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-foreground tracking-tight">
                  Recent Organization Activity
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {canViewLogs
                    ? "Latest operations performed across your organization"
                    : "Activity logs are restricted to Administrators and Managers"}
                </p>
              </div>

              {canViewLogs && (
                <Link
                  to="/activity-logs"
                  className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1"
                >
                  View all
                  <ExternalLink className="h-3 w-3" />
                </Link>
              )}
            </div>

            {canViewLogs ? (
              recentLogs.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  <Clock className="h-8 w-8 mx-auto mb-2 text-muted-foreground/60" />
                  No audit activity recorded yet.
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {recentLogs.map((log) => (
                    <div
                      key={log.id}
                      className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <Badge
                          variant={getActionBadgeVariant(log.action)}
                          className="font-mono text-[10px] px-1.5 py-0.2 shrink-0"
                        >
                          {log.action}
                        </Badge>
                        <span className="font-semibold text-foreground">
                          {log.model_name}
                        </span>
                        <span className="text-muted-foreground font-mono text-[11px]">
                          #{log.object_id.slice(0, 8)}
                        </span>
                        {log.details &&
                          typeof log.details.name === "string" && (
                            <span className="text-muted-foreground truncate max-w-[150px]">
                              ({log.details.name})
                            </span>
                          )}
                      </div>

                      <div className="flex items-center gap-3 text-muted-foreground shrink-0 sm:self-auto self-end">
                        <span>{log.user_email || "System"}</span>
                        <span>•</span>
                        <span>{formatDateTime(log.timestamp)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : (
              <div className="p-6 rounded-lg bg-muted/30 border border-border text-center text-xs text-muted-foreground mt-2">
                <Shield className="h-6 w-6 mx-auto mb-2 text-muted-foreground/60" />
                Standard staff accounts do not have permission to inspect system
                audit logs.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

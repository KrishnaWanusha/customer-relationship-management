import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import {
  History,
  Search,
  X,
  RotateCcw,
  RefreshCw,
  Building2,
  Users,
  Shield,
  FileText,
} from "lucide-react"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Badge,
  Button,
  Input,
  Pagination,
  LoadingState,
  EmptyState,
  ErrorState,
} from "@/components"
import { activityLogsService } from "@/api"
import { useAuth } from "@/hooks"
import { formatDateTime, cn } from "@/utils"
import type { ActivityLog, ActivityAction, PaginationMeta, ApiError } from "@/types"

export function ActivityLogsPage() {
  const { user } = useAuth()

  // State
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const [pagination, setPagination] = useState<PaginationMeta | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [actionFilter, setActionFilter] = useState<string>("")
  const [modelFilter, setModelFilter] = useState<string>("")

  // Loading & Error
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isFirstSearchRef = useRef(true)

  const canViewLogs = Boolean(
    user?.can_view_activity_logs ??
      (user?.role === "ADMIN" || user?.role === "MANAGER"),
  )

  // Debounce search input
  useEffect(() => {
    if (isFirstSearchRef.current) {
      isFirstSearchRef.current = false
      return
    }
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim())
      setCurrentPage(1)
    }, 350)
    return () => clearTimeout(handler)
  }, [searchQuery])

  // Fetch Activity Logs
  const fetchLogs = useCallback(async () => {
    if (!canViewLogs) return
    setIsLoading(true)
    setError(null)
    try {
      const response = await activityLogsService.getActivityLogs({
        search: debouncedSearch || undefined,
        action: (actionFilter as ActivityAction) || undefined,
        model_name: modelFilter || undefined,
        page: currentPage,
      })
      setLogs(response.data.results)
      setPagination(response.data.pagination)
    } catch (err: unknown) {
      const apiError = err as ApiError
      setError(apiError.message || "Failed to load organization activity logs.")
    } finally {
      setIsLoading(false)
    }
  }, [canViewLogs, debouncedSearch, actionFilter, modelFilter, currentPage])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  // Handlers
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value)
    },
    [],
  )

  const handleClearSearch = useCallback(() => {
    setSearchQuery("")
    setDebouncedSearch("")
    setCurrentPage(1)
  }, [])

  const handleActionChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setActionFilter(e.target.value)
      setCurrentPage(1)
    },
    [],
  )

  const handleModelChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setModelFilter(e.target.value)
      setCurrentPage(1)
    },
    [],
  )

  const handleResetFilters = useCallback(() => {
    setSearchQuery("")
    setDebouncedSearch("")
    setActionFilter("")
    setModelFilter("")
    setCurrentPage(1)
  }, [])

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
  }, [])

  const handleRetry = useCallback(() => {
    fetchLogs()
  }, [fetchLogs])

  const hasActiveFilters = useMemo(
    () => Boolean(debouncedSearch || actionFilter || modelFilter),
    [debouncedSearch, actionFilter, modelFilter],
  )

  const getActionBadge = useCallback((action: string) => {
    switch (action) {
      case "CREATE":
        return (
          <Badge variant="success" className="font-mono text-[10px] px-2 py-0.5">
            CREATE
          </Badge>
        )
      case "UPDATE":
        return (
          <Badge variant="warning" className="font-mono text-[10px] px-2 py-0.5">
            UPDATE
          </Badge>
        )
      case "DELETE":
        return (
          <Badge
            variant="destructive"
            className="font-mono text-[10px] px-2 py-0.5"
          >
            DELETE
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary" className="font-mono text-[10px] px-2 py-0.5">
            {action}
          </Badge>
        )
    }
  }, [])

  const renderDetailsSummary = useCallback((details?: Record<string, unknown>) => {
    if (!details || Object.keys(details).length === 0) {
      return <span className="text-muted-foreground text-xs">—</span>
    }

    if (typeof details.name === "string") {
      return (
        <span className="text-foreground text-xs font-medium">
          &ldquo;{details.name}&rdquo;
        </span>
      )
    }

    if (typeof details.full_name === "string") {
      return (
        <span className="text-foreground text-xs font-medium">
          &ldquo;{details.full_name}&rdquo;
        </span>
      )
    }

    if (Array.isArray(details.changed_fields) && details.changed_fields.length > 0) {
      return (
        <span className="text-muted-foreground text-xs">
          Changed:{" "}
          <strong className="text-foreground font-medium">
            {details.changed_fields.join(", ")}
          </strong>
        </span>
      )
    }

    return (
      <span className="text-muted-foreground text-xs font-mono truncate max-w-[200px] block">
        {JSON.stringify(details)}
      </span>
    )
  }, [])

  if (!canViewLogs) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-6 space-y-4">
        <div className="p-3 rounded-full bg-destructive/10 text-destructive">
          <Shield className="h-8 w-8" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-foreground">Access Restricted</h2>
          <p className="text-sm text-muted-foreground max-w-md mt-1">
            Only Organization Administrators and Managers are permitted to inspect activity audit trails.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Title & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Activity Logs
            </h1>
            <Badge variant="secondary" className="font-semibold text-xs">
              {pagination?.count ?? logs.length} Records
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Audit trail of company and contact operations across your organization
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleRetry}
          disabled={isLoading}
          className="self-start sm:self-auto text-xs"
        >
          <RefreshCw className={cn("h-3.5 w-3.5 mr-1.5", isLoading && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-card p-3 rounded-lg border border-border shadow-sm">
        <div className="flex-1 flex flex-col sm:flex-row gap-2">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search by user, model, or object ID..."
              className="pl-9 pr-8"
              value={searchQuery}
              onChange={handleSearchChange}
            />
            {searchQuery && (
              <button
                onClick={handleClearSearch}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Action Filter */}
          <div className="w-full sm:w-40">
            <select
              value={actionFilter}
              onChange={handleActionChange}
              aria-label="Filter by action"
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">All Actions</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>

          {/* Model Filter */}
          <div className="w-full sm:w-40">
            <select
              value={modelFilter}
              onChange={handleModelChange}
              aria-label="Filter by model"
              className="flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">All Models</option>
              <option value="Company">Company</option>
              <option value="Contact">Contact</option>
            </select>
          </div>
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetFilters}
            className="text-xs text-muted-foreground hover:text-foreground whitespace-nowrap self-end sm:self-auto"
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset Filters
          </Button>
        )}
      </div>

      {/* Content Area */}
      {isLoading ? (
        <LoadingState message="Loading organization activity logs..." />
      ) : error ? (
        <ErrorState message={error} onRetry={handleRetry} />
      ) : logs.length === 0 ? (
        hasActiveFilters ? (
          <EmptyState
            icon={<Search className="h-8 w-8 text-muted-foreground" />}
            title="No matching logs"
            description="No audit records match your selected filter criteria."
            actionLabel="Reset Filters"
            onAction={handleResetFilters}
          />
        ) : (
          <EmptyState
            icon={<History className="h-8 w-8 text-muted-foreground" />}
            title="No activity recorded"
            description="Mutations performed on companies and contacts will be logged here automatically."
          />
        )
      ) : (
        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Record ID</TableHead>
                <TableHead>Details / Subject</TableHead>
                <TableHead>Initiator</TableHead>
                <TableHead className="text-right">Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} className="hover:bg-muted/40">
                  <TableCell>
                    {getActionBadge(log.action)}
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-1.5 font-medium text-xs text-foreground">
                      {log.model_name === "Company" ? (
                        <Building2 className="h-3.5 w-3.5 text-primary" />
                      ) : log.model_name === "Contact" ? (
                        <Users className="h-3.5 w-3.5 text-primary" />
                      ) : (
                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                      <span>{log.model_name}</span>
                    </div>
                  </TableCell>

                  <TableCell className="font-mono text-xs text-muted-foreground">
                    #{log.object_id.slice(0, 8)}
                  </TableCell>

                  <TableCell>
                    {renderDetailsSummary(log.details)}
                  </TableCell>

                  <TableCell>
                    <div className="text-xs">
                      <span className="font-semibold text-foreground block">
                        {log.user_name || log.user_email || "System"}
                      </span>
                      {log.user_email && log.user_name && log.user_name !== log.user_email && (
                        <span className="text-muted-foreground text-[11px] block">
                          {log.user_email}
                        </span>
                      )}
                    </div>
                  </TableCell>

                  <TableCell className="text-right text-xs text-muted-foreground whitespace-nowrap">
                    {formatDateTime(log.timestamp)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {pagination && pagination.total_pages > 1 && (
            <div className="px-4 border-t border-border">
              <Pagination
                currentPage={pagination.current_page}
                totalPages={pagination.total_pages}
                totalCount={pagination.count}
                pageSize={pagination.page_size}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

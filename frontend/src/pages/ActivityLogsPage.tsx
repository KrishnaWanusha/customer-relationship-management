import { History, Search } from "lucide-react"
import { Input, EmptyState } from "@/components"

export function ActivityLogsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Activity Logs
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Audit trail of company and contact mutations across your
            organization
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Filter logs..." className="pl-9" />
        </div>
      </div>

      <EmptyState
        icon={<History className="h-8 w-8" />}
        title="Audit trail"
        description="Activity log table and filtering will be connected in the activity log UI phase."
      />
    </div>
  )
}

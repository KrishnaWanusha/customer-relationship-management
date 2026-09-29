import { Building2, Plus, Search } from "lucide-react"
import { Button, Input, EmptyState } from "@/components"

export function CompaniesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Companies
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your organization&apos;s client and partner companies
          </p>
        </div>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Company
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search companies..." className="pl-9" />
        </div>
      </div>

      <EmptyState
        icon={<Building2 className="h-8 w-8" />}
        title="Companies directory"
        description="Company list and management interface will be connected in the CRM management phase."
      />
    </div>
  )
}

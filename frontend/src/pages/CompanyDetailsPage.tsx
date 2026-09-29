import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Building2 } from "lucide-react"
import { buttonVariants } from "@/components"
import { cn } from "@/utils"

export function CompanyDetailsPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/companies"
          className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
        >
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Companies
        </Link>
      </div>

      <div className="p-8 rounded-xl border border-border bg-card">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 rounded-lg bg-primary/10 text-primary">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Company Details</h1>
            <p className="text-xs text-muted-foreground font-mono">ID: {id}</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Detailed company information, logo management, and associated contacts will be loaded here.
        </p>
      </div>
    </div>
  )
}

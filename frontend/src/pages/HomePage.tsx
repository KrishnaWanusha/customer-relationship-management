import { useState } from "react"
import { apiClient } from "@/api"
import { Button } from "@/components"

interface HealthData {
  status: string
  version: string
  service?: string
}

export function HomePage() {
  const [healthStatus, setHealthStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const checkBackendHealth = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get<HealthData>("/health/")
      setHealthStatus(
        `Connected: ${response.data.status} (API ${response.data.version})`,
      )
    } catch {
      setHealthStatus("Failed to connect to backend API")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight mb-2">
          Multi Tenant Customer Relationship Management System
        </h1>

        <div className="flex items-center gap-4">
          <Button onClick={checkBackendHealth} disabled={loading}>
            {loading ? "Checking..." : "Test Backend API"}
          </Button>

          {healthStatus && (
            <span className="text-sm font-medium text-muted-foreground">
              {healthStatus}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

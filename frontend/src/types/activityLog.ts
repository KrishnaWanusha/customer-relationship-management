export type ActivityAction = "CREATE" | "UPDATE" | "DELETE"

export interface ActivityLog {
  id: string
  organization: string
  user: string
  user_email?: string
  user_name?: string
  action: ActivityAction
  model_name: string
  object_id: string
  details?: Record<string, unknown>
  timestamp: string
}

export interface ActivityLogFilters {
  search?: string
  model_name?: string
  action?: ActivityAction
  page?: number
  page_size?: number
}

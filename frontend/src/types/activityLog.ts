export type ActivityAction = "CREATE" | "UPDATE" | "DELETE"

export interface ActivityLog {
  id: string
  organization: string
  user: string
  user_email?: string
  action: ActivityAction
  model_name: string
  object_id: string
  timestamp: string
}

export interface ActivityLogFilters {
  model_name?: string
  action?: ActivityAction
  page?: number
  page_size?: number
}

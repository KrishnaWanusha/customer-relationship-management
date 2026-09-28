export interface ApiResponse<T = unknown> {
  success: boolean
  message?: string
  data: T
  errors?: Record<string, string[]>
}

export interface ApiError {
  message: string
  status?: number
  errors?: Record<string, string[]>
}

export interface ApiResponse<T = unknown> {
  success: boolean
  message?: string
  data: T
  errors?: Record<string, string[]>
}

export interface PaginationMeta {
  count: number
  total_pages: number
  current_page: number
  next: string | null
  previous: string | null
  page_size: number
}

export interface PaginatedData<T> {
  results: T[]
  pagination: PaginationMeta
}

export type PaginatedApiResponse<T> = ApiResponse<PaginatedData<T>>

export interface ApiError {
  message: string
  status?: number
  errors?: Record<string, string[]>
}

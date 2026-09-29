import { apiClient } from "./client"
import type {
  ActivityLog,
  ActivityLogFilters,
  PaginatedApiResponse,
} from "@/types"

export const activityLogsService = {
  async getActivityLogs(
    params?: ActivityLogFilters,
  ): Promise<PaginatedApiResponse<ActivityLog>> {
    const response = await apiClient.get<PaginatedApiResponse<ActivityLog>>(
      "/activity-logs/",
      { params },
    )
    return response.data
  },
}

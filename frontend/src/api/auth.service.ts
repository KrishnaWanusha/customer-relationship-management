import { apiClient } from "./client"
import type {
  ApiResponse,
  LoginCredentials,
  LoginResponseData,
  RefreshResponseData,
  User,
} from "@/types"

export const authService = {
  async login(
    credentials: LoginCredentials,
  ): Promise<ApiResponse<LoginResponseData>> {
    const response = await apiClient.post<ApiResponse<LoginResponseData>>(
      "/auth/login/",
      credentials,
    )
    return response.data
  },

  async logout(): Promise<ApiResponse<null>> {
    const response = await apiClient.post<ApiResponse<null>>(
      "/auth/logout/",
      {},
    )
    return response.data
  },

  async refreshToken(): Promise<ApiResponse<RefreshResponseData>> {
    const response = await apiClient.post<ApiResponse<RefreshResponseData>>(
      "/auth/refresh/",
      {},
    )
    return response.data
  },

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await apiClient.get<ApiResponse<User>>("/auth/me/")
    return response.data
  },
}

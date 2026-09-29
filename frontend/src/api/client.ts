import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"
import type { ApiError, ApiResponse, RefreshResponseData } from "@/types"

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
})

let inMemoryToken: string | null = null

export const setAccessToken = (token: string | null) => {
  inMemoryToken = token
}

export const getAccessToken = () => inMemoryToken

type UnauthorizedCallback = () => void
type TokenRefreshedCallback = (token: string) => void

let unauthorizedHandler: UnauthorizedCallback | null = null
let tokenRefreshedHandler: TokenRefreshedCallback | null = null

export const registerUnauthorizedHandler = (cb: UnauthorizedCallback) => {
  unauthorizedHandler = cb
}

export const registerTokenRefreshedHandler = (cb: TokenRefreshedCallback) => {
  tokenRefreshedHandler = cb
}

interface QueueItem {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

let isRefreshing = false
let failedQueue: QueueItem[] = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token)
    } else {
      prom.reject(error)
    }
  })
  failedQueue = []
}

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (inMemoryToken) {
      config.headers.set("Authorization", `Bearer ${inMemoryToken}`)
    }
    return config
  },
  (error) => Promise.reject(error),
)

apiClient.interceptors.response.use(
  (response) => response,
  async (
    error: AxiosError<{ message?: string; errors?: Record<string, string[]> }>,
  ) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }
    const status = error.response?.status
    const url = originalRequest?.url || ""

    const isAuthEndpoint =
      url.includes("/auth/login/") ||
      url.includes("/auth/refresh/") ||
      url.includes("/auth/logout/")

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((newToken) => {
            originalRequest.headers.set("Authorization", `Bearer ${newToken}`)
            return apiClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshResponse = await axios.post<
          ApiResponse<RefreshResponseData>
        >(
          `${apiClient.defaults.baseURL}/auth/refresh/`,
          {},
          { withCredentials: true },
        )

        const newAccessToken = refreshResponse.data.data.access
        setAccessToken(newAccessToken)

        if (tokenRefreshedHandler) {
          tokenRefreshedHandler(newAccessToken)
        }

        processQueue(null, newAccessToken)
        originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`)
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        setAccessToken(null)
        if (unauthorizedHandler) {
          unauthorizedHandler()
        }
        return Promise.reject(normalizeError(error))
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(normalizeError(error))
  },
)

const normalizeError = (
  error: AxiosError<{ message?: string; errors?: Record<string, string[]> }>,
): ApiError => {
  return {
    message:
      error.response?.data?.message ||
      error.message ||
      "An unexpected error occurred",
    status: error.response?.status,
    errors: error.response?.data?.errors,
  }
}

export default apiClient

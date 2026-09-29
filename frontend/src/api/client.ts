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
  error: AxiosError<{
    message?: string
    detail?: string
    errors?: Record<string, string[]>
    [key: string]: unknown
  }>,
): ApiError => {
  const data = error.response?.data
  let extractedErrors: Record<string, string[]> | undefined = data?.errors

  if (
    !extractedErrors &&
    data &&
    typeof data === "object" &&
    !Array.isArray(data)
  ) {
    const fieldErrors: Record<string, string[]> = {}
    let hasFieldErrors = false

    for (const [key, val] of Object.entries(data)) {
      if (
        key !== "message" &&
        key !== "success" &&
        key !== "status" &&
        key !== "detail"
      ) {
        if (
          Array.isArray(val) &&
          val.every((item) => typeof item === "string")
        ) {
          fieldErrors[key] = val
          hasFieldErrors = true
        } else if (typeof val === "string") {
          fieldErrors[key] = [val]
          hasFieldErrors = true
        }
      }
    }

    if (hasFieldErrors) {
      extractedErrors = fieldErrors
    }
  }

  let message = data?.message || data?.detail

  if (!message && extractedErrors) {
    if (extractedErrors.non_field_errors?.length) {
      message = extractedErrors.non_field_errors[0]
    } else {
      const firstField = Object.keys(extractedErrors)[0]
      if (firstField && extractedErrors[firstField]?.length) {
        message = extractedErrors[firstField][0]
      }
    }
  }

  if (!message) {
    if (error.code === "ERR_NETWORK" || !error.response) {
      message =
        "Unable to connect to server. Please check your network connection."
    } else {
      message = error.message || "An unexpected error occurred"
    }
  }

  return {
    message,
    status: error.response?.status,
    errors: extractedErrors,
  }
}

export default apiClient

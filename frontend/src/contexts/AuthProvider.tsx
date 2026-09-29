import {
  useEffect,
  useReducer,
  useCallback,
  useMemo,
  useRef,
  type ReactNode,
} from "react"
import {
  authService,
  registerTokenRefreshedHandler,
  registerUnauthorizedHandler,
  setAccessToken,
} from "@/api"
import type { ApiError, AuthState, LoginCredentials, User } from "@/types"
import { AuthContext, type AuthContextValue } from "./auth-context"

type AuthAction =
  | { type: "AUTH_START" }
  | { type: "AUTH_SUCCESS"; payload: { user: User; token: string } }
  | { type: "SET_TOKEN"; payload: { token: string } }
  | { type: "AUTH_FAILURE"; payload: { error: string } }
  | { type: "AUTH_LOGOUT" }

const initialState: AuthState = {
  user: null,
  token: null,
  status: "loading",
  error: null,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "AUTH_START":
      return {
        ...state,
        status: "loading",
        error: null,
      }
    case "AUTH_SUCCESS":
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        status: "authenticated",
        error: null,
      }
    case "SET_TOKEN":
      return {
        ...state,
        token: action.payload.token,
        status: state.user ? "authenticated" : state.status,
      }
    case "AUTH_FAILURE":
      return {
        user: null,
        token: null,
        status: "unauthenticated",
        error: action.payload.error,
      }
    case "AUTH_LOGOUT":
      return {
        user: null,
        token: null,
        status: "unauthenticated",
        error: null,
      }
    default:
      return state
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)
  const isInitializedRef = useRef(false)
  const inFlightRefreshRef = useRef<Promise<boolean> | null>(null)

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } catch {
      // Ignore network errors on logout
    } finally {
      setAccessToken(null)
      dispatch({ type: "AUTH_LOGOUT" })
    }
  }, [])

  const refreshSession = useCallback(async (): Promise<boolean> => {
    if (inFlightRefreshRef.current) {
      return inFlightRefreshRef.current
    }

    const refreshPromise = (async () => {
      try {
        const refreshRes = await authService.refreshToken()
        const newToken = refreshRes.data.access
        setAccessToken(newToken)

        const userRes = await authService.getCurrentUser()
        dispatch({
          type: "AUTH_SUCCESS",
          payload: {
            user: userRes.data,
            token: newToken,
          },
        })
        return true
      } catch {
        setAccessToken(null)
        dispatch({ type: "AUTH_LOGOUT" })
        return false
      } finally {
        inFlightRefreshRef.current = null
      }
    })()

    inFlightRefreshRef.current = refreshPromise
    return refreshPromise
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: "AUTH_START" })
    try {
      const response = await authService.login(credentials)
      const { access, user } = response.data
      setAccessToken(access)
      dispatch({
        type: "AUTH_SUCCESS",
        payload: { user, token: access },
      })
    } catch (err) {
      setAccessToken(null)
      const apiError = err as ApiError
      const errorMessage = apiError.message || "Failed to log in"
      dispatch({
        type: "AUTH_FAILURE",
        payload: { error: errorMessage },
      })
      throw err
    }
  }, [])

  useEffect(() => {
    registerUnauthorizedHandler(() => {
      setAccessToken(null)
      dispatch({ type: "AUTH_LOGOUT" })
    })

    registerTokenRefreshedHandler((newToken) => {
      dispatch({ type: "SET_TOKEN", payload: { token: newToken } })
    })
  }, [])

  useEffect(() => {
    if (!isInitializedRef.current) {
      isInitializedRef.current = true
      refreshSession()
    }
  }, [refreshSession])

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user: state.user,
      token: state.token,
      status: state.status,
      isAuthenticated: state.status === "authenticated",
      isLoading: state.status === "loading",
      error: state.error,
      login,
      logout,
      refreshSession,
    }),
    [
      state.user,
      state.token,
      state.status,
      state.error,
      login,
      logout,
      refreshSession,
    ],
  )

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  )
}

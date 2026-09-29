import { createContext, useContext } from "react"
import type { AuthState, LoginCredentials, User } from "@/types"

export interface AuthContextValue {
  user: User | null
  token: string | null
  status: AuthState["status"]
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshSession: () => Promise<boolean>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider")
  }
  return context
}

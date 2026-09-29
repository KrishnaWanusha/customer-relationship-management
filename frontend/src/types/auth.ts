export type UserRole = "ADMIN" | "MANAGER" | "STAFF"

export interface OrganizationSimple {
  id: string
  name: string
  slug: string
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  organization: OrganizationSimple | null
  can_delete: boolean
  can_view_activity_logs: boolean
  is_active: boolean
  created_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface LoginResponseData {
  access: string
  user: User
}

export interface RefreshResponseData {
  access: string
}

export type AuthStatus =
  | "idle"
  | "loading"
  | "authenticated"
  | "unauthenticated"

export interface AuthState {
  user: User | null
  token: string | null
  status: AuthStatus
  error: string | null
  sessionExpired: boolean
}

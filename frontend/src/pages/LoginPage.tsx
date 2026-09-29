import React, { useState, useCallback } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "@/hooks"
import {
  Button,
  Input,
  Alert,
  AlertTitle,
  AlertDescription,
} from "@/components"
import { Lock, Mail, AlertCircle, Loader2 } from "lucide-react"
import type { ApiError } from "@/types"

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function LoginPage() {
  const { login, sessionExpired: authSessionExpired } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ||
    "/dashboard"
  const isSessionExpired =
    Boolean((location.state as { reason?: string })?.reason === "expired") ||
    authSessionExpired

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    password?: string
  }>({})

  const validate = useCallback((): boolean => {
    const errors: { email?: string; password?: string } = {}

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      errors.email = "Email address is required."
    } else if (!EMAIL_REGEX.test(trimmedEmail)) {
      errors.email = "Please enter a valid email address."
    }

    if (!password) {
      errors.password = "Password is required."
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }, [email, password])

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setGeneralError(null)

      if (!validate()) {
        return
      }

      setIsLoading(true)
      try {
        await login({ email: email.trim(), password })
        navigate(from, { replace: true })
      } catch (err: unknown) {
        const apiError = err as ApiError
        const backendErrors = apiError.errors

        const newFieldErrors: { email?: string; password?: string } = {}
        if (backendErrors?.email?.length) {
          newFieldErrors.email = backendErrors.email[0]
        }
        if (backendErrors?.password?.length) {
          newFieldErrors.password = backendErrors.password[0]
        }

        setFieldErrors(newFieldErrors)

        const nonFieldMsg =
          backendErrors?.non_field_errors?.[0] ||
          apiError.message ||
          "Invalid email or password. Please try again."

        setGeneralError(nonFieldMsg)
      } finally {
        setIsLoading(false)
      }
    },
    [validate, login, email, password, navigate, from],
  )

  const handleEmailChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setEmail(e.target.value)
      setFieldErrors((prev) =>
        prev.email ? { ...prev, email: undefined } : prev,
      )
    },
    [],
  )

  const handlePasswordChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setPassword(e.target.value)
      setFieldErrors((prev) =>
        prev.password ? { ...prev, password: undefined } : prev,
      )
    },
    [],
  )

  return (
    <div className="rounded-xl border border-border bg-card p-6 sm:p-8 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-bold tracking-tight text-foreground">
          Sign in to your account
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Enter your organization credentials to access the CRM
        </p>
      </div>

      {isSessionExpired && !generalError && (
        <Alert variant="warning" className="mb-5">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Session Expired</AlertTitle>
          <AlertDescription>
            Your session has expired or is invalid. Please sign in again.
          </AlertDescription>
        </Alert>
      )}

      {generalError && (
        <Alert variant="destructive" className="mb-5">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Authentication Failed</AlertTitle>
          <AlertDescription>{generalError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="email"
            className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1.5"
          >
            Email address
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              id="email"
              type="email"
              autoComplete="email"
              autoFocus
              placeholder="user@example.com"
              className="pl-9"
              value={email}
              onChange={handleEmailChange}
              error={Boolean(fieldErrors.email)}
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? "email-error" : undefined}
            />
          </div>
          {fieldErrors.email && (
            <p
              id="email-error"
              className="text-xs text-destructive mt-1.5 font-medium"
            >
              {fieldErrors.email}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1.5"
          >
            Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              className="pl-9"
              value={password}
              onChange={handlePasswordChange}
              error={Boolean(fieldErrors.password)}
              disabled={isLoading}
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={
                fieldErrors.password ? "password-error" : undefined
              }
            />
          </div>
          {fieldErrors.password && (
            <p
              id="password-error"
              className="text-xs text-destructive mt-1.5 font-medium"
            >
              {fieldErrors.password}
            </p>
          )}
        </div>

        <Button type="submit" className="w-full mt-2" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </Button>
      </form>
    </div>
  )
}

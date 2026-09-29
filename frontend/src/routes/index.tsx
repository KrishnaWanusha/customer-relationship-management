import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout, AuthLayout } from "@/layouts"
import {
  LoginPage,
  DashboardPage,
  CompaniesPage,
  CompanyDetailsPage,
  ContactsPage,
  ActivityLogsPage,
  NotFoundPage,
} from "@/pages"
import { ProtectedRoute } from "./ProtectedRoute"
import { PublicRoute } from "./PublicRoute"

export const router = createBrowserRouter([
  // Public routes (accessible only when unauthenticated or redirects to dashboard)
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          {
            path: "/login",
            element: <LoginPage />,
          },
        ],
      },
    ],
  },

  // Protected application routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            path: "/",
            element: <Navigate to="/dashboard" replace />,
          },
          {
            path: "/dashboard",
            element: <DashboardPage />,
          },
          {
            path: "/companies",
            element: <CompaniesPage />,
          },
          {
            path: "/companies/:id",
            element: <CompanyDetailsPage />,
          },
          {
            path: "/contacts",
            element: <ContactsPage />,
          },
          {
            path: "/activity-logs",
            element: (
              <ProtectedRoute allowedRoles={["ADMIN", "MANAGER"]}>
                <ActivityLogsPage />
              </ProtectedRoute>
            ),
          },
        ],
      },
    ],
  },

  // Fallback 404
  {
    path: "*",
    element: <NotFoundPage />,
  },
])

import { useState, useCallback, useMemo } from "react"
import { Outlet, NavLink, useNavigate } from "react-router-dom"
import {
  LayoutDashboard,
  Building2,
  Users,
  History,
  LogOut,
  Menu,
  X,
  Shield,
} from "lucide-react"
import { useAuth } from "@/hooks"
import { Badge, Button } from "@/components"
import { cn } from "@/utils"

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = useCallback(async () => {
    await logout()
    navigate("/login")
  }, [logout, navigate])

  const handleToggleMobileMenu = useCallback(() => {
    setMobileMenuOpen((prev) => !prev)
  }, [])

  const handleCloseMobileMenu = useCallback(() => {
    setMobileMenuOpen(false)
  }, [])

  const canViewActivityLogs = Boolean(
    user?.can_view_activity_logs ??
      (user?.role === "ADMIN" || user?.role === "MANAGER"),
  )

  const navItems = useMemo(
    () => [
      {
        to: "/dashboard",
        label: "Dashboard",
        icon: LayoutDashboard,
        show: true,
      },
      {
        to: "/companies",
        label: "Companies",
        icon: Building2,
        show: true,
      },
      {
        to: "/contacts",
        label: "Contacts",
        icon: Users,
        show: true,
      },
      {
        to: "/activity-logs",
        label: "Activity Logs",
        icon: History,
        show: canViewActivityLogs,
      },
    ],
    [canViewActivityLogs],
  )

  const visibleNavItems = useMemo(
    () => navItems.filter((item) => item.show),
    [navItems],
  )

  const roleVariant = useMemo(() => {
    switch (user?.role) {
      case "ADMIN":
        return "destructive"
      case "MANAGER":
        return "warning"
      default:
        return "secondary"
    }
  }, [user?.role])

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card">
        {/* Brand & Organization */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-base">
              CRM
            </div>
            <h1 className="text-lg font-bold tracking-tight">Enterprise CRM</h1>
          </div>
          {user?.organization && (
            <div className="flex items-center justify-between gap-1.5 text-xs text-muted-foreground bg-muted/60 px-2.5 py-1.5 rounded-md mt-3">
              <span className="font-semibold text-foreground truncate max-w-[130px]">
                {user.organization.name}
              </span>
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 border-primary/30 text-primary font-medium shrink-0"
              >
                {user.organization.subscription_plan ||
                  user.organization.plan ||
                  "Basic"}
              </Badge>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {visibleNavItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-border bg-card/50">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="truncate min-w-0">
              <p className="text-sm font-semibold truncate text-foreground">
                {user
                  ? `${user.first_name} ${user.last_name}`.trim() || user.email
                  : "User"}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
            <Badge
              variant={roleVariant}
              className="shrink-0 text-[10px] px-1.5 py-0.5"
            >
              <Shield className="h-3 w-3 mr-0.5" />
              {user?.role}
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-center text-xs text-muted-foreground hover:text-destructive"
          >
            <LogOut className="h-3.5 w-3.5 mr-2" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden border-b border-border bg-card px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded bg-primary flex items-center justify-center text-primary-foreground font-bold text-xs">
              CRM
            </div>
            <span className="font-semibold text-sm">Enterprise CRM</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleToggleMobileMenu}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </header>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-border bg-card p-4 space-y-2">
            {visibleNavItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={handleCloseMobileMenu}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted",
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
            })}
            <div className="pt-2 border-t border-border flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {user?.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-destructive text-xs"
              >
                <LogOut className="h-3.5 w-3.5 mr-1" />
                Sign Out
              </Button>
            </div>
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

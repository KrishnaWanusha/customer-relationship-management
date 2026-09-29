import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { Link } from "react-router-dom"
import {
  Building2,
  Plus,
  Search,
  X,
  Edit2,
  Trash2,
  ExternalLink,
  Users,
  CheckCircle,
  AlertCircle,
  RotateCcw,
} from "lucide-react"
import {
  Button,
  Input,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Pagination,
  LoadingState,
  EmptyState,
  ErrorState,
  Alert,
  AlertTitle,
  AlertDescription,
  ConfirmDialog,
  CompanyModal,
} from "@/components"
import { companiesService } from "@/api"
import { useAuth } from "@/hooks"
import { formatDate } from "@/utils"
import type { ApiError, Company, PaginationMeta } from "@/types"

export function CompaniesPage() {
  const { user } = useAuth()

  // Data & Pagination
  const [companies, setCompanies] = useState<Company[]>([])
  const [pagination, setPagination] = useState<PaginationMeta | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [industryFilter, setIndustryFilter] = useState("")
  const [countryFilter, setCountryFilter] = useState("")

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{
    type: "success" | "error"
    message: string
  } | null>(null)

  // Modals & Dialogs
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [companyToDelete, setCompanyToDelete] = useState<Company | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const isFirstSearchRef = useRef(true)

  // Debounce search input
  useEffect(() => {
    if (isFirstSearchRef.current) {
      isFirstSearchRef.current = false
      return
    }
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim())
      setCurrentPage(1)
    }, 350)
    return () => clearTimeout(handler)
  }, [searchQuery])

  // Fetch companies from API
  const fetchCompanies = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await companiesService.getCompanies({
        search: debouncedSearch || undefined,
        industry: industryFilter.trim() || undefined,
        country: countryFilter.trim() || undefined,
        page: currentPage,
      })

      setCompanies(response.data.results)
      setPagination(response.data.pagination)
    } catch (err: unknown) {
      const apiError = err as ApiError
      setError(apiError.message || "Failed to load companies.")
    } finally {
      setIsLoading(false)
    }
  }, [debouncedSearch, industryFilter, countryFilter, currentPage])

  useEffect(() => {
    fetchCompanies()
  }, [fetchCompanies])

  // Handlers for Add & Edit
  const handleOpenCreate = useCallback(() => {
    setSelectedCompany(null)
    setIsModalOpen(true)
  }, [])

  const handleOpenEdit = useCallback((company: Company) => {
    setSelectedCompany(company)
    setIsModalOpen(true)
  }, [])

  const handleModalSuccess = useCallback(
    (savedCompany: Company) => {
      if (selectedCompany) {
        setFeedback({
          type: "success",
          message: `Company "${savedCompany.name}" updated successfully.`,
        })
      } else {
        setFeedback({
          type: "success",
          message: `Company "${savedCompany.name}" created successfully.`,
        })
      }
      fetchCompanies()
    },
    [selectedCompany, fetchCompanies],
  )

  // Handlers for Delete (Soft-Delete)
  const handleDeleteConfirm = useCallback(async () => {
    if (!companyToDelete) return
    setIsDeleting(true)
    try {
      await companiesService.deleteCompany(companyToDelete.id)
      setFeedback({
        type: "success",
        message: `Company "${companyToDelete.name}" was successfully deleted.`,
      })
      setCompanyToDelete(null)
      fetchCompanies()
    } catch (err: unknown) {
      const apiError = err as ApiError
      setFeedback({
        type: "error",
        message: apiError.message || "Failed to delete company.",
      })
    } finally {
      setIsDeleting(false)
    }
  }, [companyToDelete, fetchCompanies])

  const handleResetFilters = useCallback(() => {
    setSearchQuery("")
    setDebouncedSearch("")
    setIndustryFilter("")
    setCountryFilter("")
    setCurrentPage(1)
  }, [])

  const handleClearSearch = useCallback(() => {
    setSearchQuery("")
  }, [])

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value)
    },
    [],
  )

  const handleIndustryChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setIndustryFilter(e.target.value)
      setCurrentPage(1)
    },
    [],
  )

  const handleCountryChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setCountryFilter(e.target.value)
      setCurrentPage(1)
    },
    [],
  )

  const handleDismissFeedback = useCallback(() => {
    setFeedback(null)
  }, [])

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page)
  }, [])

  const handleCloseDeleteDialog = useCallback((open: boolean) => {
    if (!open) {
      setCompanyToDelete(null)
    }
  }, [])

  const hasActiveFilters = useMemo(
    () =>
      Boolean(debouncedSearch || industryFilter.trim() || countryFilter.trim()),
    [debouncedSearch, industryFilter, countryFilter],
  )

  return (
    <div className="space-y-6">
      {/* Page Title & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Companies
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your organization&apos;s client and partner accounts
          </p>
        </div>
        <Button onClick={handleOpenCreate} size="sm">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Company
        </Button>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <Alert
          variant={feedback.type === "success" ? "success" : "destructive"}
          className="relative"
        >
          {feedback.type === "success" ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          <AlertTitle>
            {feedback.type === "success" ? "Success" : "Error"}
          </AlertTitle>
          <AlertDescription>{feedback.message}</AlertDescription>
          <button
            onClick={handleDismissFeedback}
            className="absolute top-3 right-3 text-muted-foreground hover:text-foreground"
            aria-label="Dismiss feedback"
          >
            <X className="h-4 w-4" />
          </button>
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-card p-3 rounded-lg border border-border shadow-sm">
        <div className="flex-1 flex flex-col sm:flex-row gap-2">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search companies by name, industry, or country..."
              className="pl-9 pr-8"
              value={searchQuery}
              onChange={handleSearchChange}
            />
            {searchQuery && (
              <button
                onClick={handleClearSearch}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Industry Filter */}
          <div className="w-full sm:w-44">
            <Input
              placeholder="Filter by industry"
              value={industryFilter}
              onChange={handleIndustryChange}
            />
          </div>

          {/* Country Filter */}
          <div className="w-full sm:w-36">
            <Input
              placeholder="Filter by country"
              value={countryFilter}
              onChange={handleCountryChange}
            />
          </div>
        </div>

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetFilters}
            className="text-xs text-muted-foreground hover:text-foreground whitespace-nowrap self-end sm:self-auto"
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset Filters
          </Button>
        )}
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <LoadingState message="Loading companies..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchCompanies} />
      ) : companies.length === 0 ? (
        hasActiveFilters ? (
          <EmptyState
            icon={<Search className="h-8 w-8 text-muted-foreground" />}
            title="No matching companies"
            description="No companies match the specified search query or filters."
            actionLabel="Clear Filters"
            onAction={handleResetFilters}
          />
        ) : (
          <EmptyState
            icon={<Building2 className="h-8 w-8 text-muted-foreground" />}
            title="No companies registered yet"
            description="Start building your client portfolio by creating your organization's first company."
            actionLabel="Add Company"
            onAction={handleOpenCreate}
          />
        )
      ) : (
        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12"></TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Contacts</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <TableRow key={company.id} className="hover:bg-muted/40">
                  {/* Logo / Avatar Column */}
                  <TableCell className="pr-0">
                    <div className="h-9 w-9 rounded-md border border-border bg-muted/60 flex items-center justify-center overflow-hidden shrink-0">
                      {company.logo_url ? (
                        <img
                          src={company.logo_url}
                          alt={`${company.name} logo`}
                          className="h-full w-full object-contain p-0.5"
                          loading="lazy"
                        />
                      ) : (
                        <span className="font-bold text-xs text-primary">
                          {company.name.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                  </TableCell>

                  {/* Company Name & Link */}
                  <TableCell>
                    <Link
                      to={`/companies/${company.id}`}
                      className="font-semibold text-foreground hover:text-primary hover:underline transition-colors flex items-center gap-1.5"
                    >
                      {company.name}
                      <ExternalLink className="h-3 w-3 opacity-40" />
                    </Link>
                    {company.website && (
                      <span className="text-xs text-muted-foreground block truncate max-w-[200px]">
                        {company.website.replace(/^https?:\/\//, "")}
                      </span>
                    )}
                  </TableCell>

                  {/* Industry */}
                  <TableCell>
                    {company.industry ? (
                      <Badge variant="outline" className="font-normal text-xs">
                        {company.industry}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </TableCell>

                  {/* Country */}
                  <TableCell>
                    {company.country ? (
                      <span className="font-mono text-xs uppercase bg-muted px-2 py-0.5 rounded text-foreground font-medium">
                        {company.country}
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </TableCell>

                  {/* Contacts Count */}
                  <TableCell>
                    <Link
                      to={`/companies/${company.id}`}
                      className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground font-medium"
                    >
                      <Users className="h-3.5 w-3.5" />
                      <span>{company.contacts_count || 0}</span>
                    </Link>
                  </TableCell>

                  {/* Created Date */}
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(company.created_at)}
                  </TableCell>

                  {/* Actions Column */}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleOpenEdit(company)}
                        aria-label={`Edit ${company.name}`}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </Button>

                      {user?.can_delete && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => setCompanyToDelete(company)}
                          aria-label={`Delete ${company.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination Controls */}
          {pagination && pagination.total_pages > 1 && (
            <div className="px-4 border-t border-border">
              <Pagination
                currentPage={pagination.current_page}
                totalPages={pagination.total_pages}
                totalCount={pagination.count}
                pageSize={pagination.page_size}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Company Modal */}
      <CompanyModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        company={selectedCompany}
        onSuccess={handleModalSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={Boolean(companyToDelete)}
        onOpenChange={handleCloseDeleteDialog}
        title="Delete Company"
        description={`Are you sure you want to delete "${companyToDelete?.name}"? This company and its associated contacts will be soft-deleted and removed from active CRM views.`}
        confirmText="Delete Company"
        isLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  )
}

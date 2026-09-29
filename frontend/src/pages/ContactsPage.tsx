import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { Link } from "react-router-dom"
import {
  Users,
  Search,
  X,
  Edit2,
  Trash2,
  Mail,
  Phone,
  Building2,
  CheckCircle,
  AlertCircle,
  Plus,
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
  ContactModal,
} from "@/components"
import { contactsService, companiesService } from "@/api"
import { useAuth } from "@/hooks"
import { formatDate } from "@/utils"
import type { ApiError, Contact, Company, PaginationMeta } from "@/types"

export function ContactsPage() {
  const { user } = useAuth()

  // Contacts Data & Pagination
  const [contacts, setContacts] = useState<Contact[]>([])
  const [pagination, setPagination] = useState<PaginationMeta | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Search & Filtering
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")

  // Companies
  const [companies, setCompanies] = useState<Company[]>([])
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("")

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{
    type: "success" | "error"
    message: string
  } | null>(null)

  // Modals & Confirmation
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [contactToDelete, setContactToDelete] = useState<Contact | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const isFirstSearchRef = useRef(true)

  // Debounce search
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

  // Fetch Companies for creation dropdown
  useEffect(() => {
    companiesService
      .getCompanies({ page_size: 100 })
      .then((res) => {
        setCompanies(res.data.results)
        if (res.data.results.length > 0 && !selectedCompanyId) {
          setSelectedCompanyId(res.data.results[0].id)
        }
      })
      .catch(() => {
        // Silently catch company list error
      })
  }, [selectedCompanyId])

  // Fetch Contacts
  const fetchContacts = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await contactsService.getContacts({
        search: debouncedSearch || undefined,
        page: currentPage,
      })
      setContacts(response.data.results)
      setPagination(response.data.pagination)
    } catch (err: unknown) {
      const apiError = err as ApiError
      setError(apiError.message || "Failed to load contacts.")
    } finally {
      setIsLoading(false)
    }
  }, [debouncedSearch, currentPage])

  useEffect(() => {
    fetchContacts()
  }, [fetchContacts])

  // Handlers
  const handleOpenAdd = useCallback(() => {
    if (companies.length === 0) {
      setFeedback({
        type: "error",
        message: "You must create at least one company before adding contacts.",
      })
      return
    }
    setSelectedContact(null)
    setIsModalOpen(true)
  }, [companies.length])

  const handleOpenEdit = useCallback((contact: Contact) => {
    setSelectedContact(contact)
    setSelectedCompanyId(contact.company)
    setIsModalOpen(true)
  }, [])

  const handleModalSuccess = useCallback(
    (savedContact: Contact) => {
      setFeedback({
        type: "success",
        message: selectedContact
          ? `Contact "${savedContact.full_name}" updated successfully.`
          : `Contact "${savedContact.full_name}" created successfully.`,
      })
      fetchContacts()
    },
    [selectedContact, fetchContacts],
  )

  const handleDeleteConfirm = useCallback(async () => {
    if (!contactToDelete) return
    setIsDeleting(true)
    try {
      await contactsService.deleteContact(contactToDelete.id)
      setFeedback({
        type: "success",
        message: `Contact "${contactToDelete.full_name}" was successfully removed.`,
      })
      setContactToDelete(null)
      fetchContacts()
    } catch (err: unknown) {
      const apiError = err as ApiError
      setFeedback({
        type: "error",
        message: apiError.message || "Failed to delete contact.",
      })
    } finally {
      setIsDeleting(false)
    }
  }, [contactToDelete, fetchContacts])

  const handleClearSearch = useCallback(() => {
    setSearchQuery("")
  }, [])

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(e.target.value)
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
      setContactToDelete(null)
    }
  }, [])

  const handleCloseModal = useCallback((open: boolean) => {
    setIsModalOpen(open)
  }, [])

  const selectedCompanyName = useMemo(
    () =>
      companies.find((c) => c.id === selectedCompanyId)?.name ||
      selectedContact?.company_name,
    [companies, selectedCompanyId, selectedContact?.company_name],
  )

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Contacts
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Directory of all client contacts and representatives across your
            organization
          </p>
        </div>
        <Button onClick={handleOpenAdd} size="sm">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Contact
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

      {/* Search Bar */}
      <div className="flex items-center gap-3 bg-card p-3 rounded-lg border border-border shadow-sm max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search contacts by name, email, company, or role..."
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
        {searchQuery && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearSearch}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset
          </Button>
        )}
      </div>

      {/* Contacts Content */}
      {isLoading ? (
        <LoadingState message="Loading contacts directory..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchContacts} />
      ) : contacts.length === 0 ? (
        debouncedSearch ? (
          <EmptyState
            icon={<Search className="h-8 w-8 text-muted-foreground" />}
            title="No matching contacts"
            description={`No contacts found matching "${debouncedSearch}".`}
            actionLabel="Clear Search"
            onAction={handleClearSearch}
          />
        ) : (
          <EmptyState
            icon={<Users className="h-8 w-8 text-muted-foreground" />}
            title="No contacts added yet"
            description="Start building relationships by adding contacts to your client companies."
            actionLabel="Add Contact"
            onAction={handleOpenAdd}
          />
        )
      ) : (
        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contact Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Added</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {contacts.map((contact) => (
                <TableRow key={contact.id} className="hover:bg-muted/40">
                  <TableCell className="font-semibold text-foreground">
                    {contact.full_name}
                  </TableCell>

                  <TableCell>
                    <a
                      href={`mailto:${contact.email}`}
                      className="text-primary hover:underline inline-flex items-center gap-1 text-xs"
                    >
                      <Mail className="h-3 w-3" />
                      {contact.email}
                    </a>
                  </TableCell>

                  <TableCell className="text-xs text-muted-foreground">
                    {contact.phone ? (
                      <a
                        href={`tel:${contact.phone}`}
                        className="hover:text-foreground inline-flex items-center gap-1"
                      >
                        <Phone className="h-3 w-3" />
                        {contact.phone}
                      </a>
                    ) : (
                      "—"
                    )}
                  </TableCell>

                  <TableCell>
                    <Link
                      to={`/companies/${contact.company}`}
                      className="text-foreground hover:text-primary hover:underline inline-flex items-center gap-1 text-xs font-medium"
                    >
                      <Building2 className="h-3 w-3 text-muted-foreground" />
                      {contact.company_name}
                    </Link>
                  </TableCell>

                  <TableCell>
                    {contact.role ? (
                      <Badge variant="outline" className="font-normal text-xs">
                        {contact.role}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </TableCell>

                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(contact.created_at)}
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        onClick={() => handleOpenEdit(contact)}
                        aria-label={`Edit ${contact.full_name}`}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </Button>

                      {user?.can_delete && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => setContactToDelete(contact)}
                          aria-label={`Delete ${contact.full_name}`}
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

      {/* Contact Modal */}
      {selectedCompanyId && (
        <ContactModal
          open={isModalOpen}
          onOpenChange={handleCloseModal}
          companyId={selectedCompanyId}
          companyName={selectedCompanyName}
          contact={selectedContact}
          onSuccess={handleModalSuccess}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={Boolean(contactToDelete)}
        onOpenChange={handleCloseDeleteDialog}
        title="Delete Contact"
        description={`Are you sure you want to delete "${contactToDelete?.full_name}"? This contact will be soft-deleted.`}
        confirmText="Delete Contact"
        isLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  )
}

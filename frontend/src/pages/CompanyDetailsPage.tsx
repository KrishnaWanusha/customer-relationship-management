import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import {
  ArrowLeft,
  Globe,
  Phone,
  MapPin,
  Calendar,
  Edit2,
  Trash2,
  Plus,
  Search,
  X,
  Mail,
  Users,
  CheckCircle,
  AlertCircle,
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
  ContactModal,
} from "@/components"
import { companiesService, contactsService } from "@/api"
import { useAuth } from "@/hooks"
import { formatDate } from "@/utils"
import type { ApiError, Company, Contact, PaginationMeta } from "@/types"

export function CompanyDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  // Company State
  const [company, setCompany] = useState<Company | null>(null)
  const [isLoadingCompany, setIsLoadingCompany] = useState(true)
  const [companyError, setCompanyError] = useState<string | null>(null)
  const [isEditCompanyOpen, setIsEditCompanyOpen] = useState(false)
  const [isDeleteCompanyOpen, setIsDeleteCompanyOpen] = useState(false)
  const [isDeletingCompany, setIsDeletingCompany] = useState(false)

  // Contacts State
  const [contacts, setContacts] = useState<Contact[]>([])
  const [contactsPagination, setContactsPagination] =
    useState<PaginationMeta | null>(null)
  const [contactsPage, setContactsPage] = useState(1)
  const [contactSearch, setContactSearch] = useState("")
  const [debouncedContactSearch, setDebouncedContactSearch] = useState("")
  const [isLoadingContacts, setIsLoadingContacts] = useState(true)
  const [contactsError, setContactsError] = useState<string | null>(null)

  // Contact Modal & Delete State
  const [isContactModalOpen, setIsContactModalOpen] = useState(false)
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [contactToDelete, setContactToDelete] = useState<Contact | null>(null)
  const [isDeletingContact, setIsDeletingContact] = useState(false)

  // Feedback State
  const [feedback, setFeedback] = useState<{
    type: "success" | "error"
    message: string
  } | null>(null)

  const isFirstContactSearchRef = useRef(true)

  // Debounce contact search
  useEffect(() => {
    if (isFirstContactSearchRef.current) {
      isFirstContactSearchRef.current = false
      return
    }
    const handler = setTimeout(() => {
      setDebouncedContactSearch(contactSearch.trim())
      setContactsPage(1)
    }, 350)
    return () => clearTimeout(handler)
  }, [contactSearch])

  // Fetch Company Details
  const fetchCompany = useCallback(async () => {
    if (!id) return
    setIsLoadingCompany(true)
    setCompanyError(null)
    try {
      const res = await companiesService.getCompany(id)
      setCompany(res.data)
    } catch (err: unknown) {
      const apiError = err as ApiError
      setCompanyError(apiError.message || "Failed to load company details.")
    } finally {
      setIsLoadingCompany(false)
    }
  }, [id])

  const fetchContacts = useCallback(async () => {
    if (!id) return
    setIsLoadingContacts(true)
    setContactsError(null)
    try {
      const res = await contactsService.getContacts({
        company: id,
        search: debouncedContactSearch || undefined,
        page: contactsPage,
      })
      setContacts(res.data.results)
      setContactsPagination(res.data.pagination)
    } catch (err: unknown) {
      const apiError = err as ApiError
      setContactsError(apiError.message || "Failed to load company contacts.")
    } finally {
      setIsLoadingContacts(false)
    }
  }, [id, debouncedContactSearch, contactsPage])

  useEffect(() => {
    fetchCompany()
  }, [fetchCompany])

  useEffect(() => {
    fetchContacts()
  }, [fetchContacts])

  // Company Actions
  const handleCompanyUpdateSuccess = useCallback((updatedCompany: Company) => {
    setCompany(updatedCompany)
    setFeedback({
      type: "success",
      message: "Company details updated successfully.",
    })
  }, [])

  const handleDeleteCompanyConfirm = useCallback(async () => {
    if (!company) return
    setIsDeletingCompany(true)
    try {
      await companiesService.deleteCompany(company.id)
      navigate("/companies", { replace: true })
    } catch (err: unknown) {
      const apiError = err as ApiError
      setFeedback({
        type: "error",
        message: apiError.message || "Failed to delete company.",
      })
      setIsDeleteCompanyOpen(false)
    } finally {
      setIsDeletingCompany(false)
    }
  }, [company, navigate])

  // Contact Actions
  const handleOpenAddContact = useCallback(() => {
    setSelectedContact(null)
    setIsContactModalOpen(true)
  }, [])

  const handleOpenEditContact = useCallback((contact: Contact) => {
    setSelectedContact(contact)
    setIsContactModalOpen(true)
  }, [])

  const handleContactModalSuccess = useCallback(
    (savedContact: Contact) => {
      setFeedback({
        type: "success",
        message: selectedContact
          ? `Contact "${savedContact.full_name}" updated successfully.`
          : `Contact "${savedContact.full_name}" added successfully.`,
      })
      fetchContacts()
      fetchCompany()
    },
    [selectedContact, fetchContacts, fetchCompany],
  )

  const handleDeleteContactConfirm = useCallback(async () => {
    if (!contactToDelete) return
    setIsDeletingContact(true)
    try {
      await contactsService.deleteContact(contactToDelete.id)
      setFeedback({
        type: "success",
        message: `Contact "${contactToDelete.full_name}" was successfully removed.`,
      })
      setContactToDelete(null)
      fetchContacts()
      fetchCompany()
    } catch (err: unknown) {
      const apiError = err as ApiError
      setFeedback({
        type: "error",
        message: apiError.message || "Failed to delete contact.",
      })
    } finally {
      setIsDeletingContact(false)
    }
  }, [contactToDelete, fetchContacts, fetchCompany])

  const handleDismissFeedback = useCallback(() => {
    setFeedback(null)
  }, [])

  const handleClearContactSearch = useCallback(() => {
    setContactSearch("")
  }, [])

  const handleContactSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setContactSearch(e.target.value)
    },
    [],
  )

  const handleContactsPageChange = useCallback((page: number) => {
    setContactsPage(page)
  }, [])

  const handleOpenEditCompany = useCallback(() => {
    setIsEditCompanyOpen(true)
  }, [])

  const handleOpenDeleteCompany = useCallback(() => {
    setIsDeleteCompanyOpen(true)
  }, [])

  const handleCloseDeleteCompanyDialog = useCallback((open: boolean) => {
    setIsDeleteCompanyOpen(open)
  }, [])

  const handleCloseDeleteContactDialog = useCallback((open: boolean) => {
    if (!open) {
      setContactToDelete(null)
    }
  }, [])

  const normalizedWebsiteUrl = useMemo(() => {
    const rawWebsite = company?.website
    if (!rawWebsite) return null
    return rawWebsite.startsWith("http") ? rawWebsite : `https://${rawWebsite}`
  }, [company?.website])

  if (isLoadingCompany) {
    return <LoadingState message="Loading company profile..." />
  }

  if (companyError || !company) {
    return (
      <div className="space-y-4">
        <Link
          to="/companies"
          className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Companies
        </Link>
        <ErrorState
          title="Company Not Found"
          message={
            companyError ||
            "The requested company does not exist or has been removed."
          }
          onRetry={fetchCompany}
        />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/companies"
          className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Companies
        </Link>
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

      {/* Company Profile Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            {/* Logo Avatar */}
            <div className="h-16 w-16 rounded-xl border border-border bg-muted/60 flex items-center justify-center overflow-hidden shrink-0 shadow-sm">
              {company.logo_url ? (
                <img
                  src={company.logo_url}
                  alt={`${company.name} logo`}
                  className="h-full w-full object-contain p-1"
                />
              ) : (
                <span className="font-bold text-xl text-primary">
                  {company.name.charAt(0).toUpperCase()}
                </span>
              )}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                  {company.name}
                </h1>
                {company.industry && (
                  <Badge variant="secondary">{company.industry}</Badge>
                )}
                {company.country && (
                  <span className="font-mono text-xs uppercase bg-muted px-2 py-0.5 rounded text-foreground font-medium">
                    {company.country}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-muted-foreground/80" />
                  Added {formatDate(company.created_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5 text-muted-foreground/80" />
                  {company.contacts_count || contacts.length} contacts
                </span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-start">
            <Button variant="outline" size="sm" onClick={handleOpenEditCompany}>
              <Edit2 className="h-3.5 w-3.5 mr-1.5" />
              Edit Company
            </Button>

            {user?.can_delete && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenDeleteCompany}
                className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                Delete
              </Button>
            )}
          </div>
        </div>

        {/* Detailed Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-6 border-t border-border text-sm">
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Website
            </span>
            {normalizedWebsiteUrl ? (
              <a
                href={normalizedWebsiteUrl}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline flex items-center gap-1 font-medium truncate"
              >
                <Globe className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{company.website}</span>
              </a>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </div>

          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Phone
            </span>
            {company.phone ? (
              <a
                href={`tel:${company.phone}`}
                className="text-foreground hover:text-primary flex items-center gap-1 font-medium truncate"
              >
                <Phone className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{company.phone}</span>
              </a>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </div>

          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Address
            </span>
            {company.address ? (
              <span className="text-foreground flex items-center gap-1 font-medium truncate">
                <MapPin className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{company.address}</span>
              </span>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </div>
        </div>
      </div>

      {/* Nested Contacts Management Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Contacts
              </h2>
              <Badge variant="secondary" className="font-semibold">
                {contactsPagination?.count ?? contacts.length}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              People associated with {company.name}
            </p>
          </div>

          <Button size="sm" onClick={handleOpenAddContact}>
            <Plus className="h-4 w-4 mr-1.5" />
            Add Contact
          </Button>
        </div>

        {/* Contacts Filter / Search */}
        <div className="flex items-center gap-2 bg-card p-2 rounded-lg border border-border max-w-sm">
          <Search className="h-4 w-4 text-muted-foreground ml-1" />
          <Input
            placeholder="Search contacts by name, email, or role..."
            value={contactSearch}
            onChange={handleContactSearchChange}
            className="border-0 shadow-none focus-visible:ring-0 h-8"
          />
          {contactSearch && (
            <button
              onClick={handleClearContactSearch}
              className="text-muted-foreground hover:text-foreground mr-1"
              aria-label="Clear contact search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Contacts Table / Empty / Loading */}
        {isLoadingContacts ? (
          <LoadingState message="Loading company contacts..." />
        ) : contactsError ? (
          <ErrorState message={contactsError} onRetry={fetchContacts} />
        ) : contacts.length === 0 ? (
          contactSearch ? (
            <EmptyState
              icon={<Search className="h-7 w-7 text-muted-foreground" />}
              title="No contacts found"
              description={`No contacts match "${contactSearch}".`}
              actionLabel="Clear Search"
              onAction={handleClearContactSearch}
            />
          ) : (
            <EmptyState
              icon={<Users className="h-7 w-7 text-muted-foreground" />}
              title="No contacts added yet"
              description={`Add key people and business contacts for ${company.name}.`}
              actionLabel="Add Contact"
              onAction={handleOpenAddContact}
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
                      {contact.role ? (
                        <Badge
                          variant="outline"
                          className="font-normal text-xs"
                        >
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
                          onClick={() => handleOpenEditContact(contact)}
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

            {/* Contacts Pagination */}
            {contactsPagination && contactsPagination.total_pages > 1 && (
              <div className="px-4 border-t border-border">
                <Pagination
                  currentPage={contactsPagination.current_page}
                  totalPages={contactsPagination.total_pages}
                  totalCount={contactsPagination.count}
                  pageSize={contactsPagination.page_size}
                  onPageChange={handleContactsPageChange}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Edit Company Modal */}
      <CompanyModal
        open={isEditCompanyOpen}
        onOpenChange={setIsEditCompanyOpen}
        company={company}
        onSuccess={handleCompanyUpdateSuccess}
      />

      {/* Delete Company Confirm Dialog */}
      <ConfirmDialog
        open={isDeleteCompanyOpen}
        onOpenChange={handleCloseDeleteCompanyDialog}
        title="Delete Company"
        description={`Are you sure you want to delete "${company.name}"? This company and all its contacts will be soft-deleted.`}
        confirmText="Delete Company"
        isLoading={isDeletingCompany}
        onConfirm={handleDeleteCompanyConfirm}
      />

      {/* Add / Edit Contact Modal */}
      <ContactModal
        open={isContactModalOpen}
        onOpenChange={setIsContactModalOpen}
        companyId={company.id}
        companyName={company.name}
        contact={selectedContact}
        onSuccess={handleContactModalSuccess}
      />

      {/* Delete Contact Confirm Dialog */}
      <ConfirmDialog
        open={Boolean(contactToDelete)}
        onOpenChange={handleCloseDeleteContactDialog}
        title="Delete Contact"
        description={`Are you sure you want to delete "${contactToDelete?.full_name}"? The contact will be soft-deleted.`}
        confirmText="Delete Contact"
        isLoading={isDeletingContact}
        onConfirm={handleDeleteContactConfirm}
      />
    </div>
  )
}

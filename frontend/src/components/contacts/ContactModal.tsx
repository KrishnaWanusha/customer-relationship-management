import React, { useState, useEffect, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
  Alert,
  AlertTitle,
  AlertDescription,
} from "@/components"
import { contactsService } from "@/api"
import type { ApiError, Contact } from "@/types"
import { Loader2, User, AlertCircle } from "lucide-react"

export interface ContactModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  companyId: string
  companyName?: string
  contact?: Contact | null
  onSuccess: (contact: Contact) => void
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function ContactModal({
  open,
  onOpenChange,
  companyId,
  companyName,
  contact,
  onSuccess,
}: ContactModalProps) {
  const isEdit = Boolean(contact)

  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [role, setRole] = useState("")

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (open) {
      if (contact) {
        setFullName(contact.full_name || "")
        setEmail(contact.email || "")
        setPhone(contact.phone || "")
        setRole(contact.role || "")
      } else {
        setFullName("")
        setEmail("")
        setPhone("")
        setRole("")
      }
      setGeneralError(null)
      setFieldErrors({})
    }
  }, [open, contact])

  const validate = useCallback((): boolean => {
    const errors: Record<string, string> = {}
    if (!fullName.trim()) {
      errors.full_name = "Full name is required."
    }
    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      errors.email = "Email address is required."
    } else if (!EMAIL_REGEX.test(trimmedEmail)) {
      errors.email = "Please enter a valid email address."
    }

    if (phone.trim()) {
      const digitsOnly = phone.replace(/\D/g, "")
      if (digitsOnly.length < 8 || digitsOnly.length > 15) {
        errors.phone = "Phone number must contain between 8 and 15 digits."
      }
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }, [fullName, email, phone])

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setGeneralError(null)

      if (!validate()) return

      setIsSubmitting(true)
      try {
        const payload = {
          company: companyId,
          full_name: fullName.trim(),
          email: email.trim(),
          phone: phone.trim() || undefined,
          role: role.trim() || undefined,
        }

        let savedContact: Contact
        if (isEdit && contact) {
          const res = await contactsService.updateContact(contact.id, payload)
          savedContact = res.data
        } else {
          const res = await contactsService.createContact(payload)
          savedContact = res.data
        }

        onSuccess(savedContact)
        onOpenChange(false)
      } catch (err: unknown) {
        const apiError = err as ApiError
        const backendErrors = apiError.errors

        const newFieldErrors: Record<string, string> = {}
        if (backendErrors) {
          for (const [key, msgs] of Object.entries(backendErrors)) {
            if (Array.isArray(msgs) && msgs.length > 0) {
              newFieldErrors[key] = msgs[0]
            }
          }
        }
        setFieldErrors(newFieldErrors)

        const generalMsg =
          backendErrors?.non_field_errors?.[0] ||
          apiError.message ||
          `Failed to ${isEdit ? "update" : "create"} contact.`
        setGeneralError(generalMsg)
      } finally {
        setIsSubmitting(false)
      }
    },
    [
      validate,
      companyId,
      fullName,
      email,
      phone,
      role,
      isEdit,
      contact,
      onSuccess,
      onOpenChange,
    ],
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-md"
        onClose={() => !isSubmitting && onOpenChange(false)}
      >
        <DialogHeader>
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            <DialogTitle>
              {isEdit ? "Edit Contact" : "Add New Contact"}
            </DialogTitle>
          </div>
          <DialogDescription>
            {isEdit
              ? "Update contact details."
              : `Add a contact person for ${companyName || "this company"}.`}
          </DialogDescription>
        </DialogHeader>

        {generalError && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{generalError}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 mt-4" noValidate>
          <div>
            <label
              htmlFor="contact-fullname"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Full Name <span className="text-destructive">*</span>
            </label>
            <Input
              id="contact-fullname"
              placeholder="e.g. Jane Doe"
              value={fullName}
              onChange={(e) => {
                setFullName(e.target.value)
                if (fieldErrors.full_name) {
                  setFieldErrors((prev) => ({ ...prev, full_name: "" }))
                }
              }}
              error={Boolean(fieldErrors.full_name)}
              disabled={isSubmitting}
              required
            />
            {fieldErrors.full_name && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.full_name}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="contact-email"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Email Address <span className="text-destructive">*</span>
            </label>
            <Input
              id="contact-email"
              type="email"
              placeholder="e.g. jane.doe@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (fieldErrors.email) {
                  setFieldErrors((prev) => ({ ...prev, email: "" }))
                }
              }}
              error={Boolean(fieldErrors.email)}
              disabled={isSubmitting}
              required
            />
            {fieldErrors.email && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.email}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="contact-phone"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Phone Number
            </label>
            <Input
              id="contact-phone"
              placeholder="e.g. +1 555-0199"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value)
                if (fieldErrors.phone) {
                  setFieldErrors((prev) => ({ ...prev, phone: "" }))
                }
              }}
              error={Boolean(fieldErrors.phone)}
              disabled={isSubmitting}
            />
            {fieldErrors.phone && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.phone}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="contact-role"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Role / Position
            </label>
            <Input
              id="contact-role"
              placeholder="e.g. VP of Operations"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={isSubmitting}
            />
            {fieldErrors.role && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.role}
              </p>
            )}
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  {isEdit ? "Saving Contact..." : "Adding Contact..."}
                </>
              ) : (
                <>{isEdit ? "Save Contact" : "Add Contact"}</>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

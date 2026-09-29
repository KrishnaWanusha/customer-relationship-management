import React, { useState, useEffect, useRef, useCallback } from "react"
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
import { companiesService } from "@/api"
import type { ApiError, Company } from "@/types"
import { Loader2, Upload, X, Building2, AlertCircle } from "lucide-react"

export interface CompanyModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company?: Company | null
  onSuccess: (company: Company) => void
}

const ALLOWED_LOGO_TYPES = ["image/jpeg", "image/png", "image/webp"]
const MAX_LOGO_SIZE_BYTES = 2 * 1024 * 1024 // 2MB

export function CompanyModal({
  open,
  onOpenChange,
  company,
  onSuccess,
}: CompanyModalProps) {
  const isEdit = Boolean(company)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [name, setName] = useState("")
  const [industry, setIndustry] = useState("")
  const [country, setCountry] = useState("")
  const [website, setWebsite] = useState("")
  const [phone, setPhone] = useState("")
  const [address, setAddress] = useState("")
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(null)

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (open) {
      if (company) {
        setName(company.name || "")
        setIndustry(company.industry || "")
        setCountry(company.country || "")
        setWebsite(company.website || "")
        setPhone(company.phone || "")
        setAddress(company.address || "")
        setLogoPreview(company.logo_url || null)
      } else {
        setName("")
        setIndustry("")
        setCountry("")
        setWebsite("")
        setPhone("")
        setAddress("")
        setLogoPreview(null)
      }
      setLogoFile(null)
      setGeneralError(null)
      setFieldErrors({})
    }
  }, [open, company])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return

      if (!ALLOWED_LOGO_TYPES.includes(file.type)) {
        setFieldErrors((prev) => ({
          ...prev,
          logo: "Logo must be a JPEG, PNG, or WebP image.",
        }))
        return
      }

      if (file.size > MAX_LOGO_SIZE_BYTES) {
        setFieldErrors((prev) => ({
          ...prev,
          logo: "Logo file size cannot exceed 2MB.",
        }))
        return
      }

      setFieldErrors((prev) => ({ ...prev, logo: "" }))
      setLogoFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setLogoPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    },
    [],
  )

  const handleRemoveLogo = useCallback(() => {
    setLogoFile(null)
    setLogoPreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }, [])

  const validate = useCallback((): boolean => {
    const errors: Record<string, string> = {}
    if (!name.trim()) {
      errors.name = "Company name is required."
    }
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }, [name])

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setGeneralError(null)

      if (!validate()) return

      setIsSubmitting(true)
      try {
        let savedCompany: Company

        if (logoFile) {
          const formData = new FormData()
          formData.append("name", name.trim())
          if (industry.trim()) formData.append("industry", industry.trim())
          if (country.trim()) formData.append("country", country.trim())
          if (website.trim()) formData.append("website", website.trim())
          if (phone.trim()) formData.append("phone", phone.trim())
          if (address.trim()) formData.append("address", address.trim())
          formData.append("logo", logoFile)

          if (isEdit && company) {
            const res = await companiesService.updateCompany(
              company.id,
              formData,
            )
            savedCompany = res.data
          } else {
            const res = await companiesService.createCompany(formData)
            savedCompany = res.data
          }
        } else {
          const payload = {
            name: name.trim(),
            industry: industry.trim(),
            country: country.trim(),
            website: website.trim(),
            phone: phone.trim(),
            address: address.trim(),
          }

          if (isEdit && company) {
            const res = await companiesService.updateCompany(
              company.id,
              payload,
            )
            savedCompany = res.data
          } else {
            const res = await companiesService.createCompany(payload)
            savedCompany = res.data
          }
        }

        onSuccess(savedCompany)
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
          `Failed to ${isEdit ? "update" : "create"} company.`
        setGeneralError(generalMsg)
      } finally {
        setIsSubmitting(false)
      }
    },
    [
      validate,
      logoFile,
      name,
      industry,
      country,
      website,
      phone,
      address,
      isEdit,
      company,
      onSuccess,
      onOpenChange,
    ],
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-xl max-h-[90vh] overflow-y-auto"
        onClose={() => !isSubmitting && onOpenChange(false)}
      >
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            <DialogTitle>
              {isEdit ? "Edit Company" : "Create New Company"}
            </DialogTitle>
          </div>
          <DialogDescription>
            {isEdit
              ? "Update company information and branding."
              : "Add a new client or account company to your organization."}
          </DialogDescription>
        </DialogHeader>

        {generalError && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{generalError}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {/* Logo Upload & Preview */}
          <div>
            <label className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-2">
              Company Logo
            </label>
            <div className="flex items-center gap-4">
              <div className="relative h-16 w-16 rounded-lg border border-border bg-muted/40 flex items-center justify-center overflow-hidden shrink-0">
                {logoPreview ? (
                  <img
                    src={logoPreview}
                    alt="Company logo preview"
                    className="h-full w-full object-contain p-1"
                  />
                ) : (
                  <Building2 className="h-7 w-7 text-muted-foreground/60" />
                )}
              </div>

              <div className="flex flex-col gap-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isSubmitting}
                  >
                    <Upload className="h-3.5 w-3.5 mr-1.5" />
                    {logoPreview ? "Change Logo" : "Upload Logo"}
                  </Button>
                  {logoPreview && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={handleRemoveLogo}
                      disabled={isSubmitting}
                      className="text-destructive hover:text-destructive"
                    >
                      <X className="h-3.5 w-3.5 mr-1" />
                      Remove
                    </Button>
                  )}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  PNG, JPG, or WebP up to 2MB.
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
            {fieldErrors.logo && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.logo}
              </p>
            )}
          </div>

          {/* Name & Industry */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="company-name"
                className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
              >
                Company Name <span className="text-destructive">*</span>
              </label>
              <Input
                id="company-name"
                placeholder="e.g. Acme Corporation"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                  if (fieldErrors.name) {
                    setFieldErrors((prev) => ({ ...prev, name: "" }))
                  }
                }}
                error={Boolean(fieldErrors.name)}
                disabled={isSubmitting}
                required
              />
              {fieldErrors.name && (
                <p className="text-xs text-destructive mt-1 font-medium">
                  {fieldErrors.name}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="company-industry"
                className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
              >
                Industry
              </label>
              <Input
                id="company-industry"
                placeholder="e.g. Technology, Healthcare"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                disabled={isSubmitting}
              />
              {fieldErrors.industry && (
                <p className="text-xs text-destructive mt-1 font-medium">
                  {fieldErrors.industry}
                </p>
              )}
            </div>
          </div>

          {/* Country & Phone */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="company-country"
                className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
              >
                Country
              </label>
              <Input
                id="company-country"
                placeholder="e.g. US, DE, United States"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                disabled={isSubmitting}
              />
              {fieldErrors.country && (
                <p className="text-xs text-destructive mt-1 font-medium">
                  {fieldErrors.country}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="company-phone"
                className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
              >
                Phone
              </label>
              <Input
                id="company-phone"
                placeholder="e.g. +1 555-0123"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={isSubmitting}
              />
              {fieldErrors.phone && (
                <p className="text-xs text-destructive mt-1 font-medium">
                  {fieldErrors.phone}
                </p>
              )}
            </div>
          </div>

          {/* Website */}
          <div>
            <label
              htmlFor="company-website"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Website
            </label>
            <Input
              id="company-website"
              placeholder="e.g. https://example.com"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              disabled={isSubmitting}
            />
            {fieldErrors.website && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.website}
              </p>
            )}
          </div>

          {/* Address */}
          <div>
            <label
              htmlFor="company-address"
              className="block text-xs font-semibold text-foreground uppercase tracking-wider mb-1"
            >
              Address
            </label>
            <Input
              id="company-address"
              placeholder="e.g. 123 Innovation Way, Suite 100"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              disabled={isSubmitting}
            />
            {fieldErrors.address && (
              <p className="text-xs text-destructive mt-1 font-medium">
                {fieldErrors.address}
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
                  {isEdit ? "Saving Changes..." : "Creating Company..."}
                </>
              ) : (
                <>{isEdit ? "Save Changes" : "Create Company"}</>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export interface Contact {
  id: string
  company: string
  company_name: string
  organization: string
  full_name: string
  email: string
  phone: string
  role: string
  created_at: string
  updated_at: string
}

export interface ContactCreateUpdate {
  company: string
  full_name: string
  email: string
  phone?: string
  role?: string
}

export interface ContactFilters {
  search?: string
  company?: string
  page?: number
  page_size?: number
}

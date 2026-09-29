export interface Company {
  id: string
  name: string
  industry: string
  country: string
  logo: string | null
  logo_url: string | null
  website: string
  phone: string
  address: string
  organization: string
  contacts_count: number
  created_at: string
  updated_at: string
}

export interface CompanyCreateUpdate {
  name: string
  industry?: string
  country?: string
  website?: string
  phone?: string
  address?: string
  logo?: File | null
}

export interface CompanyFilters {
  search?: string
  industry?: string
  country?: string
  page?: number
  page_size?: number
}

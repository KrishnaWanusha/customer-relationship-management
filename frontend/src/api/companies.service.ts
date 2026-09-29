import { apiClient } from "./client"
import type {
  ApiResponse,
  Company,
  CompanyCreateUpdate,
  CompanyFilters,
  PaginatedApiResponse,
} from "@/types"

export const companiesService = {
  async getCompanies(params?: CompanyFilters): Promise<PaginatedApiResponse<Company>> {
    const response = await apiClient.get<PaginatedApiResponse<Company>>("/companies/", {
      params,
    })
    return response.data
  },

  async getCompany(id: string): Promise<ApiResponse<Company>> {
    const response = await apiClient.get<ApiResponse<Company>>(`/companies/${id}/`)
    return response.data
  },

  async createCompany(data: CompanyCreateUpdate | FormData): Promise<ApiResponse<Company>> {
    const isFormData = data instanceof FormData
    const response = await apiClient.post<ApiResponse<Company>>("/companies/", data, {
      headers: isFormData ? { "Content-Type": "multipart/form-data" } : undefined,
    })
    return response.data
  },

  async updateCompany(
    id: string,
    data: Partial<CompanyCreateUpdate> | FormData,
  ): Promise<ApiResponse<Company>> {
    const isFormData = data instanceof FormData
    const response = await apiClient.patch<ApiResponse<Company>>(`/companies/${id}/`, data, {
      headers: isFormData ? { "Content-Type": "multipart/form-data" } : undefined,
    })
    return response.data
  },

  async deleteCompany(id: string): Promise<ApiResponse<null>> {
    const response = await apiClient.delete<ApiResponse<null>>(`/companies/${id}/`)
    return response.data
  },
}

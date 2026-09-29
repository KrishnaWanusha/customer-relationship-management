import { apiClient } from "./client"
import type {
  ApiResponse,
  Contact,
  ContactCreateUpdate,
  ContactFilters,
  PaginatedApiResponse,
} from "@/types"

export const contactsService = {
  async getContacts(
    params?: ContactFilters,
  ): Promise<PaginatedApiResponse<Contact>> {
    const response = await apiClient.get<PaginatedApiResponse<Contact>>(
      "/contacts/",
      {
        params,
      },
    )
    return response.data
  },

  async getContact(id: string): Promise<ApiResponse<Contact>> {
    const response = await apiClient.get<ApiResponse<Contact>>(
      `/contacts/${id}/`,
    )
    return response.data
  },

  async createContact(
    data: ContactCreateUpdate,
  ): Promise<ApiResponse<Contact>> {
    const response = await apiClient.post<ApiResponse<Contact>>(
      "/contacts/",
      data,
    )
    return response.data
  },

  async updateContact(
    id: string,
    data: Partial<ContactCreateUpdate>,
  ): Promise<ApiResponse<Contact>> {
    const response = await apiClient.patch<ApiResponse<Contact>>(
      `/contacts/${id}/`,
      data,
    )
    return response.data
  },

  async deleteContact(id: string): Promise<ApiResponse<null>> {
    const response = await apiClient.delete<ApiResponse<null>>(
      `/contacts/${id}/`,
    )
    return response.data
  },
}

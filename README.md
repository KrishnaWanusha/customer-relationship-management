# Multi-Tenant Customer Relationship Management (CRM) System

A robust, enterprise-grade, multi-tenant CRM application engineered with Django REST Framework, PostgreSQL, and React. Built to comply strictly with modern security, tenant isolation, role-based access control (RBAC), and cloud asset management standards.

---

## 1. Project Overview

This repository implements a production-ready Multi-Tenant CRM system featuring:

- **Strict Multi-Tenancy**: Shared PostgreSQL database with shared schema and row-level tenant partitioning via `django-multitenant`.
- **JWT Dual-Token Security**: Access tokens kept in JavaScript memory only; long-lived refresh tokens isolated in HttpOnly, SameSite cookies.
- **Enterprise RBAC**: Admin, Manager, and Staff roles with server-enforced permission boundaries.
- **Auditing & Traceability**: Automatic, immutable activity logging for all entity operations (CREATE, UPDATE, DELETE).
- **Private S3 Storage**: Secure company logo uploads with partitioned S3 prefixes and time-limited presigned URLs.
- **Resilient Frontend**: React 19 + TypeScript + Vite with a centralized Axios interceptor for automatic token refresh queueing and zero data leakage.

---

## 2. Technology Stack

### Backend

- **Framework**: Python 3.12+ / Django 5.1 / Django REST Framework 3.15
- **Database**: PostgreSQL 15+
- **Multi-Tenancy**: `django-multitenant` 4.1
- **Authentication**: `djangorestframework-simplejwt` 5.3 (HttpOnly cookie refresh)
- **Object Storage**: AWS S3 (`django-storages`, `boto3`, `pillow`)
- **Filtering & Search**: `django-filter`, `rest_framework.filters`

### Frontend

- **Framework**: React 19 / TypeScript / Vite 8
- **Styling**: Tailwind CSS / Lucide React / shadcn-style component architecture
- **Routing**: React Router v7
- **HTTP Client**: Axios with custom interceptors and request queueing
- **State Management**: React Context + `useReducer` + memoized state hooks

---

## 3. High-Level Architecture

```
[ React 19 SPA (Vite + TS) ]
        |
        |  HTTPS / JSON (/api/v1/)
        |  Authorization: Bearer <memory_token>
        |  Cookie: refresh_token (HttpOnly)
        v
[ Django REST Framework API Layer ]
        ├── Authentication: SimpleJWT + HttpOnly Cookie Handler
        ├── Multi-Tenancy Context: TenantFilteredViewSetMixin
        ├── RBAC Engine: IsAdmin | CanModifyCRMRecord | CanViewActivityLogs
        ├── Serializers: Validation & Data Transformation
        └── Audit Service: Immutable ActivityLog recording
        |
        v
[ Persistence & Cloud Infrastructure ]
        ├── Database: PostgreSQL (Shared DB + Shared Schema + Row-Level Partitioning)
        └── Storage: AWS S3 (Private Bucket + Presigned URL Retrieval)
```

---

## 4. Getting Started & Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm 10+
- PostgreSQL 15+ running locally or in Docker

---

### Backend Setup

1. **Navigate to the backend directory**:

   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:

   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and configure your local PostgreSQL credentials:

   ```bash
   cp .env.example .env
   ```

5. **Apply database migrations**:

   ```bash
   python manage.py migrate
   ```

6. **Seed the database with test organizations and users**:

   ```bash
   python manage.py seed_crm
   ```

7. **Run the backend development server**:
   ```bash
   python manage.py runserver
   ```
   Backend will be running at: `http://127.0.0.1:8000/`

---

### Frontend Setup

1. **Navigate to the frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment variables**:
   Verify `frontend/.env` contains the API base URL:

   ```bash
   VITE_API_URL=http://localhost:8000/api/v1
   ```

4. **Run the frontend development server**:
   ```bash
   npm run dev
   ```
   Frontend will be running at: `http://localhost:5173/`

---

## 5. Seed Credentials

The seed command (`python manage.py seed_crm`) sets up two isolated organizations with the following credentials (Password for all accounts: `Password123!`):

| Organization           | Role      | Email                     | Permissions                                                 |
| :--------------------- | :-------- | :------------------------ | :---------------------------------------------------------- |
| **Alpha Corporation**  | `ADMIN`   | `admin@alphacorp.com`     | Full CRUD, soft delete, activity logs                       |
| **Alpha Corporation**  | `MANAGER` | `manager@alphacorp.com`   | Create/edit companies & contacts, activity logs             |
| **Alpha Corporation**  | `STAFF`   | `staff@alphacorp.com`     | Create/edit companies & contacts (No delete, No audit logs) |
| **Beta Solutions Ltd** | `ADMIN`   | `admin@betasolutions.com` | Isolated Tenant Admin (Cannot see Alpha Corp data)          |

---

## 6. Running Tests & Quality Verification

### Run Backend Tests (131 Automated Tests)

```bash
cd backend
python manage.py test apps common
```

- Covers:
  - Multi-tenant cross-organization isolation & direct ID tampering (IDOR)
  - RBAC enforcement across Admin, Manager, and Staff roles
  - JWT authentication, refresh cookie rotation, and logout
  - Soft deletion lifecycle and cascade protection
  - S3 storage presigned URL generation and prefix isolation
  - Activity audit logging on CREATE, UPDATE, DELETE

### Run Frontend Linting & Type Checking

```bash
cd frontend
npm run lint         # Runs oxlint across all source files
npm run build        # Executes TypeScript compilation (tsc -b) and Vite production build
```

---

## 7. Security & Tenant Isolation

1. **Memory-Only Access Token**:
   - Access tokens are never saved to `localStorage` or `sessionStorage`.
   - Immune to token exfiltration via client-side XSS.
2. **HttpOnly Refresh Cookie**:
   - Long-lived refresh token stored in an inaccessible HttpOnly, SameSite=Lax cookie.
   - Transparently refreshed via an Axios interceptor queue on 401 status.
3. **Row-Level Tenant Isolation**:
   - All tenant-owned models (`Company`, `Contact`, `ActivityLog`, `User`) inherit from `django-multitenant`'s `TenantModel`.
   - The user's authenticated organization is always authoritative; client-provided `organization_id` parameters are ignored server-side.
4. **Soft Delete**:
   - CRM entities are never physically purged.
   - Deletion invokes soft-delete logic (`is_deleted=True`, `deleted_at=now()`, `deleted_by=user`).
5. **Private S3 Bucket**:
   - Bucket public access is blocked.
   - Assets are accessed via AWS S3 presigned URLs with 1-hour expiration.

---

## 8. REST API Reference

All endpoints are versioned under `/api/v1/` and follow standardized response envelopes:

```json
// Success Response (HTTP 200 / 201)
{
  "success": true,
  "message": "Company created successfully",
  "data": { ... }
}

// Error Response (HTTP 400 / 401 / 403 / 404 / 500)
{
  "success": false,
  "message": "Invalid credentials provided.",
  "errors": { ... }
}
```

### Core Endpoints

| Method      | Endpoint                      | Description                                                  | Role Access             |
| :---------- | :---------------------------- | :----------------------------------------------------------- | :---------------------- |
| `POST`      | `/api/v1/auth/login/`         | Authenticate user, return access token & set refresh cookie  | Public                  |
| `POST`      | `/api/v1/auth/refresh/`       | Refresh access token using HttpOnly cookie                   | Public (Cookie)         |
| `POST`      | `/api/v1/auth/logout/`        | Invalidate and clear refresh token cookie                    | Public                  |
| `GET`       | `/api/v1/auth/me/`            | Retrieve current authenticated user profile & tenant info    | Authenticated           |
| `GET`       | `/api/v1/companies/`          | List tenant companies (supports search, filters, pagination) | Admin, Manager, Staff   |
| `POST`      | `/api/v1/companies/`          | Create a new company (supports multipart logo upload)        | Admin, Manager, Staff   |
| `GET`       | `/api/v1/companies/{id}/`     | Retrieve company details and presigned logo URL              | Admin, Manager, Staff   |
| `PUT/PATCH` | `/api/v1/companies/{id}/`     | Update company information                                   | Admin, Manager, Staff   |
| `DELETE`    | `/api/v1/companies/{id}/`     | Soft delete company and associated records                   | **Admin only**          |
| `GET`       | `/api/v1/contacts/`           | List tenant contacts (filterable by `company_id`)            | Admin, Manager, Staff   |
| `POST`      | `/api/v1/contacts/`           | Create a new contact nested under a tenant company           | Admin, Manager, Staff   |
| `GET`       | `/api/v1/contacts/{id}/`      | Retrieve contact details                                     | Admin, Manager, Staff   |
| `PUT/PATCH` | `/api/v1/contacts/{id}/`      | Update contact information                                   | Admin, Manager, Staff   |
| `DELETE`    | `/api/v1/contacts/{id}/`      | Soft delete contact                                          | **Admin only**          |
| `GET`       | `/api/v1/activity-logs/`      | List immutable audit logs for current tenant                 | **Admin, Manager only** |
| `GET`       | `/api/v1/activity-logs/{id}/` | Retrieve single audit log entry                              | **Admin, Manager only** |

---

## 9. Production Configuration

In production environments:

1. Set `DJANGO_SETTINGS_MODULE=config.settings.production`.
2. Set `DJANGO_DEBUG=False`.
3. Provide a strong, unique `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`.
4. Configure `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to your registered production domains.
5. Set `USE_S3=True` and configure `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, and appropriate IAM credentials/role.
6. Frontend build output in `frontend/dist/` can be served via Nginx, Cloudflare Pages, AWS S3 + CloudFront, or any standard CDN.

---

## 10. License

All rights reserved.

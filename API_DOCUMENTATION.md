# GJ Spaces CRM - API Documentation

Comprehensive API documentation for the **GJ Spaces Centralized CRM Backend**, covering Authentication, Role-Based Access Control (RBAC), and Workforce Administration.

---

## 1. Overview & Setup

- **Base URL:** `http://localhost:8000`
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Spec:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Authentication Mechanism
Protected endpoints require a standard HTTP **Bearer Token** passed in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```
The token is obtained via the `POST /auth/login` endpoint. It uses JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`) and has a default expiration of 120 minutes.

### Default Seeded Super Admin Credentials
On server startup, the database automatically initializes the default roles and seeds the initial Super Admin:
- **Email:** `ankita.patil@shakham.com`
- **Password:** `password1234`
- **Contact Number:** `+910000000000`

---

## 2. Roles & RBAC Matrix

| Role ID | Role Name | Description |
| :---: | :--- | :--- |
| **1** | `Super Admin` | Full root access across workforce, user creation, and soft-deletion. |
| **2** | `Manager` | Administrative access to view workforce users, roles, and profiles. Cannot create or delete users. |
| **3** | `Employee` | Standard workforce account. Can log in and view own profile (`/me`). |

### Permissions by Endpoint

| HTTP Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Public | Root service info |
| `GET` | `/health` | Public | Container health check |
| `POST` | `/auth/login` | Public | Step 1: Verify credentials & send 6-digit OTP to email |
| `POST` | `/auth/verify-otp` | Public | Step 2: Verify OTP & receive JWT access token |
| `POST` | `/auth/resend-otp` | Public | Resend fresh 6-digit OTP to email |
| `GET` | `/me` (or `/auth/me`) | Super Admin, Manager, Employee | Retrieve own profile (clean profile details) |
| `GET` | `/users/roles` | Super Admin, Manager | List master roles (`id` and `role_name` only) |
| `POST` | `/users` | Super Admin | Create Manager or Employee (auto-emails credentials) |
| `GET` | `/users` | Super Admin, Manager | List all workforce users (with filters) |
| `GET` | `/users/{user_id}` | Super Admin, Manager | Retrieve user details by UUID |
| `DELETE` | `/users/{user_id}` | Super Admin | Soft delete user |
| `POST` | `/attendance/mark-present` | Super Admin, Manager, Employee | Mark present for today & capture `login_time` |
| `PUT` | `/attendance/tasks` | Super Admin, Manager, Employee | Upload / update today's `to_do_list` |
| `POST` | `/attendance/logout` | Super Admin, Manager, Employee | Clock out & capture `logout_time` |
| `GET` | `/attendance/today` | Super Admin, Manager, Employee | View today's attendance record & tasks |
| `GET` | `/attendance/my-history` | Super Admin, Manager, Employee | View own historical attendance logs |
| `GET` | `/attendance` | Super Admin, Manager | View all workforce attendance with user info |
| `POST` | `/lead-sources` | Super Admin | Create a new lead source |
| `GET` | `/lead-sources` | Super Admin | List all active lead sources |
| `PUT` | `/lead-sources/{id}` | Super Admin | Update lead source name/description |
| `DELETE` | `/lead-sources/{id}` | Super Admin | Soft delete lead source |
| `POST` | `/lead-categories` | Super Admin | Create a new lead category |
| `GET` | `/lead-categories` | Super Admin | List all active lead categories |
| `PUT` | `/lead-categories/{id}` | Super Admin | Update lead category name/description |
| `DELETE` | `/lead-categories/{id}` | Super Admin | Soft delete lead category |
| `POST` | `/lead-statuses` | Super Admin | Create a new lead status |
| `GET` | `/lead-statuses` | Super Admin | List all active lead statuses |
| `PUT` | `/lead-statuses/{id}` | Super Admin | Update lead status name/description |
| `DELETE` | `/lead-statuses/{id}` | Super Admin | Soft delete lead status |
| `POST` | `/forms` | Super Admin | Create a new configurable form |
| `GET` | `/forms` | Super Admin, Manager, Employee | List all active forms (with field count) |
| `GET` | `/forms/{form_id}` | Super Admin, Manager, Employee | Get form structure with ordered fields |
| `PUT` | `/forms/{form_id}` | Super Admin | Update form title, description, or status |
| `DELETE` | `/forms/{form_id}` | Super Admin | Soft delete a form and its fields |
| `POST` | `/forms/{form_id}/fields` | Super Admin | Add a field to a form |
| `PUT` | `/forms/fields/{field_id}` | Super Admin | Update field properties (name, type, options, etc.) |
| `DELETE` | `/forms/fields/{field_id}` | Super Admin | Soft delete a field |
| `PUT` | `/forms/{form_id}/reorder-fields` | Super Admin | Bulk reorder fields in a form |

---

## 3. Endpoints Specification

### 3.1 System & Health

---

#### `GET /`
Returns service status and documentation URLs.

- **Access:** Public
- **Headers:** None
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "service": "GJ Spaces CRM API",
  "status": "online",
  "documentation": "/docs",
  "version": "1.0.0"
}
```

---

#### `GET /health`
Uptime health check endpoint.

- **Access:** Public
- **Headers:** None
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "status": "healthy"
}
```

---

### 3.2 Authentication & Session (`/auth`, `/me`)

---

#### `POST /auth/login`
**Step 1 of Login:** Validates user credentials (email/contact number and password). Upon success, generates a 6-digit verification OTP and delivers it to the user's registered email address (valid for 10 minutes).

- **Access:** Public
- **Headers:** `Content-Type: application/json`
- **Request Body Schema:**
  - `email` (string, required): Registered user email or contact number.
  - `password` (string, required): Plaintext password.

**Sample Request Body:**
```json
{
  "email": "ankita.patil@shakham.com",
  "password": "password1234"
}
```
*(Also valid: `"email": "+910000000000"`)*

**Response `200 OK`:**
```json
{
  "message": "Verification OTP has been sent to your registered email (ankita.patil@shakham.com).",
  "email": "ankita.patil@shakham.com",
  "otp_sent": true
}
```

**Common Error Responses:**
- `401 Unauthorized`:
  ```json
  {
    "detail": "Incorrect email or password."
  }
  ```
- `403 Forbidden`:
  ```json
  {
    "detail": "Account is inactive. Please contact Super Admin."
  }
  ```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ankita.patil@shakham.com",
    "password": "password1234"
  }'
```

---

#### `POST /auth/verify-otp`
**Step 2 of Login:** Verifies the 6-digit OTP sent to the user's registered email. Upon successful verification, marks the OTP as used and issues the signed JWT access token.

- **Access:** Public
- **Headers:** `Content-Type: application/json`
- **Request Body Schema:**
  - `email` (string, required): Registered user email or contact number.
  - `otp` (string, 6 characters, required): The 6-digit verification code received via email.

**Sample Request Body:**
```json
{
  "email": "ankita.patil@shakham.com",
  "otp": "481920"
}
```

**Response `200 OK`:**
```json
{
  "message": "Authentication successful.",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role_name": "Super Admin",
  "email": "ankita.patil@shakham.com"
}
```

**Common Error Responses:**
- `400 Bad Request`:
  ```json
  {
    "detail": "Invalid or expired OTP. Please check the code or request a new one."
  }
  ```
- `404 Not Found`:
  ```json
  {
    "detail": "User with identifier 'ankita.patil@shakham.com' was not found."
  }
  ```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ankita.patil@shakham.com",
    "otp": "481920"
  }'
```

---

#### `POST /auth/resend-otp`
Invalidates any pending OTP and issues a fresh 6-digit verification OTP delivered to the registered email.

- **Access:** Public
- **Headers:** `Content-Type: application/json`
- **Request Body Schema:**
  - `email` (string, required): Registered user email or contact number.

**Sample Request Body:**
```json
{
  "email": "ankita.patil@shakham.com"
}
```

**Response `200 OK`:**
```json
{
  "message": "A fresh verification OTP has been sent to your registered email (ankita.patil@shakham.com).",
  "email": "ankita.patil@shakham.com",
  "otp_sent": true
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/resend-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ankita.patil@shakham.com"
  }'
```

---

#### `GET /me` (or `GET /auth/me`)
Retrieves the logged-in user's profile information. Both URLs (`/me` and `/auth/me`) are supported.

- **Access:** Any authenticated active user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "role_name": "Super Admin",
  "first_name": "Super",
  "last_name": "Admin",
  "email": "ankita.patil@shakham.com",
  "contact_number": "+910000000000"
}
```

**Common Error Responses:**
- `401 Unauthorized`:
  ```json
  {
    "detail": "Could not validate credentials."
  }
  ```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer <access_token>"
```

---

### 3.3 Workforce & User Administration (`/users`)

---

#### `GET /users/roles`
Retrieves available master roles for workforce assignment. Returns only `id` and `role_name`.

- **Access:** `Super Admin`, `Manager`
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Request Body:** None

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "role_name": "Super Admin"
  },
  {
    "id": 2,
    "role_name": "Manager"
  },
  {
    "id": 3,
    "role_name": "Employee"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/users/roles" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `POST /users`
Super Admin endpoint to create new Managers or Employees.
- **Automated Credential Email:** Asynchronously sends an onboarding email to the new user's registered email with their portal URL, email address, assigned role, and plaintext initial password.
- `status` defaults to `"active"` automatically.
- `role_id` defaults to `3` (`Employee`) if omitted, or you can specify `2` for `Manager`.
- You can alternatively provide `"role_name": "Manager"` instead of `role_id`.

- **Access:** `Super Admin` only
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **Request Body Fields:**
  - `first_name` (string, required): User's first name.
  - `last_name` (string, optional): User's last name.
  - `email` (string, required): Unique email address.
  - `contact_number` (string, required): Unique contact phone number.
  - `password` (string, required, min 6 chars): Password.
  - `role_id` (integer, optional, default: `3`): `2` for Manager, `3` for Employee.
  - `role_name` (string, optional): Alternatively pass `"Manager"` or `"Employee"`.
  - `status` (string, optional, default: `"active"`): Defaults to `"active"`.

**Sample Request Body (Creating a Manager):**
```json
{
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "email": "rajesh.kumar@gjspaces.com",
  "contact_number": "+919876543210",
  "password": "SecurePassword123!",
  "role_id": 2
}
```

**Sample Request Body (Creating an Employee - minimal):**
```json
{
  "first_name": "Priya",
  "last_name": "Sharma",
  "email": "priya.sharma@gjspaces.com",
  "contact_number": "+919876543211",
  "password": "SecurePassword123!"
}
```
*(Automatically assigns `role_name`: "Employee" and `status`: "active")*

**Response `201 Created`:**
```json
{
  "id": "7b0a7082-f54e-4e31-8bc4-72945d8b8a01",
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "email": "rajesh.kumar@gjspaces.com",
  "contact_number": "+919876543210",
  "role_name": "Manager",
  "status": "active"
}
```

**Common Error Responses:**
- `400 Bad Request` (Invalid role):
  ```json
  {
    "detail": "Role with ID '99' does not exist."
  }
  ```
- `403 Forbidden` (Attempting to create another Super Admin):
  ```json
  {
    "detail": "Secondary Super Admin users cannot be created via this endpoint."
  }
  ```
- `409 Conflict` (Email or Contact already in use):
  ```json
  {
    "detail": "Email 'rajesh.kumar@gjspaces.com' is already registered."
  }
  ```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "first_name": "Rajesh",
    "last_name": "Kumar",
    "email": "rajesh.kumar@gjspaces.com",
    "contact_number": "+919876543210",
    "password": "SecurePassword123!",
    "role_id": 2
  }'
```

---

#### `GET /users`
Lists active workforce users.

- **Access:** `Super Admin`, `Manager`
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Query Parameters (Optional):**
  - `role_id` (integer): Filter by Role ID (`?role_id=2` or `?role_id=3`)
  - `status` (string): Filter by user status (`?status=active`)
- **Request Body:** None

**Response `200 OK`:**
```json
[
  {
    "id": "7b0a7082-f54e-4e31-8bc4-72945d8b8a01",
    "first_name": "Rajesh",
    "last_name": "Kumar",
    "email": "rajesh.kumar@gjspaces.com",
    "contact_number": "+919876543210",
    "role_name": "Manager",
    "status": "active"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/users" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `GET /users/{user_id}`
Retrieves a single user's profile and assigned role by UUID.

- **Access:** `Super Admin`, `Manager`
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Path Parameters:**
  - `user_id` (UUID string, required)
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "id": "7b0a7082-f54e-4e31-8bc4-72945d8b8a01",
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "email": "rajesh.kumar@gjspaces.com",
  "contact_number": "+919876543210",
  "role_name": "Manager",
  "status": "active"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/users/7b0a7082-f54e-4e31-8bc4-72945d8b8a01" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `DELETE /users/{user_id}`
Soft deletes a user record (sets `is_deleted = true`, `status = 'inactive'`).

- **Access:** `Super Admin` only
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Path Parameters:**
  - `user_id` (UUID string, required)
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "message": "User 'Rajesh Kumar' soft-deleted successfully.",
  "user_id": "7b0a7082-f54e-4e31-8bc4-72945d8b8a01"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/users/7b0a7082-f54e-4e31-8bc4-72945d8b8a01" \
  -H "Authorization: Bearer <access_token>"
```

---

### 3.4 Attendance & Daily Tasks (`/attendance`)

---

#### `POST /attendance/mark-present`
Employee marks their attendance as present for today, capturing `login_time`. Optionally accepts `to_do` or `to_do_list`.

- **Access:** Any authenticated user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Content-Type: application/json` (optional if passing body)
  - `Authorization: Bearer <access_token>`
- **Request Body Fields (All Optional):**
  - `to_do` (string, optional): Initial daily tasks or to-do list for today.
  - `to_do_list` (string, optional): Alias for `to_do`.

**Sample Request Body (Optional - leave empty `{}` or omit if no to-do yet):**
```json
{
  "to_do": "1. Review sprint tasks\n2. Work on CRM attendance module"
}
```

**Response `201 Created`:**
```json
{
  "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "user_id": "0a84de0f-982e-47b0-880b-bd80e55d3de6",
  "login_time": "2026-11-19T09:30:00Z",
  "logout_time": null,
  "to_do_list": "1. Review sprint tasks\n2. Work on CRM attendance module"
}
```

**Common Error Responses:**
- `400 Bad Request` (Attempting to mark present after already checking out):
  ```json
  {
    "detail": "You have already checked out for today at 18:00:00. Cannot mark attendance again today."
  }
  ```
- `409 Conflict` (Attempting to mark present multiple times):
  ```json
  {
    "detail": "Attendance already marked present for today at 09:30:00. Attendance can only be marked once per day."
  }
  ```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/attendance/mark-present" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `PUT /attendance/tasks`
Submits or updates the employee's daily `to_do_list` / task deliverables for today's active attendance record.

- **Access:** Any authenticated user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **Request Body Fields:**
  - `to_do_list` (string, required): Summary or bullet points of daily tasks / deliverables.

**Sample Request Body:**
```json
{
  "to_do_list": "1. Implemented attendance API module\n2. Tested mark-present and logout flows\n3. Updated documentation"
}
```

**Response `200 OK`:**
```json
{
  "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "user_id": "0a84de0f-982e-47b0-880b-bd80e55d3de6",
  "login_time": "2026-11-19T09:30:00Z",
  "logout_time": null,
  "to_do_list": "1. Implemented attendance API module\n2. Tested mark-present and logout flows\n3. Updated documentation"
}
```

**Common Error Responses:**
- `400 Bad Request` (Empty task content):
  ```json
  {
    "detail": "Task content cannot be empty."
  }
  ```
- `400 Bad Request` (Attempting to update tasks after check-out):
  ```json
  {
    "detail": "Cannot update tasks after check-out. You have already logged out today at 18:00:00."
  }
  ```
- `404 Not Found`:
  ```json
  {
    "detail": "No attendance record found for today. Please mark present first."
  }
  ```

**cURL Example:**
```bash
curl -X PUT "http://localhost:8000/attendance/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "to_do_list": "1. Implemented attendance API\n2. Verified database schema"
  }'
```

---

#### `POST /attendance/logout`
Clocks out the employee for the workday, capturing the `logout_time`.

- **Access:** Any authenticated user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "message": "Logged out successfully.",
  "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "login_time": "2026-11-19T09:30:00Z",
  "logout_time": "2026-11-19T18:00:00Z",
  "to_do_list": "1. Implemented attendance API module\n2. Tested mark-present and logout flows\n3. Updated documentation"
}
```

**Common Error Responses:**
- `400 Bad Request` (Already checked out):
  ```json
  {
    "detail": "Already logged out today at 18:00:00. You cannot check out multiple times."
  }
  ```
- `404 Not Found` (Never marked present today):
  ```json
  {
    "detail": "No attendance record found for today. You must mark present before checking out."
  }
  ```
- `400 Bad Request` (Already clocked out):
  ```json
  {
    "detail": "Already logged out today at 18:00:00 UTC."
  }
  ```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/attendance/logout" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `GET /attendance/today`
Retrieves the logged-in employee's active attendance record and tasks for today.

- **Access:** Any authenticated user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Request Body:** None

**Response `200 OK`:**
```json
{
  "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "user_id": "0a84de0f-982e-47b0-880b-bd80e55d3de6",
  "login_time": "2026-11-19T09:30:00Z",
  "logout_time": "2026-11-19T18:00:00Z",
  "to_do_list": "1. Implemented attendance API module\n2. Tested mark-present and logout flows\n3. Updated documentation"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/attendance/today" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `GET /attendance/my-history`
Retrieves the logged-in employee's past attendance records.

- **Access:** Any authenticated user (`Super Admin`, `Manager`, `Employee`)
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Query Parameters (Optional):**
  - `limit` (integer, default `30`, min `1`, max `100`): Max records to return.
- **Request Body:** None

**Response `200 OK`:**
```json
[
  {
    "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "user_id": "0a84de0f-982e-47b0-880b-bd80e55d3de6",
    "login_time": "2026-11-19T09:30:00Z",
    "logout_time": "2026-11-19T18:00:00Z",
    "to_do_list": "1. Implemented attendance API module"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/attendance/my-history?limit=10" \
  -H "Authorization: Bearer <access_token>"
```

---

#### `GET /attendance`
Super Admin and Manager endpoint to view workforce attendance across all employees, enriched with employee name and email.

- **Access:** `Super Admin`, `Manager`
- **Headers:** 
  - `Authorization: Bearer <access_token>`
- **Query Parameters (Optional):**
  - `target_date` (string, format `YYYY-MM-DD`): Filter attendance on a specific calendar date (e.g. `?target_date=2026-11-19`).
  - `user_id` (UUID): Filter attendance for a specific employee.
- **Request Body:** None

**Response `200 OK`:**
```json
[
  {
    "attendance_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "user_id": "0a84de0f-982e-47b0-880b-bd80e55d3de6",
    "employee_name": "Priya Sharma",
    "email": "priya.sharma@gjspaces.com",
    "login_time": "2026-11-19T09:30:00Z",
    "logout_time": "2026-11-19T18:00:00Z",
    "to_do_list": "1. Implemented attendance API module"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/attendance?target_date=2026-11-19" \
  -H "Authorization: Bearer <access_token>"
```

---

### 3.5 Lead Master Configuration (`/lead-sources`, `/lead-categories`, `/lead-statuses`)

Master configuration endpoints for managing lead dropdowns and taxonomy in the CRM.

---

#### 1. Lead Sources (`/lead-sources`)

##### `POST /lead-sources`
Adds a new lead source (e.g. *Instagram, Website, Justdial*).
- **Access:** `Super Admin` only
- **Headers:** 
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`
- **Request Body:**
```json
{
  "name": "LinkedIn Ads",
  "description": "Leads from LinkedIn B2B campaigns"
}
```
- **Response `201 Created`:**
```json
{
  "id": 7,
  "name": "LinkedIn Ads",
  "description": "Leads from LinkedIn B2B campaigns",
  "is_active": true
}
```

##### `GET /lead-sources`
Retrieves all active lead sources for dropdown options.
- **Access:** `Super Admin` only
- **Headers:** `Authorization: Bearer <access_token>`
- **Response `200 OK`:**
```json
[
  { "id": 1, "name": "Instagram", "description": "Leads from Instagram ads & page", "is_active": true },
  { "id": 2, "name": "Website", "description": "Organic form inquiries from company website", "is_active": true },
  { "id": 3, "name": "Justdial", "description": "Inquiries from Justdial listings", "is_active": true },
  { "id": 4, "name": "Facebook", "description": "Leads from Facebook ad campaigns", "is_active": true },
  { "id": 5, "name": "Referral", "description": "Word-of-mouth or customer referral", "is_active": true },
  { "id": 6, "name": "Direct Walk-in", "description": "Walk-in inquiries at project office", "is_active": true }
]
```

##### `PUT /lead-sources/{id}`
Updates a lead source's name, description, or active status.
- **Access:** `Super Admin` only
- **Path Parameter:** `id` (integer)
- **Request Body:**
```json
{
  "name": "Instagram Influencers",
  "description": "Updated description",
  "is_active": true
}
```

##### `DELETE /lead-sources/{id}`
Soft deletes a lead source.
- **Access:** `Super Admin` only
- **Response `200 OK`:**
```json
{
  "message": "Lead Source 'LinkedIn Ads' deleted successfully.",
  "id": 7
}
```

---

#### 2. Lead Categories (`/lead-categories`)

##### `POST /lead-categories`
Adds a new lead category (e.g. *Hot, Warm, Cold*).
- **Access:** `Super Admin` only
- **Request Body:**
```json
{
  "name": "Ultra Hot",
  "description": "Immediate decision maker ready to book"
}
```
- **Response `201 Created`:**
```json
{
  "id": 4,
  "name": "Ultra Hot",
  "description": "Immediate decision maker ready to book",
  "is_active": true
}
```

##### `GET /lead-categories`
Retrieves all active lead categories.
- **Access:** `Super Admin` only
- **Response `200 OK`:**
```json
[
  { "id": 1, "name": "Hot", "description": "High purchase intent, immediate follow-up required", "is_active": true },
  { "id": 2, "name": "Warm", "description": "Interested buyer evaluating options", "is_active": true },
  { "id": 3, "name": "Cold", "description": "Low engagement or future prospect", "is_active": true }
]
```

##### `PUT /lead-categories/{id}`
Updates a lead category.
- **Access:** `Super Admin` only

##### `DELETE /lead-categories/{id}`
Soft deletes a lead category.
- **Access:** `Super Admin` only

---

#### 3. Lead Statuses (`/lead-statuses`)

##### `POST /lead-statuses`
Adds a new lead lifecycle status.
- **Access:** `Super Admin` only
- **Request Body:**
```json
{
  "name": "Token Advance Paid",
  "description": "Client paid booking token amount"
}
```
- **Response `201 Created`:**
```json
{
  "id": 9,
  "name": "Token Advance Paid",
  "description": "Client paid booking token amount",
  "is_active": true
}
```

##### `GET /lead-statuses`
Retrieves all active lead statuses.
- **Access:** `Super Admin` only
- **Response `200 OK`:**
```json
[
  { "id": 1, "name": "New Lead", "description": "Newly created lead, not contacted yet", "is_active": true },
  { "id": 2, "name": "Contacted", "description": "First call/message delivered to lead", "is_active": true },
  { "id": 3, "name": "Follow-up", "description": "Follow-up conversation in progress", "is_active": true },
  { "id": 4, "name": "Site Visit Scheduled", "description": "Appointment booked for property tour", "is_active": true },
  { "id": 5, "name": "Site Visit Completed", "description": "Client attended property walkthrough", "is_active": true },
  { "id": 6, "name": "Negotiation", "description": "Price or terms negotiation underway", "is_active": true },
  { "id": 7, "name": "Closed Won", "description": "Booking finalized and deal closed", "is_active": true },
  { "id": 8, "name": "Lost", "description": "Lead dropped or opted out", "is_active": true }
]
```

##### `PUT /lead-statuses/{id}`
Updates a lead status.
- **Access:** `Super Admin` only

##### `DELETE /lead-statuses/{id}`
Soft deletes a lead status.
- **Access:** `Super Admin` only

---

## 4. End-to-End Testing Workflow

```mermaid
flowchart TD
    A["1. Login Employee<br/>POST /auth/login"] --> B["2. Mark Attendance<br/>POST /attendance/mark-present"]
    B --> C["3. Upload Tasks / To-Do<br/>PUT /attendance/tasks"]
    C --> D["4. Check Status<br/>GET /attendance/today"]
    D --> E["5. Clock Out<br/>POST /attendance/logout"]
    E --> F["6. Manager Monitoring<br/>GET /attendance"]
```

### 1. Login as Employee
```bash
curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "priya.sharma@gjspaces.com", "password": "Password123!"}'
```

### 2. Mark Attendance as Present (Check-In)
Captures `login_time`:
```bash
curl -s -X POST "http://localhost:8000/attendance/mark-present" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 3. Upload Daily Tasks / To-Do List
```bash
curl -s -X PUT "http://localhost:8000/attendance/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>" \
  -d '{
    "to_do_list": "1. Client onboarding\n2. Code review\n3. Tested endpoints"
  }'
```

### 4. Verify Today's Attendance
```bash
curl -s -X GET "http://localhost:8000/attendance/today" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 5. Clock Out (Log Out)
Captures `logout_time`:
```bash
curl -s -X POST "http://localhost:8000/attendance/logout" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 6. Manager Review (Super Admin / Manager Token)
Inspect workforce attendance:
```bash
curl -s -X GET "http://localhost:8000/attendance" \
  -H "Authorization: Bearer <SUPER_ADMIN_TOKEN>"
```

---

## 3.6 Configurable Forms (`/forms`)

Provides a dynamic form configuration engine where Super Admin can define, modify, reorder, and soft-delete forms and their fields.
Pre-seeded with the client's 5 Google Forms:
1. **Lead Format** (26 fields)
2. **Project Form** (29 fields)
3. **Plotting Form** (12 fields)
4. **Commercial Project Form** (21 fields)
5. **Loan Format** (9 fields)

---

### `GET /forms`
Retrieves all active configured forms with their active field counts.

- **Access:** `Super Admin`, `Manager`, `Employee`
- **Query Params:** `is_active` (boolean, optional)

**Response `200 OK`:**
```json
[
  {
    "id": "5521e888-269f-49dd-a532-f00415468cb9",
    "form_title": "Lead Format",
    "description": "Client lead capture form for prospective property buyers",
    "is_active": true,
    "field_count": 26,
    "created_at": "2026-11-20T11:09:22.460000Z",
    "updated_at": "2026-11-20T11:09:22.460000Z"
  },
  {
    "id": "291bda47-a609-463c-852b-35fbdb1668f4",
    "form_title": "Project Form",
    "description": "Residential project details and developer registration form",
    "is_active": true,
    "field_count": 29,
    "created_at": "2026-11-20T11:09:22.460000Z",
    "updated_at": "2026-11-20T11:09:22.460000Z"
  }
]
```

---

### `GET /forms/{form_id}`
Retrieves a complete form definition along with all its active fields sorted by `display_order`.

- **Access:** `Super Admin`, `Manager`, `Employee`

**Response `200 OK`:**
```json
{
  "id": "5521e888-269f-49dd-a532-f00415468cb9",
  "form_title": "Lead Format",
  "description": "Client lead capture form for prospective property buyers",
  "is_active": true,
  "field_count": 26,
  "created_at": "2026-11-20T11:09:22.460000Z",
  "updated_at": "2026-11-20T11:09:22.460000Z",
  "fields": [
    {
      "id": "c1397bd7-d52a-4d64-af98-3f0af84cf26d",
      "form_id": "5521e888-269f-49dd-a532-f00415468cb9",
      "field_name": "Customer Name",
      "field_type": "text",
      "is_required": true,
      "display_order": 1,
      "options": null,
      "is_active": true,
      "created_at": "2026-11-20T11:09:22.460000Z",
      "updated_at": "2026-11-20T11:09:22.460000Z"
    },
    {
      "id": "90e1f487-b5ca-4a0b-9dfc-2ea90098bc14",
      "form_id": "5521e888-269f-49dd-a532-f00415468cb9",
      "field_name": "Configuration",
      "field_type": "select",
      "is_required": true,
      "display_order": 4,
      "options": ["1 BHK", "2 BHK", "3 BHK", "4 BHK", "Plotting", "Commercial (Shop,office space)", "Other"],
      "is_active": true,
      "created_at": "2026-11-20T11:09:22.460000Z",
      "updated_at": "2026-11-20T11:09:22.460000Z"
    }
  ]
}
```

---

### `POST /forms`
Creates a new custom form.

- **Access:** `Super Admin` only

**Request Body:**
```json
{
  "form_title": "Site Visit Feedback Form",
  "description": "Feedback form collected after customer site visit",
  "is_active": true
}
```

---

### `PUT /forms/{form_id}`
Updates a form's title, description, or `is_active` status.

- **Access:** `Super Admin` only

**Request Body:**
```json
{
  "form_title": "Updated Site Visit Feedback",
  "description": "Updated description",
  "is_active": true
}
```

---

### `DELETE /forms/{form_id}`
Soft deletes a form and all associated fields.

- **Access:** `Super Admin` only

---

### `POST /forms/{form_id}/fields`
Adds a new field to an existing form.

- **Access:** `Super Admin` only

**Request Body:**
```json
{
  "field_name": "Overall Rating",
  "field_type": "select",
  "is_required": true,
  "display_order": 1,
  "options": ["Excellent", "Good", "Average", "Poor"],
  "is_active": true
}
```

---

### `PUT /forms/fields/{field_id}`
Updates a field's properties.

- **Access:** `Super Admin` only

**Request Body:**
```json
{
  "field_name": "Overall Rating (1 to 5 Stars)",
  "options": ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"],
  "is_required": true
}
```

---

### `DELETE /forms/fields/{field_id}`
Soft deletes a specific field.

- **Access:** `Super Admin` only

---

### `PUT /forms/{form_id}/reorder-fields`
Bulk updates the display order of fields in a form.

- **Access:** `Super Admin` only

**Request Body:**
```json
{
  "orders": [
    {
      "field_id": "c1397bd7-d52a-4d64-af98-3f0af84cf26d",
      "display_order": 1
    },
    {
      "field_id": "90e1f487-b5ca-4a0b-9dfc-2ea90098bc14",
      "display_order": 2
    }
  ]
}
```

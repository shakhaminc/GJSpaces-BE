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
| `POST` | `/auth/login` | Public | Authenticate user credentials & receive JWT |
| `GET` | `/me` (or `/auth/me`) | Super Admin, Manager, Employee | Retrieve own profile (clean profile details) |
| `GET` | `/users/roles` | Super Admin, Manager | List master roles (`id` and `role_name` only) |
| `POST` | `/users` | Super Admin | Create Manager or Employee |
| `GET` | `/users` | Super Admin, Manager | List all workforce users (with filters) |
| `GET` | `/users/{user_id}` | Super Admin, Manager | Retrieve user details by UUID |
| `DELETE` | `/users/{user_id}` | Super Admin | Soft delete user |
| `POST` | `/attendance/mark-present` | Super Admin, Manager, Employee | Mark present for today & capture `login_time` |
| `PUT` | `/attendance/tasks` | Super Admin, Manager, Employee | Upload / update today's `to_do_list` |
| `POST` | `/attendance/logout` | Super Admin, Manager, Employee | Clock out & capture `logout_time` |
| `GET` | `/attendance/today` | Super Admin, Manager, Employee | View today's attendance record & tasks |
| `GET` | `/attendance/my-history` | Super Admin, Manager, Employee | View own historical attendance logs |
| `GET` | `/attendance` | Super Admin, Manager | View all workforce attendance with user info |

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
Authenticates a user using email or contact number and password. Returns signed JWT access token.

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
  "message": "Authentication successful.",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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

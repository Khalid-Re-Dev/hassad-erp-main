# API Conventions (Future Phases)

## Overview

This document outlines the API conventions that will be followed in future phases when REST API endpoints are implemented.

## General Principles

1. **RESTful Design**: Follow REST principles for resource-based APIs
2. **JSON Format**: All requests and responses use JSON
3. **HTTP Status Codes**: Use standard HTTP status codes appropriately
4. **Versioning**: API versioning via URL path (e.g., `/api/v1/`)
5. **Authentication**: JWT-based authentication
6. **Authorization**: Role-based access control (RBAC)

## URL Structure

\`\`\`
/api/v1/{resource}/{id}/{sub-resource}
\`\`\`

Examples:
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}` - Get company details
- `GET /api/v1/companies/{id}/branches` - List company branches
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

## HTTP Methods

- **GET**: Retrieve resource(s)
- **POST**: Create new resource
- **PUT**: Update entire resource
- **PATCH**: Partial update of resource
- **DELETE**: Delete resource (soft delete)

## Response Format

### Success Response

\`\`\`json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Example"
  },
  "message": "Operation successful"
}
\`\`\`

### Error Response

\`\`\`json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
\`\`\`

### List Response

\`\`\`json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
\`\`\`

## Status Codes

- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

## Authentication

JWT tokens will be used for authentication:

\`\`\`
Authorization: Bearer {jwt_token}
\`\`\`

## Pagination

Query parameters for pagination:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

## Filtering

Query parameters for filtering:

- `filter[field]=value`: Filter by field value
- `search=query`: Full-text search

## Sorting

Query parameter for sorting:

- `sort=field`: Sort ascending
- `sort=-field`: Sort descending

## Field Selection

Query parameter for field selection:

- `fields=field1,field2`: Return only specified fields

## Implementation Notes

These conventions will be implemented in Phase 2+ when building the API layer.

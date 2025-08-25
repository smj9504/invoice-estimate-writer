# Admin Interface Setup Guide

## Current Status

The SQLAdmin interface has been integrated into the FastAPI application but requires proper initialization order to work correctly.

## Problem Identified

SQLAdmin needs to be initialized after:
1. FastAPI app creation
2. SessionMiddleware setup (required for authentication)
3. CORS middleware setup

But before:
1. The server starts accepting requests

## Solution Implemented

### Files Modified:

1. **app/main.py** - Added SessionMiddleware and admin initialization
2. **app/admin.py** - Complete admin interface with authentication and model views
3. **app/admin_app.py** - Centralized admin creation logic

### How to Access Admin

1. Start the server:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the admin interface:
- URL: http://localhost:8000/admin
- Username: `admin`
- Password: `admin123`

## Admin Features

The admin interface provides full CRUD operations for:

1. **Companies (회사)** - Company management
2. **Invoices (송장)** - Invoice management
3. **Invoice Items (송장 항목)** - Invoice line items
4. **Estimates (견적서)** - Estimate management
5. **Estimate Items (견적 항목)** - Estimate line items
6. **Plumber Reports (배관공 보고서)** - Plumber report management
7. **Documents (문서)** - Document tracking

All interfaces include:
- Korean labels for better usability
- Search functionality
- Sorting capabilities
- Pagination
- Status indicators with icons
- Currency formatting

## Security Note

The current implementation uses hardcoded credentials for development. For production:

1. Change the admin credentials
2. Implement proper user authentication
3. Use environment variables for sensitive data
4. Add role-based access control

## Troubleshooting

If the admin interface doesn't load:

1. Check that SQLite database is being used (development mode)
2. Verify SessionMiddleware is configured
3. Ensure the database tables are created
4. Check server logs for initialization errors

## Alternative Access Methods

If the integrated admin doesn't work, you can use:

1. **Test Admin Script**: `python test_admin.py` (runs on port 8002)
2. **Direct Database Access**: Use SQLite browser to view `mjestimate_dev.db`
3. **API Endpoints**: Use the REST API endpoints directly via `/docs`

## Next Steps for Production

1. Replace hardcoded authentication with proper user management
2. Add SSL/TLS for secure access
3. Implement audit logging for admin actions
4. Add data export/import functionality
5. Customize the admin UI theme to match brand
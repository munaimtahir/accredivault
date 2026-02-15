# Prompt 3 — TODO Checklist

- [x] Add djangorestframework-simplejwt to requirements + rebuild
- [x] Update DRF settings to IsAuthenticated + JWTAuthentication
- [x] Add SIMPLE_JWT settings
- [x] Implement canonical Groups: ADMIN/MANAGER/AUDITOR/DATA_ENTRY/VIEWER
- [x] Add apps/users permissions.py with RBAC permission classes
- [x] Implement /auth/login, /auth/refresh, /auth/me endpoints
- [x] Implement /users CRUD + role assignment + reset-password (ADMIN only)
- [x] Add seed_roles_and_admin management command
- [x] Enforce RBAC across standards/evidence/compliance/audit apps
- [x] Ensure /health remains AllowAny
- [x] Add backend tests for auth + RBAC matrix
- [x] Update frontend api.ts with auth wrapper + refresh retry logic
- [x] Replace Login.tsx placeholder with real login
- [x] Gate App.tsx by auth; add Logout + role-aware nav
- [x] Add Users.tsx (ADMIN only) + styling
- [x] Add Audit.tsx (ADMIN/MANAGER/AUDITOR) + styling
- [x] Add scripts/verify_prompt3.sh
- [x] Update README.md + docs/TODO_CHECKLIST.md + frontend login note

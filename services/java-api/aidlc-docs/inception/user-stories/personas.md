# User Personas - Profile Update Feature

## Overview
This document defines the user personas for the profile update feature. These personas represent the different types of users who will interact with the profile update functionality, each with distinct capabilities, goals, and authorization levels.

---

## Regular User (Sarah Thompson)

### Demographics
- **Role**: Standard Application User
- **Experience Level**: Intermediate
- **Technical Proficiency**: Medium
- **Age Range**: 25-45
- **Context**: Uses the application regularly for their daily work activities

### Goals
- Maintain up-to-date personal information in the system
- Keep email address current for notifications and communication
- Update display name to reflect preferences or changes
- Quickly and easily make profile changes without assistance

### Motivations
- **Accuracy**: Ensure personal information is correct for communication purposes
- **Control**: Maintain ownership and control over personal data
- **Efficiency**: Complete profile updates quickly without administrative intervention
- **Privacy**: Update information securely and confidentially

### Pain Points
- **Current Limitation**: Unable to update own profile information independently
- **Dependency**: Must request administrators to make simple profile changes
- **Delays**: Waiting for administrative help for routine updates
- **Inconvenience**: Cannot update email when it changes, causing missed notifications

### Capabilities in System
- **Self-Update Authority**: Can update own name and email fields
- **View Access**: Can view own complete profile information
- **Authentication**: Uses HTTP Basic authentication to access system
- **Restricted Fields**: Cannot modify own role or active status

### Authorization Rules
- ✅ **Allowed**: Update own name (PUT /api/users/{ownUserId})
- ✅ **Allowed**: Update own email (PUT /api/users/{ownUserId})
- ✅ **Allowed**: View own profile details
- ❌ **Restricted**: Cannot update other users' profiles (403 Forbidden)
- ❌ **Restricted**: Cannot change own role
- ❌ **Restricted**: Cannot change own active status
- ❌ **Restricted**: Cannot access admin-only functions

### User Journey
Sarah logs into the application using her credentials. She navigates to her profile section and realizes her email address has changed due to a company reorganization. She clicks "Edit Profile," updates her email address to the new one, and submits the changes. The system validates the new email, checks that it's not already in use, and confirms the update. Sarah receives confirmation that her profile has been updated successfully and can now receive notifications at her new email address.

---

## Administrator (Michael Chen)

### Demographics
- **Role**: System Administrator
- **Experience Level**: Expert
- **Technical Proficiency**: High
- **Age Range**: 30-50
- **Context**: Manages users and system configuration for the organization

### Goals
- Manage user accounts across the entire system
- Update any user's profile information when needed
- Grant or revoke user privileges by changing roles
- Deactivate or reactivate user accounts based on organizational needs
- Maintain system integrity and user data accuracy

### Motivations
- **System Management**: Efficiently administer all user accounts
- **User Support**: Help users with profile updates when they cannot do it themselves
- **Security**: Manage user roles and access levels appropriately
- **Compliance**: Ensure user data meets organizational standards
- **Operational Excellence**: Keep the system running smoothly with accurate user data

### Pain Points
- **Current Limitation**: No REST API endpoint to perform profile updates programmatically
- **Manual Processes**: Must use database tools for user management tasks
- **Lack of API**: Cannot integrate user management into existing admin workflows
- **Support Burden**: Users depend on admins for routine profile updates

### Capabilities in System
- **Full Update Authority**: Can update any user's name, email, role, and active status
- **User Management**: Can view and modify all user profiles
- **Role Assignment**: Can grant or revoke ROLE_ADMIN or ROLE_USER
- **Account Control**: Can activate or deactivate user accounts
- **Authentication**: Uses HTTP Basic authentication with ROLE_ADMIN privileges

### Authorization Rules
- ✅ **Allowed**: Update any user's name (PUT /api/users/{anyUserId})
- ✅ **Allowed**: Update any user's email (PUT /api/users/{anyUserId})
- ✅ **Allowed**: Change any user's role (PUT /api/users/{anyUserId})
- ✅ **Allowed**: Change any user's active status (PUT /api/users/{anyUserId})
- ✅ **Allowed**: View any user's profile details
- ✅ **Allowed**: Perform partial updates (update some fields, leave others unchanged)
- ✅ **Allowed**: Update own profile with full capabilities

### User Journey
Michael receives a support ticket that a user's email address needs to be updated urgently because they're locked out of receiving notifications. He authenticates to the system with his admin credentials, navigates to the user management API, and makes a PUT request to `/api/users/{userId}` with the updated email address. The system validates the admin's authorization, checks the new email for uniqueness, and updates the user's profile immediately. Michael confirms the change was successful and notifies the user that their email has been updated.

Alternatively, when an employee leaves the company, Michael makes an API call to update the user's `active` status to `false`, effectively deactivating their account without deleting their data, ensuring audit trail compliance.

---

## Authorization Matrix

| Action | Regular User (Sarah) | Administrator (Michael) |
|--------|---------------------|------------------------|
| Update own name | ✅ Allowed | ✅ Allowed |
| Update own email | ✅ Allowed | ✅ Allowed |
| Update own role | ❌ Forbidden | ✅ Allowed |
| Update own active status | ❌ Forbidden | ✅ Allowed |
| Update other user's name | ❌ Forbidden | ✅ Allowed |
| Update other user's email | ❌ Forbidden | ✅ Allowed |
| Update other user's role | ❌ Forbidden | ✅ Allowed |
| Update other user's active status | ❌ Forbidden | ✅ Allowed |
| View own profile | ✅ Allowed | ✅ Allowed |
| View other user's profile | ❌ Forbidden (assumed) | ✅ Allowed |

---

## Persona Usage in Stories

These personas will be referenced in user stories to clearly indicate:
- **Who** the story is for (Regular User vs Administrator)
- **What capabilities** they have in the system
- **What authorization rules** apply to their actions
- **What value** the feature provides to each persona

Stories will be organized by persona to ensure clear separation between self-update capabilities and administrative capabilities.

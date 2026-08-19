# Roles and Permission Model

Permissions are capabilities, not client-side role checks. A role is a tenant-scoped bundle of permissions. Platform administration uses a separate platform scope.

## Baseline matrix

| Capability | Learner | Mentor | Instructor | Team lead / manager | Learning admin | Org admin | Platform admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Manage own profile/private data | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create personal roadmap/notes/code | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Review explicitly shared learner work |  | ✓ | ✓ | ✓ | ✓ | ✓ | policy only |
| Create organization learning content |  |  | ✓ |  | ✓ | ✓ |  |
| Assign roadmap/course |  |  | ✓ | team | ✓ | ✓ |  |
| View aggregate team analytics |  |  | cohort | team | ✓ | ✓ | operational only |
| Manage teams and memberships |  |  |  | team | ✓ | ✓ |  |
| Configure organization roles/policy |  |  |  |  |  | ✓ |  |
| Search organization audit log |  |  |  |  | limited | ✓ | tenant support only |
| Manage tenants/plans/system policy |  |  |  |  |  |  | ✓ |

## Authorization decision

Every protected request is evaluated as:

`authenticated user + active membership + tenant + permission + object visibility + resource state`

- The tenant comes from a validated route/header context, never solely from request JSON.
- Ownership does not bypass organization policy, and organization membership does not imply access to private notes.
- Managers receive aggregate metrics by default. Row-level evidence requires a separate sharing permission.
- Platform administrators do not receive blanket content access; support access is time-bound, justified, and audited.

## Initial permission codes

`organization.view`, `organization.manage`, `member.view`, `member.invite`, `member.manage`, `roadmap.create`, `roadmap.assign`, `learning.view_shared`, `analytics.view_team`, `audit.view`, `policy.manage`.


# Frontend Map, Components, and Repository Structure

## Page map

```text
Public: landing, pricing-ready, login, register, verify, reset
Onboarding: identity -> goals -> skills -> availability -> preferences -> plan review
Personal app:
  dashboard
  my-learning / roadmaps / roadmap/:id / study/:activityId
  videos / notes / code / challenges / projects
  quizzes / flashcards / goals / analytics / career-readiness
  notifications / settings / integrations / privacy
Organization:
  org/:slug/dashboard / people / teams / learning / reports / audit / settings
Platform admin:
  tenants / plans / health / moderation / audited-support
```

## Component hierarchy

```text
RootProviders
  AuthProvider / QueryProvider / ThemeProvider / OrganizationProvider
  AppShell
    SidebarNavigation
    TopBar (search, timer, notifications, organization switcher, profile)
    RouteContent
      PageHeader / Breadcrumbs
      MetricCard / DataTable / ChartPanel / ActivityFeed
      EmptyState / ErrorState / Skeleton
      Domain forms and workspaces
  DialogHost / ToastHost / CommandPalette
```

## Recommended repository

```text
lear nos/
  frontend/
    app/ components/ features/ lib/ hooks/ stores/ types/ tests/
  backend/
    config/ core/
    accounts/ organizations/ permissions/ learning/ roadmaps/ content/
    videos/ study_sessions/ notes/ coding/ challenges/ projects/
    quizzes/ flashcards/ goals/ analytics/ ai/ integrations/
    notifications/ audit/ subscriptions/
  services/execution-controller/
  runners/python/ runners/javascript/
  infrastructure/docker/ kubernetes/ terraform/ observability/
  docs/product/ docs/architecture/ docs/planning/ docs/operations/
```

Each backend domain follows `models`, `selectors`, `services`, `policies`, `tasks`, `api`, `events`, `admin`, `migrations`, and `tests` as needed. Empty ceremony is avoided until the domain requires it.


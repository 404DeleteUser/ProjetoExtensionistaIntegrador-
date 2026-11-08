# Rule: Domain Isolation

## Objective

Ensure that changes within one domain do not cause unintended side effects in other domains or parts of the application.

The primary goal is to preserve system stability, maintain domain boundaries, and prevent regressions when implementing changes.

## 1. Domain Isolation Principles

- Changes must remain isolated to the domain and scope of the requested task whenever possible.
- Do not modify other domains unless the task explicitly requires it or a verified dependency makes it necessary.
- Preserve existing behavior and contracts across domain boundaries.
- Do not introduce unintended coupling between domains.
- Avoid changes to shared components, utilities, interfaces, or abstractions that could affect unrelated parts of the application without a clear justification.
- Treat shared modules and public interfaces as high-impact areas requiring additional scrutiny.
- Never assume that a change is safe simply because it passes tests within the modified domain.

## 2. Mandatory Checks Before Modifying Code

Before modifying any files, perform the following checks.

### Step 1: Identify the Change Scope

- List all files expected to be modified to complete the requested task.
- Identify the domain or domains to which each file belongs.
- Explain why each file needs to be changed.
- Identify shared modules, public interfaces, and cross-domain dependencies within the planned scope.

Do not begin implementation until the expected change scope has been identified.

If additional files become necessary during implementation, reassess the scope and impact before modifying them.

### Step 2: Map Dependencies and Potential Impact

Use repository search tools such as `Grep` and `Glob` to identify files and components that import, reference, extend, implement, invoke, or otherwise depend on the files being modified.

Check, when applicable:

- Direct and indirect imports and dependencies.
- Function, method, and class call sites.
- Shared utilities, services, components, and interfaces.
- API endpoints, event handlers, and event consumers.
- Database models, schemas, migrations, and queries.
- Configuration files and dependency injection registrations.
- Tests, mocks, fixtures, and test utilities.
- Cross-domain communication and integration points.

Determine which other domains or application components could be affected by the proposed changes.

Do not rely solely on direct imports when indirect dependencies, runtime registration, dynamic imports, events, or dependency injection may be involved.

If dependency analysis is incomplete, explicitly state the limitation and avoid claiming that the change is fully isolated.

### Step 3: Analyze Public Signatures and Contracts

Before modifying an existing function, method, class, interface, or other public contract, compare its current signature with the proposed signature.

Check for changes to:

- Input parameters and their types.
- Return values and output types.
- Optional parameters and default values.
- Exceptions and error-handling behavior.
- Public methods, properties, and exported symbols.
- API request and response schemas.
- Events, message payloads, and shared data structures.
- Observable behavior relied upon by other domains.

If a public signature or contract must change:

1. Identify the affected consumers and integration points.
2. Explain the proposed change and its potential impact.
3. Alert the user before proceeding with a potentially breaking change.
4. Update all affected usage sites when the change is authorized and necessary.
5. Update relevant tests, mocks, documentation, and contracts.
6. Verify compatibility and regression risks across affected domains.

Do not silently introduce breaking changes or leave known consumers incompatible.

Prefer backward-compatible changes when they satisfy the requirements.

## 3. Implementation Rules

- Modify only the files required to fulfill the approved task.
- Preserve domain boundaries and existing architectural conventions.
- Avoid changing shared behavior when a domain-specific solution is sufficient.
- Do not alter unrelated business rules, workflows, or data models.
- If a shared component must change, analyze its consumers before implementation.
- If the implementation reveals an unexpected cross-domain dependency, reassess the impact before continuing.
- If the required changes exceed the original scope or introduce significant risk, pause and consult the user.

## 4. Mandatory Regression Verification

After implementation, verify that the changes do not introduce unintended effects outside the target domain.

When applicable:

- Run tests for the modified domain.
- Run tests for directly dependent domains and components.
- Run relevant integration and contract tests.
- Run type checks, linting, and build validation.
- Verify public interfaces and all affected call sites.
- Check for unexpected changes in unrelated files.
- Review the final diff for accidental scope expansion.

Prioritize tests according to the dependency impact analysis.

If broader regression tests are available and feasible, run them. If they cannot be executed, report which checks remain outstanding and why.

Passing tests in the target domain alone is not sufficient evidence that cross-domain behavior remains correct.

## 5. Definition of Done

A task is complete only when:

- [x] The expected file changes have been identified and reviewed.
- [ ] Relevant dependencies and affected domains have been mapped.
- [ ] Public signatures and contracts have been checked.
- [ ] All necessary consumers have been updated for authorized contract changes.
- [ ] Domain-specific behavior remains correct.
- [ ] Relevant cross-domain regression checks have been executed.
- [ ] No known unintended side effects remain unresolved.
- [ ] Any unverified dependencies, failed tests, or remaining risks are documented.

If any required verification cannot be completed, explicitly report the limitation instead of claiming complete isolation.

## Fundamental Principle

**A change in one domain must not unintentionally break another domain or any other part of the application.**

Every change must be evaluated not only for what it modifies, but also for what depends on it.

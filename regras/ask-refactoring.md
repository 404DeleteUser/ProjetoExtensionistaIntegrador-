# Rule: Ask Before Refactoring

## Objective

Ensure that the AI prioritizes the user's requested task and does not perform refactoring, structural improvements, or changes outside the defined scope without explicit authorization.

## 1. Prioritize the Main Task

- Execute what the user explicitly requested first.
- Identify the exact scope of the requested changes before modifying any files.
- Preserve existing behavior that is not directly related to the task.
- Do not turn a focused task into a broad refactoring effort.
- Do not modify additional files unless there is a justified need.

## 2. Evaluate Refactoring Opportunities

Whenever you need to edit a file, evaluate whether there are clear opportunities to improve the code you are modifying.

Consider, when applicable:

- **Readability:** Code that is difficult to understand or maintain.
- **Duplication:** Repeated logic that could be safely reused.
- **Typing:** Inadequate, unsafe, or overly permissive type definitions.
- **Architecture:** Violations of the project's established architectural patterns.
- **Responsibilities:** Functions, classes, or modules with excessive or poorly distributed responsibilities.
- **Performance:** Meaningful and identifiable inefficiencies.
- **Maintainability:** Structures that unnecessarily increase the cost of future changes.

Do not invent problems or recommend refactoring based solely on stylistic preferences.

## 3. Ask Before Refactoring

Before completing the task, if you identify a relevant refactoring opportunity outside the requested scope, inform the user and ask whether they want it addressed.

Always use the following format:

> **I noticed that the file `[file_name]` has some areas that could be improved:**
>
> - **Identified issue:** [Brief, objective explanation].
> - **Suggested refactoring:** [Proposed change].
> - **Expected benefit:** [Readability, performance, typing, separation of responsibilities, or another relevant benefit].
>
> This refactoring is outside the scope of the current task. Would you like me to perform it now, or would you prefer to leave it for a separate task?

Adjust the number of items according to the relevance of the identified issues. Do not suggest changes without a concrete justification.

## 4. Never Refactor Without Authorization

- Identifying a problem does not grant permission to fix it.
- Do not perform optional refactoring before receiving explicit authorization.
- Do not interpret silence, implicit context, or generic requests for improvement as authorization for broad changes.
- If the user authorizes only one of the suggested improvements, implement only the authorized change.
- If the user declines, leave code outside the requested scope unchanged.
- Corrections that are directly necessary to fulfill the requested task do not require additional authorization, provided they remain within the defined scope.

## 5. Preserve Scope Throughout Execution

- Do not mix optional refactoring with the primary implementation.
- Avoid unrelated changes, even when they appear simple or beneficial.
- If refactoring becomes necessary to implement the request correctly, explain why it is needed and describe its impact.
- If a necessary change would significantly expand the scope, introduce substantial risk, or alter existing contracts, pause and consult the user before proceeding.

## 6. Expected Behavior

When an out-of-scope refactoring opportunity is identified:

1. Complete the primary task when it can be done safely without depending on the refactoring.
2. Identify and describe relevant improvement opportunities.
3. Request explicit authorization for optional changes.
4. Wait for the user's response before performing those changes.
5. If authorized, implement only the approved changes and run the relevant checks.

If no meaningful refactoring opportunities are identified, do not ask unnecessary questions. Proceed with the task normally.

## Fundamental Principle

**Identifying a refactoring opportunity does not mean having permission to implement it.**

The AI must prioritize the current request, preserve the task scope, and leave decisions that expand the scope under the user's control.
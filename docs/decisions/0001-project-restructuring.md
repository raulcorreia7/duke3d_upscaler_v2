# 0001 - Project Restructuring

## Status
Accepted

## Context
The Duke3D Upscaler v2 project had 21 items in the root directory, making it cluttered and difficult to navigate. Users were unclear where to place files, and the structure didn't follow industry best practices for maintainability.

## Decision
Restructure the project to:
- Reduce root directory items from 21 to 11
- Create clear separation of concerns with `src/`, `files/`, `tools/`, `docs/`
- Simplify user workflow: drop files in `files/input/`, run `make all`, get output in `files/output/`
- Improve maintainability and scalability

## Consequences
- **Positive**: Cleaner structure, better user experience, improved maintainability
- **Negative**: Breaking changes requiring migration
- **Neutral**: Same functionality with better organization

## Implementation
- Create 30 detailed tasks for systematic restructuring
- Update all paths and references
- Maintain backward compatibility where possible
- Provide migration guide for existing users
# Assembly Workflow - Next Implementation

Development branch: `feature/assembly-workflow`

## Goal

Upgrade automatic companion items into synchronized estimating assemblies without changing the existing costing rules.

## Required behavior

1. Primary catalog items remain the production-driving rows.
2. Companion rows remain material-only and do not add crew or equipment days.
3. EA companion quantities always round upward.
4. Editing a primary quantity recalculates every automatic companion from its stored ratio.
5. Existing automatic companions are replaced during synchronization so stale or duplicate rows cannot accumulate.
6. Deleting a primary continues to delete its automatic companions.
7. Manual rows are never changed by assembly synchronization.
8. Pipe edits must recalculate bedding from the selected bedding rule.

## Planned service API

- `update_line_item(...)` updates the primary snapshot and recalculates bedding where applicable.
- `sync_line_companions(parent_line_item_id)` deletes/rebuilds only auto-generated children.
- `assembly_preview(material_rate_id, quantity)` returns companion quantities before database insertion.

## UI

- Add an Edit action to primary line items.
- Show an assembly summary beneath a primary item when it owns companions.
- Keep generated companion rows indented and labeled AUTO.
- Display a success message stating how many companions were recalculated.

## Safety

Implementation must remain on this feature branch until tested locally. The `main` branch should not be modified until the assembly edit/sync workflow passes domain and application tests.

# Assembly workflow milestone

This branch develops estimate assemblies and automatic companion materials.

Planned behavior:
- Primary catalog items may define one or more companion rules.
- Companion quantity is primary quantity divided by the rule ratio.
- EA companions round up to whole units.
- Updating a primary quantity must resynchronize generated companion quantities.
- Deleting a primary item deletes its generated companions.
- Generated companion items remain material-only and do not create duplicate production days.
- Bedding and depth calculations remain attached to the primary line item.

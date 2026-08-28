# New Estimator V4

**Launch address:** http://127.0.0.1:5052

V4 is a separate development build. It uses port 5052 so it can run alongside the older estimator and V3.1 without a port collision. Every page shows a visible **New Estimator V4** badge.

## What V4 adds

V4 keeps the project/section/rate-catalog, production, equipment-tiering, tax, depth-band, and bedding logic from V3.1 and adds **automatic companion materials**.

When a catalog item has a companion rule, adding that primary item automatically creates the related material-only line item(s). Examples already in the seeded catalog include:

- 14Ga Wire Back Silt Fence -> T-Posts
- TEMP Plastic Fence -> T-Posts
- C900 MJ 90 bends -> matching gasket + Mega Lug
- C900 MJ tees -> matching gasket + Mega Lug

The stored ratio is interpreted as **primary units per one companion unit**. Example: a ratio of 6 means one T-post for every 6 LF of fence. Companion items measured as `EA` are rounded up to whole units.

Automatic companions:

- snapshot the companion material's current catalog cost when generated;
- do **not** add separate production days, labor days, or equipment days;
- appear as indented `AUTO` rows beneath the estimate;
- are deleted automatically when the primary estimate line is removed.

A **Companion Rules** page lets you review every currently configured automatic relationship.

## Existing estimating features

- Projects and scope sections: Erosion, Demo, Dirt, Under Cut, Sewer, Water, Storm Drain, Other
- Reusable labor, equipment, and material catalogs
- Production-rate-driven duration
- Crew cost using 8 regular + 2 overtime hours per assigned role
- Day/week/month equipment rental comparison plus fuel
- Material + bedding + labor + equipment rollup
- Overhead, profit, and tax/no-tax totals
- Snapshot pricing on estimate line items
- Depth-band production and depth pricing
- 440 Mississippi/Tennessee bedding-rule rows
- Bedding quantity calculation in CY
- Confidence/prohibition handling and `VERIFY BEFORE BID` warnings
- Pipe material, size, fitting, joint, application, and jurisdiction reference data

## Start on Windows

1. Extract the ZIP into a new folder.
2. Open that folder.
3. Double-click **Start Estimator.bat**.
4. Your browser should open automatically at `http://127.0.0.1:5052`.

The first launch creates `.venv` and installs the packages in `requirements.txt`.

## Suggested first test

1. Create a project.
2. Add an **Erosion** section.
3. Add `14Ga Wire Back Silt Fence` with quantity `120 LF`.
4. V4 should automatically add `20 EA T-Posts` as an indented AUTO line.
5. Remove the fence line; its T-Post line should disappear with it.

For Water, add one of the seeded C900 MJ bends/tees to see gasket and Mega Lug companions generated 1:1.

## Build a standalone .exe (no Python required to run it)

1. Double-click **build_exe.bat**. First run installs `pyinstaller` into `.venv` and can take a few minutes.
2. When it finishes, your executable is at `dist\CivilEstimator.exe`.
3. Copy that single file into its own folder (it creates `estimator.db` next to itself on first launch, seeded from this repo's catalog) and double-click it. Your browser opens automatically at `http://127.0.0.1:5052`.

Re-run `build_exe.bat` any time after pulling changes to rebuild the .exe.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The test suite includes companion-ratio rounding, legacy costing, equipment tiering, bedding geometry, and depth pricing.

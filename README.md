# New Estimator V3.1

**Launch address:** http://127.0.0.1:5051

V3.1 uses port 5051 so it can run alongside older local estimator versions that use port 5000. A visible `New Estimator V3.1` badge appears in the lower-right corner of every page.

# New Estimator V3

A separate local web estimator for construction estimating. V3 keeps the V2 bid/section/rate-catalog foundation and adds pipe depth and regulatory bedding calculations using the supplied Mississippi and Tennessee bedding estimating workbooks.

## Included in V3

- Projects with scope sections (Dirt, Sewer, Water, Storm Drain, Demo, Erosion, Under Cut, etc.)
- Reusable labor, equipment, and material catalogs
- Production-rate-driven line-item duration
- Crew cost using 8 regular + 2 overtime hours per assigned role
- Day/week/month equipment rental comparison plus fuel
- Material + bedding + labor + equipment rollup
- Overhead, profit, and tax/no-tax totals
- Snapshot rates on bid line items
- Depth-band selection for catalog rows flagged as depth-priced
- Pipe bedding quantity calculation in CY from pipe OD, bedding depth, haunch/envelope geometry, and trench width
- 440 imported MS/TN bedding-rule rows
- Bedding rule browser with confidence and prohibition flags
- Visible VERIFY BEFORE BID warnings for source rows marked assumed

## Important bedding-data behavior

The app preserves the source workbook's own confidence labels. In particular, many Mississippi rows are marked as assumed because the source workbook says the exact MDOT Table 603-I values still need verification. The program will calculate those rows, but it displays a warning on the estimate. Prohibited rows are blocked rather than treated as valid zero-cost selections.

Bedding cost is calculated as:

`bedding quantity (CY) x bedding material unit cost ($/CY)`

The regulatory geometry determines quantity. You still enter the current supplier price per CY for the bedding material when adding the pipe line item.

## Start on Windows

1. Extract the ZIP.
2. Open the `new_estimator_v3` folder.
3. Double-click **Start Estimator.bat**.

On the first run it creates a local Python virtual environment and installs the required packages. It then opens:

`http://127.0.0.1:5051`

If Windows does not open the browser automatically, type that address into Chrome or Edge.

## Suggested pipe workflow

1. Create/edit a project and enter `TN` or `MS` for State.
2. Choose the exact **Bedding jurisdiction** from the provided list.
3. Add a **Sewer** or **Storm Drain** section.
4. Add a catalog pipe item.
5. For depth-priced rows, choose the depth band.
6. For rows labeled `bedding calc`, choose the matching bedding rule and enter the current bedding material price per CY.
7. Review any confidence warning before using the number in a bid.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The domain tests include a bedding geometry check against a known row from the supplied Mississippi workbook.

## Optional data refresh

The packaged database already contains the bedding data. If the source workbooks are later revised, `scripts/import_bedding_workbooks.py` can refresh the rules when given the updated workbook paths. `scripts/import_legacy_catalogs.py` can refresh reusable rate/reference catalogs from the older estimator database without importing its old bids.

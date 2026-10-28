# Grain statements (Guide Section 5)

**Status:** draft for review (Oct 28, 2026). Profiled from the files in `data/` with pandas.
The row counts below describe the *original* files. The app never relies on them: it counts
rows from whatever data is currently loaded.

## Grain table

| Table | Source file / sheet | One row = ___ | Key column(s) | Row count | Contains revenue? |
|---|---|---|---|---|---|
| Stores | `data/Support_EX_B_Stores.csv` (**tab-separated**) | one store / sales outlet (20 physical stores + the website, SH00) | `ID` | 21 | No |
| Categories | `data/Categories.csv` (from Access) | one product category | `Category ID` | 5 | No |
| Products | `data/Products.csv` (from Access) | one product | `Product ID` | 20 | No |
| Sales | `data/Sales.csv` (from Access) | one store's revenue for one product in one month | `Sales ID` (also unique on `Store ID` + `Product ID` + month) | 25,200 | **Yes** (`Revenue`) |
| Survey Results | `data/Support_EX_B_Survey.xlsx`, sheet `Survey Results` (headers on row 3) | one store's survey result for one year | `Survey ID` (format `SH01_25`) | 105 | No |

## Evidence for each grain

- **Stores:** `ID` is unique with no blanks. City is *not* unique (two Orlando stores, SH01 and SH08), so it must never be used as a key.
- **Categories / Products:** each ID is unique with no blanks. `Products.csv` has **no category column**. Which category a product belongs to is recorded only in `Sales.Category ID`. Every product appears under exactly one category in Sales.
- **Sales:**
  - `Sales ID` is unique.
  - The combination store × product × month is also unique: 21 stores × 20 products × 60 months = 25,200, a complete grid.
  - Dates are one per month (Jan 2025 – Dec 2029). Most are month-end dates, but Feb 2028 is stored as `2028-02-28` (2028 is a leap year), so group by **month**, not by exact date.
  - `StoreYear` always equals `Store ID` + `_` + the two-digit year of `Date`.
- **Survey Results:**
  - `Survey ID` is unique; 21 stores × 5 years = 105 rows.
  - `Year` is text (`Y2025`), not a number.
  - SH00 (Website) has 5 rows with blank `Satisfaction` and `Interest`. That's expected, because there's no in-store survey for a website.

## Relationships (verified key coverage, no joins performed yet)

| From (many) | To (one) | Join columns | Unmatched rows in Sales |
|---|---|---|---|
| Sales | Stores | `Store ID` → `ID` | 0 |
| Sales | Products | `Product ID` → `Product ID` | 0 |
| Sales | Categories | `Category ID` → `Category ID` | 0 |
| Sales | Survey Results | `StoreYear` → `Survey ID` | 0 |

Every lookup key is unique, so each of these joins is many-to-one. A many-to-one join should not
change the Sales row count or the revenue sum. This will be confirmed with `check_merge()` and
recorded in the merge-check log in Checkpoint 2.

**Difference from our Power BI model:** Power BI reached Stores *through* the survey table
(Sales → Survey Results → Stores). We plan to join Sales → Stores directly on `Store ID`, because
it's simpler and doesn't depend on the survey file. The two routes give the same channel totals,
because SH00 has survey rows. That comparison is a validation point.

**Survey grain warning:** the survey is one row per store-year, but Sales has ~240 rows per
store-year. Joining the survey onto Sales would repeat each satisfaction score ~240 times.
To compare satisfaction with revenue, first total revenue to store-year, then attach the survey.
Never average satisfaction from the joined Sales table.

## Merge-check log (to fill in during Checkpoint 2)

| Merge | Rows before | Rows after | Revenue sum before | Revenue sum after | Explanation |
|---|---|---|---|---|---|
| Sales → Stores | | | | | |
| Sales → Products | | | | | |
| Sales → Categories | | | | | |
| Store-year revenue → Survey | | | | | |

# Validation: Power BI vs. Streamlit app (Guide Section 8)

**Status:** draft started Oct 29, 2026. The Power BI column is filled in; the **App result**
column is filled in once the app calculates revenue (Checkpoint 2, step 2).

**Power BI source:** our submitted report (`docs/powerbi/finishedpowerbi.pbix`). The values are
the chart **data labels**, read from the screenshots in `docs/powerbi/`. The labels are
**rounded** (millions to one decimal place or none, percentages to two decimal places), so a
match means the app's exact value rounds to the Power BI label. Exact tooltip values will be
added if we get them.

## Validation table

| Metric | Power BI result | App result | Match? / Explanation |
|---|---|---|---|
| Total revenue (five years) | Not shown as a number on our report pages. The walkthrough says "about $42 million", and the channel bars add up to 27M + 15M = 42M. | _pending_ | Independent check: **$42,174,440.00**, which agrees with "about $42M". We need an exact Power BI figure (a card visual or tooltip) for a full comparison. |
| Website revenue | 27M ("Total Revenue by Store Type") | _pending_ | Independent check: **$27,218,880.00**, which rounds to 27M. ✓ |
| Brick-and-mortar revenue | 15M ("Total Revenue by Store Type") | _pending_ | Independent check: **$14,955,560.00**, which rounds to 15M. ✓ |
| Revenue by year | 2025: 7.2M · 2026: 8.0M · 2027: 8.8M · 2028: 9.0M · 2029: 9.2M ("Total Revenue by Year") | _pending_ | Independent check: 7,181,750 · 8,016,950 · 8,824,720 · 8,969,470 · 9,181,550, which round to 7.2M / 8.0M / 8.8M / 9.0M / 9.2M. ✓ all five years. |
| Monthly revenue pattern | "Percent of Annual Revenue per Month": Jan 7.74% · Feb 3.83% · Apr 5.15% · Jun 6.50% · Aug 6.45% · Oct 8.31% · Nov 12.71% · Dec 25.61%. Mar, May, Jul and Sep bars have no data labels. | _pending_ | All 8 labelled months match the independent check to two decimal places. ✓ **But the chart's title is misleading; see the note below.** It shows each month's share of the **five-year grand total**, not of each year's total. Our app must label its monthly chart by what it actually calculates. |
| Additional measure: **Chicago store (SH11) revenue by year** | With Chicago selected in the store bar chart: 2025: 0.54M · 2026: 0.41M · 2027: 0.36M · 2028: 0.27M · 2029: 0.18M; five-year bar: 2M | _pending_ | Independent check: 539,740 · 407,390 · 355,730 · 269,100 · 179,130, which round to the five labels ✓. Five-year total **$1,751,090**, which rounds to 2M ✓. That is a **66.8% decline** from 2025 to 2029, while company revenue grew. This measure tests the store filter, and it is the evidence behind the assignment's "Should E-Presso close its Chicago store?" question. |

## Note on the monthly chart's denominator

The chart is titled **"Percent of Annual Revenue per Month"**, but it does not divide by each
year's revenue:

- **How it was built:** step 4 of the walkthrough (`docs/powerbi-walkthrough.md`, line 423)
  sets the measure to *Show value as → **Percent of grand total***. The chart's axis is month
  only, with no year, so each bar is that month's revenue **added up across all five years**,
  divided by the **five-year total** ($42,174,440).
  - Example: November = $5,361,150 / $42,174,440 = **12.71%**.
- **What the title suggests:** a percent of *annual* revenue would divide each month by its own
  year's total (e.g. Nov 2027 / all of 2027), giving 60 values, five per month.
- **Does it change the numbers here?** Only slightly, because E-Presso's seasonal pattern is
  very stable from year to year. The average of the five yearly percentages differs from the
  grand-total percentage by at most 0.02 percentage points (November: 12.73% vs. 12.71%).
  However, single years vary more: November ranges from **12.26% to 13.19%** across
  2025–2029. So the chart describes the five-year pattern, not any one year.
- **Filters change the denominator (confirmed).** In Power BI, "percent of grand total" is
  calculated over whatever is currently filtered. Clicking Brick & Mortar (as the walkthrough
  does at line 428) makes the denominator total brick-and-mortar revenue. Selecting a single
  year would make it that year's total, which is the only case where the title is literally
  accurate.
  - **Observed with Chicago selected** (Audrey's screenshot, Oct 29): the bars changed to
    Jan 7.87% · Feb 3.91% · Apr 5.19% · Jun 6.51% · Aug 6.37% · Oct 8.52% · Nov 13.21% ·
    Dec 24.75%. These match the independent check exactly when the denominator is **Chicago's
    own five-year total** ($1,751,090). Example: Chicago December = $433,320 / $1,751,090 =
    24.75%, compared with 25.61% company-wide. The bars still add up to 100%.
  - Chicago's single years vary even more than the company's: its December share ranges from
    23.93% to 26.25%, and November from 12.77% to 13.74%. A small, declining store makes the
    five-year figure an even rougher guide to any one year.
- **For our app:** label the chart by its denominator, e.g. "Share of revenue by month (% of
  total revenue for the selected period)". State in the caption that the denominator is the
  total for the current filters, and test that the percentages still add up to 100% under
  every filter.

## Note on the store bar chart (drilled down to City)

With Chicago selected, the "Total Revenue by Store Type" chart is drilled down from store type
to **City**. This is fine for Chicago, which has one store (SH11), and Baltimore (SH15,
$1,941,550 ≈ 2M). But **Orlando has two stores**, so Power BI shows one combined Orlando bar:
SH01 $727,080 + SH08 $366,190 = $1,093,270. Our app filters and groups stores by **ID** (with
the city as a label), so it shows the two Orlando stores separately. If we compare
store-level figures with Power BI, Orlando must be compared as the sum of SH01 and SH08.

## Monthly detail (independent check, all 12 months)

| Month | Revenue, all 5 years | % of 5-year total (Power BI's method) | Power BI label | Average of the 5 yearly % | Range of yearly % |
|---|---|---|---|---|---|
| Jan | $3,266,270 | 7.74% | 7.74% | 7.74% | 7.62 – 7.94% |
| Feb | $1,616,410 | 3.83% | 3.83% | 3.83% | 3.77 – 3.89% |
| Mar | $1,873,190 | 4.44% | (no label) | 4.44% | 4.35 – 4.51% |
| Apr | $2,173,470 | 5.15% | 5.15% | 5.15% | 5.05 – 5.28% |
| May | $2,411,110 | 5.72% | (no label) | 5.72% | 5.66 – 5.76% |
| Jun | $2,743,370 | 6.50% | 6.50% | 6.51% | 6.37 – 6.67% |
| Jul | $2,706,590 | 6.42% | (no label) | 6.41% | 6.24 – 6.59% |
| Aug | $2,718,500 | 6.45% | 6.45% | 6.44% | 6.34 – 6.58% |
| Sep | $3,000,500 | 7.11% | (no label) | 7.10% | 6.88 – 7.37% |
| Oct | $3,502,890 | 8.31% | 8.31% | 8.31% | 8.09 – 8.47% |
| Nov | $5,361,150 | 12.71% | 12.71% | 12.73% | 12.26 – 13.19% |
| Dec | $10,800,990 | 25.61% | 25.61% | 25.61% | 25.11 – 26.00% |
| **Total** | **$42,174,440** | **100.00%** | | | |

## Independent check (reproducible)

**What:** total, channel, yearly and monthly revenue, calculated directly from the source files
without using any of the app's code.

**How:** Python and pandas, reading `data/Sales.csv` and the tab-separated
`data/Support_EX_B_Stores.csv`, run from the project folder:

```python
import pandas as pd
sales = pd.read_csv('data/Sales.csv')
stores = pd.read_csv('data/Support_EX_B_Stores.csv', sep='\t')
date = pd.to_datetime(sales['Date'])
sales = sales.merge(stores[['ID', 'StoreType']], left_on='Store ID', right_on='ID', how='left')
total = sales['Revenue'].sum()
print(total)                                                    # five-year total
print(sales.groupby('StoreType')['Revenue'].sum())              # Website vs. Brick & Mortar
print(sales.groupby(date.dt.year)['Revenue'].sum())             # by year
print(sales.groupby(date.dt.month)['Revenue'].sum() / total * 100)  # Power BI's monthly %
```

**Result:** the values in the tables above. The merge kept 25,200 rows, and 0 rows were left
without a store type.

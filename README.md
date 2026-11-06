# Real-World Online Retail Analysis

**Exploratory Data Analysis, Customer Segmentation and Business Insights Using the UCI Online Retail Dataset**

A reproducible, end-to-end data analytics project completed for **YuvaIntern Data Analytics Internship — Task 4**. The project analyses the genuine UCI Online Retail dataset (541,909 transactions) and produces an executed Jupyter notebook, 18 publication-ready visualisations, a 25+ page Word report, and a GitHub-ready repository.

> **Author:** *[Your Name]*, Data Analytics Intern — YuvaIntern
> **Date:** November 2026
> **Dataset DOI:** [10.24432/C5BW33](https://doi.org/10.24432/C5BW33)
> **Submission document (Google Docs, public link):** https://docs.google.com/document/d/1ZnkecSn0G92pgaTV7B5jI8Q99rJ6ae7vQYT2gIaMDN0/edit

---

## 1. Project overview

Online retailers collect large volumes of transaction data but often lack a single, reproducible view of what that data means commercially. This project builds that view for a UK-based online retailer using the complete UCI Online Retail dataset.

The analysis follows a full workflow:

1. **Verify** the genuine dataset against its published dimensions and record a SHA-256 fingerprint.
2. **Inspect** structure, types, memory, missing values, duplicates and distributions.
3. **Assess and clean** with an auditable, issue-by-issue decision log.
4. **Engineer** eleven derived variables with explicit leakage controls.
5. **Explore** univariate, bivariate, time-series, customer, product, geographic and cancellation dimensions.
6. **Test** hypotheses with confidence intervals, Welch t-tests, Mann–Whitney U and chi-square tests, reporting effect sizes.
7. **Segment** customers with an RFM model and quantify each segment's revenue contribution.
8. **Test** the 80/20 rule rather than assuming it.
9. **Visualise** 18 charts, each with a caption and interpretation.
10. **Recommend** six evidence-based actions with KPIs, benefits, risks and limitations.

**No synthetic records were added. No result was hard-coded. Every number is produced by the executed pipeline.**

---

## 2. Business problem

Management needs to understand sales performance, customer purchasing behaviour, product demand, geographical performance and cancellation patterns, but has no consolidated evidence base. Four specific problems motivate the work:

- Revenue reporting mixes sales, cancellations, returns, zero-priced lines and non-product charges, so headline totals are not comparable.
- Customer value is not segmented, so a loyal high-value account cannot be distinguished from a one-off large purchase.
- Geographic performance is not separated from customer concentration.
- Cancellation causes are not recorded, so avoidable quality failures cannot be separated from genuine commercial returns.

---

## 3. Dataset source

| Attribute | Value |
|---|---|
| Dataset | UCI Machine Learning Repository — Online Retail |
| Official page | https://archive.ics.uci.edu/dataset/352/online+retail |
| DOI | https://doi.org/10.24432/C5BW33 |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| File | `Online Retail.xlsx` (single worksheet, 23.72 MB) |
| SHA-256 | `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d` |
| Rows × columns | 541,909 × 8 |
| Period | 1 December 2010 – 9 December 2011 (305 trading days) |
| Variables | InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country |

The raw file is **not committed** to this repository (it is 23 MB and is available from the official source). Download instructions and the expected fingerprint are in [`data/data_source.txt`](data/data_source.txt).

### Reproducing the dataset

```bash
# Create the data directory and download the official archive
mkdir -p data && cd data
curl -L -o online+retail.zip "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
unzip online+retail.zip
# The extracted file must be named exactly: Online Retail.xlsx
```

Verify the fingerprint before running the notebook:

```bash
sha256sum "Online Retail.xlsx"
# expected: 43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d
```

---

## 4. Objectives

| # | Business question | Analytical objective | Decision informed |
|---|---|---|---|
| 1 | How does revenue change over time? | Monthly/daily revenue aggregation, MoM growth, seasonality | Seasonal stock and cash planning |
| 2 | Which products contribute most to sales? | Product revenue and quantity rankings | Range and availability decisions |
| 3 | Which countries generate the highest revenue? | Country revenue, orders, customers, AOV | Market prioritisation |
| 4 | Which customers contribute most to revenue? | Customer monetary aggregation and concentration | Named-account management |
| 5 | What are the purchasing frequency patterns? | Frequency distribution, repeat rate, orders per customer | Loyalty programme design |
| 6 | What percentage of transactions are cancellations? | Cancellation invoice and line shares; gross value | Returns policy and quality control |
| 7 | Which months/periods show higher sales? | Monthly, weekday and hourly patterns | Staffing and campaign timing |
| 8 | Are there unusual quantities or prices? | IQR outlier analysis and inspection of extremes | Data-entry and approval controls |
| 9 | Which segments have the greatest business value? | RFM scoring and segment revenue contribution | Retention budget allocation |
| 10 | What practical actions can management take? | Evidence-based opportunities with KPIs and risks | Management action plan |

---

## 5. Tools and technologies

- **Python 3.13**
- **pandas 2.2** — data loading, cleaning, aggregation
- **NumPy 2.3** — numerical computation
- **SciPy 1.17** — t-tests, Mann–Whitney U, chi-square, confidence intervals
- **Matplotlib 3.11** and **Seaborn 0.13** — 18 publication-ready visualisations
- **Jupyter / nbformat / nbconvert** — executed notebook
- **python-docx** — Word report generation
- **Git / GitHub** — version control and submission

Install the exact environment with:

```bash
pip install -r requirements.txt
```

---

## 6. Methodology

### 6.1 Cleaning pipeline (fixed, auditable order)

| Step | Action | Count |
|---|---|---|
| 1 | Remove exact duplicate rows | 5,268 |
| 2 | Impute missing descriptions as `UNKNOWN` | 1,454 |
| 3 | Separate cancellation invoices (`InvoiceNo` starts with `C`) | 9,251 working rows / 3,836 invoices |
| 4 | Separate non-cancellation negative-quantity returns | 1,336 |
| 5 | Exclude zero/negative unit prices from valid sales | 2,512 working rows |
| 6 | Flag non-product codes (POST, DOT, M, AMAZONFEE, etc.) | 2,910 working rows |
| 7 | Retain and flag missing `CustomerID`; exclude only from customer-level analysis | 135,037 working rows |
| 8 | Validate dates | 0 invalid |
| 9 | Compute IQR bounds and retain genuine extremes | 37,827 flagged |

**Final datasets**

| Dataset | Rows | Columns |
|---|---|---|
| Raw (untouched) | 541,909 | 8 |
| Cleaned, all records | 536,641 | 12 |
| Valid sales analysis | 524,878 | 12 |
| Valid sales + engineered features | 524,878 | 23 |
| Cancellation analysis | 9,251 | 12 |
| Returns analysis | 1,336 | 12 |

**Invoice reconciliation:** 25,900 total = 19,960 valid + 3,836 cancelled + 2,104 excluded (returns / non-positive price).

### 6.2 Feature engineering

Eleven derived variables: `Revenue`, `Year`, `Month`, `MonthName`, `Quarter`, `DayOfWeek`, `IsWeekend`, `Hour`, `InvoiceValue`, `ProductTotalQty` and the `Date` key. All are deterministic functions of observed data. Recency uses a reference date of **10 December 2011** (the day after the final transaction) to avoid compressing recency at the end of the observation window.

### 6.3 Statistical methods

- **95% confidence interval** for mean invoice value (t-distribution).
- **Welch t-test** (UK vs non-UK order values; repeat vs one-time AOV), justified by the Central Limit Theorem given large n and unequal variances.
- **Mann–Whitney U** as a distribution-free robustness check for skewed monetary data.
- **Cohen's d** for effect size, so statistical significance is not confused with business importance.
- **Chi-square test of independence** (country group × repeat status) with **Cramér's V**.
- **Spearman and Pearson correlations**, with an explicit statement that correlation does not imply causation.
- **IQR outlier analysis** with a winsorisation sensitivity check.

### 6.4 Advanced analysis

- **RFM segmentation** using quintile rank scores (1–5) and an ordered rule set producing nine segments.
- **Pareto analysis** for customers and products, reporting the exact number of entities needed to reach 80% of revenue.
- **Business opportunity analysis** with supporting evidence, KPIs, benefits and risks.

---

## 7. Key findings

| # | Finding | Evidence |
|---|---|---|
| 1 | Revenue is highly seasonal | Peak month **November 2011: £1,503,867**; December 2010: £821,453 |
| 2 | The 80/20 rule is directionally correct but imprecise | **1,130 customers (26.1%)** generate 80% of revenue; top 20% generate 74.66% |
| 3 | Revenue is driven by basket size, not price | Spearman ρ (invoice value vs lines) = **0.55**; vs average price = **0.09** |
| 4 | The UK dominates revenue | **£9,001,744 (84.59%)** of £10,642,111 |
| 5 | Repeat purchase is common among identified customers | **2,845 of 4,338 (65.58%)** ordered more than once |
| 6 | Cancellations are a material, persistent leakage | **3,836 invoices (16.12%)**, **£893,980** gross value |
| 7 | Extreme values are genuine commercial events | Largest line: **80,995 units** of PAPER CRAFT LITTLE BIRDIE (£168,470) |
| 8 | Customer value is highly unequal | Top customer **£280,206 (2.63%)**; top 10 = **14.45%** |
| 9 | Non-UK order values are higher, but the effect is small | £845 vs £500; Welch p = 1.8e-16, **Cohen's d = 0.19** |
| 10 | Repeat customers buy more consistently, not at a higher average | Mean AOV £421 vs £411 (p = 0.87); medians £303 vs £256 (Mann–Whitney p = 8.6e-12) |
| 11 | Trading follows a weekday, business-hours rhythm | Peak day **Thursday (£2.20m)**; peak hour **12:00 (3,220 orders)**; **no Saturday transactions at all** |
| 12 | Product revenue sits in a long tail | Top 10 products = **9.44%** of product revenue; **825 of 3,912** products needed for 80% |

### Headline KPIs

| KPI | Result |
|---|---|
| Total valid sales revenue | **£10,642,110.80** |
| Total units sold | **5,572,420** |
| Valid invoices | **19,960** |
| Unique purchasing customers | **4,338** |
| Average order value | **£533.17** |
| Repeat customer rate | **65.58%** |
| Cancellation rate (by invoice) | **16.12%** |
| Top country revenue share | **84.59% (United Kingdom)** |
| Top customer revenue share | **2.63% (Customer 14646)** |

### RFM segments

| Segment | Customers | Revenue | Revenue share |
|---|---|---|---|
| Champions | 942 | £5,729,483 | **64.47%** |
| Loyal Customers | 770 | £1,439,912 | 16.20% |
| At Risk | 485 | £433,176 | 4.87% |
| Can't Lose Them | 173 | £385,720 | 4.34% |
| Lost | 570 | £292,576 | 3.29% |
| Hibernating | 507 | £232,239 | 2.61% |
| Needs Attention | 432 | £189,512 | 2.13% |
| Potential Loyalist | 326 | £141,387 | 1.59% |
| New / Promising | 133 | £43,203 | 0.49% |

---

## 8. Visualisations

All 18 charts are saved as 200-dpi PNGs in [`visualizations/`](visualizations/) and embedded in the Word report.

| # | File | Chart type | Analytical purpose |
|---|---|---|---|
| 1 | `monthly_revenue.png` | Line | Monthly revenue trend and seasonality |
| 2 | `monthly_orders.png` | Line | Monthly order volume |
| 3 | `top_products.png` | Horizontal bar | Top 10 products by revenue |
| 4 | `top_products_qty.png` | Horizontal bar | Top 10 products by quantity |
| 5 | `country_analysis.png` | Horizontal bar | Revenue by country |
| 6 | `quantity_distribution.png` | Histogram | Quantity distribution |
| 7 | `unitprice_distribution.png` | Histogram | Unit price distribution |
| 8 | `revenue_distribution.png` | Histogram | Invoice value distribution |
| 9 | `quantity_outliers.png` | Box plot | Quantity outliers (log scale) |
| 10 | `customer_spending_box.png` | Box plot | Customer monetary distribution |
| 11 | `customer_segmentation.png` | Bar | RFM segment sizes |
| 12 | `correlation_heatmap.png` | Heatmap | Invoice-level correlations |
| 13 | `cancellation_trends.png` | Bar | Cancellations by month |
| 14 | `weekday_sales.png` | Bar | Revenue by day of week |
| 15 | `hourly_patterns.png` | Bar | Order volume by hour |
| 16 | `pareto_chart.png` | Pareto curve | Customer revenue concentration |
| 17 | `top_customers.png` | Horizontal bar | Top 10 customers by revenue |
| 18 | `rfm_scatter.png` | Scatter | Recency vs monetary value by segment |

---

## 9. How to execute the notebook

### Option A — run as-is (dataset already present)

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=900 \
  notebooks/Real_World_Dataset_Analysis.ipynb
```

### Option B — interactive

```bash
pip install -r requirements.txt
jupyter lab notebooks/Real_World_Dataset_Analysis.ipynb
```

The notebook locates the project root automatically, so it can be run from the repository root or from inside `notebooks/`. It writes:

- `outputs/*.csv` and `outputs/results.json` — summary tables and every key figure
- `visualizations/*.png` — all 18 charts

### Rebuilding the Word report

```bash
python scripts/build_report.py
# → reports/Real_World_Dataset_Analysis_Report.docx
```

### Rebuilding the analysis from source

```bash
cat scripts/analysis.py scripts/analysis_part2.py > scripts/run_analysis.py
python scripts/run_analysis.py
```

---

## 10. Project structure

```
real-world-online-retail-analysis/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── data_source.txt
├── notebooks/
│   └── Real_World_Dataset_Analysis.ipynb   (fully executed)
├── reports/
│   └── Real_World_Dataset_Analysis_Report.docx
├── visualizations/                          (18 PNG charts)
├── outputs/
│   ├── cleaned_data_summary.csv
│   ├── kpi_summary.csv
│   ├── cleaning_audit.csv
│   ├── data_dictionary.csv
│   ├── rfm_segments.csv
│   ├── key_findings.csv
│   ├── business_opportunities.csv
│   ├── monthly_summary.csv
│   ├── country_summary.csv
│   ├── top_customers.csv
│   ├── customer_correlations.csv
│   ├── univariate_statistics.csv
│   ├── missing_values.csv
│   ├── raw_numeric_describe.csv
│   └── results.json
├── scripts/
│   ├── analysis.py
│   ├── analysis_part2.py
│   ├── run_analysis.py
│   └── build_report.py
└── SUBMISSION_DESCRIPTION.md
```

---

## 11. Project limitations

1. **Age of the data** — the window ends 9 December 2011; behaviour may not reflect current markets.
2. **Single seasonal cycle** — 13 months contain one November and one December, so seasonality is estimated from one observation per month.
3. **Geographic concentration** — 91.43% of lines are UK; non-UK findings rest on small customer counts.
4. **Missing customer identifiers** — 135,037 working rows (24.93%) cannot be attributed to a customer, so customer-level metrics describe 75% of activity.
5. **No cost or margin data** — only revenue can be computed; profitability is out of scope.
6. **No cancellation reasons** — quality failures cannot be separated from commercial returns.
7. **Non-product lines** — postage, fees and adjustments are mixed with products in the raw file.
8. **No causal identification** — all tests establish association, not causation.
9. **Unobserved confounders** — customer type, contract terms and promotional exposure are not recorded.

---

## 12. Synthetic data statement

**No synthetic records were used.** Every row originates from the official UCI file. Derived variables (revenue, recency, frequency, monetary value, RFM scores) are deterministic functions of observed records. Synthetic data would risk misrepresenting customer behaviour, distributions, outliers, statistical relationships and business decisions; the project therefore avoids it entirely and documents this explicitly in Section 19 of the report.

---

## 13. Author attribution

- **Author:** *[Your Name]* — Data Analytics Intern, YuvaIntern (Task 4)
- **Dataset:** UCI Machine Learning Repository, Online Retail, DOI 10.24432/C5BW33, licensed CC BY 4.0
- **Report:** `reports/Real_World_Dataset_Analysis_Report.docx`
- **Submission document (Google Docs):** https://docs.google.com/document/d/1ZnkecSn0G92pgaTV7B5jI8Q99rJ6ae7vQYT2gIaMDN0/edit
- **Submission description:** `SUBMISSION_DESCRIPTION.md`

> Update the author name and any institutional details before submitting. The dataset licence (CC BY 4.0) permits reuse with attribution; the attribution is provided in the report references and in `data/data_source.txt`.

---

## 14. Reproducibility statement

The raw dataset fingerprint, cleaning counts, statistical tests and every chart are generated by the executed notebook. The report is generated from `outputs/results.json` and the CSV summary tables, so the report and notebook cannot diverge: both are produced by the same pipeline. If the dataset is re-downloaded, the SHA-256 fingerprint in `data/data_source.txt` should match before running the analysis.

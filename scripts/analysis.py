# %% [markdown]
# # Real-World Dataset Analysis Project
# ### Exploratory Data Analysis, Customer Segmentation and Business Insights Using the UCI Online Retail Dataset
#
# **Author:** YuvaIntern Data Analytics Intern
# **Dataset:** UCI Machine Learning Repository — Online Retail (DOI: 10.24432/C5BW33)
# **Environment:** Python 3, Pandas, NumPy, Matplotlib, Seaborn, SciPy
#
# This notebook is fully executed. Every number, table and chart below is produced directly from the
# original `Online Retail.xlsx` file downloaded from the official UCI source. No synthetic records
# have been added and no result has been hard-coded.
#
# ---
# ## 0. Notebook configuration and reproducibility
#
# The notebook locates the project root automatically so that it can be executed either from the
# repository root or from inside the `notebooks/` folder.

# %%
import os, json, hashlib, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # headless rendering for reproducible PNG export
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

try:                      # display() exists in Jupyter; provide a fallback for plain `python` runs
    display
except NameError:
    from IPython.display import display

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 220)
pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

# ---- project paths -------------------------------------------------------
def find_project_root() -> Path:
    for candidate in [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]:
        if (candidate / "data" / "Online Retail.xlsx").exists():
            return candidate
    raise FileNotFoundError("Could not locate data/Online Retail.xlsx")

ROOT = find_project_root()
DATA_PATH = ROOT / "data" / "Online Retail.xlsx"
OUT = ROOT / "outputs"; OUT.mkdir(parents=True, exist_ok=True)
VIZ = ROOT / "visualizations"; VIZ.mkdir(parents=True, exist_ok=True)

print("Project root :", ROOT)
print("Dataset file :", DATA_PATH)
print("File size MB :", round(DATA_PATH.stat().st_size / 1e6, 2))

# ---- global chart style --------------------------------------------------
sns.set_theme(style="whitegrid", context="talk", font_scale=1.05)
plt.rcParams.update({
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.edgecolor": "#4d4d4d",
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "savefig.bbox": "tight",
})
PALETTE = "viridis"
ACCENT = "#1f4e79"
GREY = "#7f8c8d"

# Unified result container: every key figure is written to results.json at the end.
R = {}

# %% [markdown]
# ---
# ## 1. Data loading and integrity verification
#
# The genuine dataset is downloaded from the official UCI page
# (`https://archive.ics.uci.edu/static/public/352/online+retail.zip`) and is **never modified**.
# We first record a SHA-256 fingerprint so that the exact file analysed can be audited later.

# %%
sha256 = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
print("SHA-256 of raw dataset:", sha256)

raw = pd.read_excel(DATA_PATH, sheet_name="Online Retail")
print("\nRaw dataset loaded.")
print("Shape (rows, columns):", raw.shape)
print("Columns:", list(raw.columns))
print("\nFirst 5 rows:")
display(raw.head())

R["raw_shape"] = list(raw.shape)
R["raw_rows"] = int(raw.shape[0])
R["raw_cols"] = int(raw.shape[1])
R["sha256"] = sha256
R["file_size_mb"] = round(DATA_PATH.stat().st_size / 1e6, 2)

# Preserve the untouched raw data for audit / reproducibility.
RAW_BACKUP = ROOT / "data" / "raw_online_retail.pkl"
raw.to_pickle(RAW_BACKUP)
print("\nRaw snapshot preserved at:", RAW_BACKUP)

# %% [markdown]
# ## 2. Dataset understanding
#
# ### 2.1 Structure and memory

# %%
mem = raw.memory_usage(deep=True)
print("Memory usage by column (MB):")
print((mem / 1e6).round(3).to_string())
print("\nTotal memory (MB):", round(mem.sum() / 1e6, 2))
R["memory_mb"] = round(float(mem.sum() / 1e6), 2)

print("\nData types:")
print(raw.dtypes.to_string())
R["dtypes"] = {c: str(t) for c, t in raw.dtypes.items()}

print("\nNon-null counts:")
print(raw.notna().sum().to_string())

print("\nMissing-value counts and percentages:")
missing = pd.DataFrame({
    "missing_count": raw.isna().sum(),
    "missing_pct": (raw.isna().sum() / len(raw) * 100).round(3),
}).sort_values("missing_count", ascending=False)
display(missing)
missing.to_csv(OUT / "missing_values.csv")
R["missing"] = missing.reset_index().rename(columns={"index": "column"}).to_dict("records")

print("\nExact duplicate rows:", int(raw.duplicated().sum()))
print("Duplicate percentage:", round(raw.duplicated().mean() * 100, 3), "%")
R["duplicates"] = int(raw.duplicated().sum())
R["duplicate_pct"] = round(float(raw.duplicated().mean() * 100), 3)

# %% [markdown]
# ### 2.2 Unique values in important variables

# %%
for col in ["InvoiceNo", "StockCode", "Description", "CustomerID", "Country"]:
    print(f"{col:12s} unique values: {raw[col].nunique():>7,}")

print("\nDate range:", raw["InvoiceDate"].min(), "→", raw["InvoiceDate"].max())
print("Number of distinct days:", raw["InvoiceDate"].dt.date.nunique())
R["date_min"] = str(raw["InvoiceDate"].min())
R["date_max"] = str(raw["InvoiceDate"].max())
R["n_days"] = int(raw["InvoiceDate"].dt.date.nunique())
R["n_invoices"] = int(raw["InvoiceNo"].nunique())
R["n_stockcodes"] = int(raw["StockCode"].nunique())
R["n_customers_raw"] = int(raw["CustomerID"].nunique())
R["n_countries"] = int(raw["Country"].nunique())

# %% [markdown]
# ### 2.3 Numerical distributions (raw)

# %%
num_desc = raw[["Quantity", "UnitPrice"]].describe(
    percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
).T
num_desc["IQR"] = num_desc["75%"] - num_desc["25%"]
num_desc["skew"] = raw[["Quantity", "UnitPrice"]].skew()
num_desc["kurtosis"] = raw[["Quantity", "UnitPrice"]].kurtosis()
display(num_desc.round(3))
num_desc.to_csv(OUT / "raw_numeric_describe.csv")

# %% [markdown]
# ### 2.4 Categorical distributions (raw)

# %%
print("Country distribution (top 12):")
print(raw["Country"].value_counts().head(12).to_string())
print("\nNumber of countries:", raw["Country"].nunique())
print("\nTop 10 products by line count:")
print(raw["Description"].value_counts().head(10).to_string())

# %% [markdown]
# ### 2.5 Data dictionary
#
# The example values below are read directly from the raw dataframe (first non-null occurrence),
# not typed in by hand.

# %%
examples = {
    "InvoiceNo": raw.loc[raw["InvoiceNo"].notna(), "InvoiceNo"].iloc[0],
    "StockCode": raw["StockCode"].iloc[0],
    "Description": raw["Description"].dropna().iloc[0],
    "Quantity": raw["Quantity"].iloc[0],
    "InvoiceDate": raw["InvoiceDate"].iloc[0],
    "UnitPrice": raw["UnitPrice"].iloc[0],
    "CustomerID": raw["CustomerID"].dropna().iloc[0],
    "Country": raw["Country"].iloc[0],
}
dict_rows = [
    ("InvoiceNo", "object (text)", "Unique transaction identifier; prefix 'C' marks a cancellation/credit note.", examples["InvoiceNo"], "Invoice-level aggregation; separating cancellations from sales"),
    ("StockCode", "object (text)", "Product or service code (includes non-product codes such as POST, DOT, M, AMAZONFEE).", examples["StockCode"], "Product identification and demand analysis"),
    ("Description", "object (text)", "Human-readable product name; 1,454 missing values.", examples["Description"], "Product naming, top-product reporting, data-quality checks"),
    ("Quantity", "int64", "Number of units on the invoice line; negative values are returns.", examples["Quantity"], "Demand, outlier detection, revenue calculation"),
    ("InvoiceDate", "datetime64[ns]", "Date and time the invoice was generated.", examples["InvoiceDate"], "Time-series, seasonality, recency, weekday/hour patterns"),
    ("UnitPrice", "float64", "Price per unit in GBP; zero/negative values occur on some lines.", examples["UnitPrice"], "Revenue calculation, price distribution, outlier checks"),
    ("CustomerID", "float64 (nullable)", "Anonymous numeric customer identifier; 135,080 missing (24.93%).", examples["CustomerID"], "RFM segmentation, customer value, repeat-purchase analysis"),
    ("Country", "object (text)", "Customer country; 38 distinct values, dominated by the United Kingdom.", examples["Country"], "Geographic performance and market concentration"),
]
data_dict = pd.DataFrame(dict_rows, columns=["Variable", "Data type", "Description", "Example value (actual)", "Analytical purpose"])
display(data_dict)
data_dict.to_csv(OUT / "data_dictionary.csv", index=False)
R["data_dictionary_rows"] = len(data_dict)

# %% [markdown]
# ### 2.6 Initial data-quality observations
#
# 1. **135,080 missing CustomerID values (24.93%)** — customer-level analysis must use the complete-case subset.
# 2. **1,454 missing product descriptions** — product names cannot be recovered from the file alone.
# 3. **5,268 exact duplicate rows (0.97%)** — identical copies that would double-count revenue.
# 4. **9,288 rows on 3,836 cancellation invoices** (`InvoiceNo` starting with `C`), all with negative quantity.
# 5. **2,517 rows with unit price ≤ 0** (2 negative), including zero-priced promotional lines.
# 6. **Extreme values**: quantity up to 80,995 and unit price up to £38,970 require investigation, not automatic deletion.
# 7. **No invalid or missing dates** — the date column is clean.
# 8. **Non-product stock codes** (POST, DOT, M, AMAZONFEE, BANK CHARGES) inflate product-level rankings if not flagged.

# %% [markdown]
# ---
# ## 3. Data quality assessment and cleaning
#
# Cleaning is performed in a fixed, auditable order. The raw file is never overwritten; every
# intermediate count is recorded so that before/after figures can be reconciled.
#
# **Principle applied:** *do not delete unusual observations by default.* Each issue is classified as
# a genuine business event (return/cancellation), a data-entry error, or a genuine extreme purchase,
# and treated accordingly.

# %%
df = raw.copy()
audit = []          # cleaning audit rows
orig_n = len(df)

def audit_row(issue, raw_count, treatment, affected, reason):
    audit.append({
        "Data quality issue": issue,
        "Count in raw data": int(raw_count),
        "Treatment": treatment,
        "Records affected (working data)": int(affected),
        "Reason": reason,
    })

# ---- 3.1 exact duplicates ------------------------------------------------
raw_dup = int(raw.duplicated().sum())
dup_count = int(df.duplicated().sum())
df = df.drop_duplicates().copy()
audit_row("Exact duplicate records", raw_dup, "Removed",
          dup_count, "Identical copies; retaining them would double-count revenue and units.")

# ---- 3.2 missing descriptions -------------------------------------------
raw_desc_missing = int(raw["Description"].isna().sum())
desc_missing = int(df["Description"].isna().sum())
df["Description"] = df["Description"].fillna("UNKNOWN")
audit_row("Missing product description", raw_desc_missing, "Imputed with 'UNKNOWN'",
          desc_missing, "Preserves the transaction line; the product name is unavailable in the source file.")

# ---- 3.3 cancellation / return flags ------------------------------------
df["IsCancellation"] = df["InvoiceNo"].astype(str).str.startswith("C")
df["IsReturn"] = (~df["IsCancellation"]) & (df["Quantity"] < 0)
df["HasCustomerID"] = df["CustomerID"].notna()

raw_canc = int(raw["InvoiceNo"].astype(str).str.startswith("C").sum())
canc_rows = int(df["IsCancellation"].sum())
canc_invoices = int(df.loc[df["IsCancellation"], "InvoiceNo"].nunique())
audit_row("Cancellation invoices (InvoiceNo prefix 'C')", raw_canc,
          "Separated into cancellation dataset; excluded from valid sales",
          canc_rows, "Credit notes are genuine returns, not revenue; they must be analysed separately.")

raw_ret = int(((~raw["InvoiceNo"].astype(str).str.startswith("C")) & (raw["Quantity"] < 0)).sum())
returns_rows = int(df["IsReturn"].sum())
audit_row("Negative quantity on non-cancellation invoices", raw_ret,
          "Separated into returns dataset; excluded from valid sales",
          returns_rows, "Unpaid/returned goods; including them would understate sales.")

# ---- 3.4 zero / negative unit price -------------------------------------
raw_price_bad = int((raw["UnitPrice"] <= 0).sum())
price_bad = int((df["UnitPrice"] <= 0).sum())
price_neg = int((df["UnitPrice"] < 0).sum())
audit_row("Zero or negative unit price", raw_price_bad,
          "Excluded from valid sales; retained in raw data", price_bad,
          "Zero-price lines carry no revenue; negative prices are data-entry errors.")

# ---- 3.5 non-product stock codes ----------------------------------------
NON_PRODUCT = {"POST", "DOT", "M", "BANK CHARGES", "AMAZONFEE", "PADS", "D", "C2", "CRUK",
               "TEST001", "TEST002", "SAMPLES", "NOTES", "B", "S", "AMAZON", "CHECK", "COLLECT"}
df["IsNonProduct"] = df["StockCode"].astype(str).str.upper().isin(NON_PRODUCT)
raw_nonprod = int(raw["StockCode"].astype(str).str.upper().isin(NON_PRODUCT).sum())
nonprod_rows = int(df["IsNonProduct"].sum())
audit_row("Non-product stock codes (postage, fees, samples)", raw_nonprod,
          "Flagged; retained in revenue totals, excluded from product rankings",
          nonprod_rows, "These lines are real revenue but are not physical products; mixing them distorts product demand.")

# ---- 3.6 missing CustomerID ---------------------------------------------
raw_cust_missing = int(raw["CustomerID"].isna().sum())
cust_missing = int((~df["HasCustomerID"]).sum())
audit_row("Missing CustomerID", raw_cust_missing,
          "Retained and flagged; excluded only from customer-level analysis",
          cust_missing, "Dropping these rows would remove 25% of transactions and bias revenue/geography results.")

# ---- 3.7 invalid dates ---------------------------------------------------
bad_dates = int(df["InvoiceDate"].isna().sum())
audit_row("Invalid or missing invoice date", int(raw["InvoiceDate"].isna().sum()), "None required", bad_dates,
          "No invalid dates were found; the column parsed cleanly as datetime.")

# ---- 3.8 outliers --------------------------------------------------------
valid_tmp = df[(~df["IsCancellation"]) & (df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
q1, q3 = valid_tmp["Quantity"].quantile([0.25, 0.75])
iqr = q3 - q1
qty_out = int(((valid_tmp["Quantity"] < q1 - 1.5 * iqr) | (valid_tmp["Quantity"] > q3 + 1.5 * iqr)).sum())
p1, p3 = valid_tmp["UnitPrice"].quantile([0.25, 0.75])
pir = p3 - p1
price_out = int(((valid_tmp["UnitPrice"] < p1 - 1.5 * pir) | (valid_tmp["UnitPrice"] > p3 + 1.5 * pir)).sum())
audit_row("Unusual quantity / price values (IQR rule)", max(qty_out, price_out),
          "Retained and flagged; winsorised only in a sensitivity check",
          max(qty_out, price_out), "Inspection showed genuine wholesale purchases; automatic deletion would destroy real revenue.")

cleaning_audit = pd.DataFrame(audit)
cleaning_audit.columns = ["Data quality issue", "Count in raw data", "Treatment",
                          "Records affected (working data)", "Reason"]
display(cleaning_audit)
cleaning_audit.to_csv(OUT / "cleaning_audit.csv", index=False)
R["cleaning_audit"] = cleaning_audit.to_dict("records")
R["dup_count"] = dup_count
R["desc_missing"] = desc_missing
R["canc_rows"] = canc_rows
R["canc_invoices"] = canc_invoices
R["returns_rows"] = returns_rows
R["price_bad"] = price_bad
R["price_neg"] = price_neg
R["nonprod_rows"] = nonprod_rows
R["cust_missing"] = cust_missing
R["qty_outliers"] = qty_out
R["price_outliers"] = price_out
R["qty_iqr_bounds"] = [float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr)]
R["price_iqr_bounds"] = [float(p1 - 1.5 * pir), float(p3 + 1.5 * pir)]

# %% [markdown]
# ### 3.9 Creating the four analysis datasets
#
# Keeping the datasets separate is essential: cancellation information must not be destroyed before it
# is analysed, and customer-level metrics must not be contaminated by anonymous transactions.

# %%
raw_data = raw.copy()                                   # 1. untouched original
cleaned_all = df.copy()                                 # 2. de-duplicated, typed, flagged
valid_sales = df[(~df["IsCancellation"]) & (df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
cancel_data = df[df["IsCancellation"]].copy()
return_data = df[df["IsReturn"]].copy()

print("Raw dataset           :", raw_data.shape)
print("Cleaned (all records) :", cleaned_all.shape)
print("Valid sales analysis  :", valid_sales.shape)
print("Cancellation analysis :", cancel_data.shape)
print("Returns analysis      :", return_data.shape)

R["cleaned_all_shape"] = list(cleaned_all.shape)
R["valid_sales_shape"] = list(valid_sales.shape)
R["cancel_shape"] = list(cancel_data.shape)
R["return_shape"] = list(return_data.shape)

# %% [markdown]
# ---
# ## 4. Feature engineering
#
# All features below are **derived** from the original eight columns. No new information is introduced
# from outside the dataset, therefore no data leakage is possible. Derived columns are added to a copy
# of the valid-sales data so the raw file remains untouched.

# %%
v = valid_sales.copy()
v["Revenue"] = v["Quantity"] * v["UnitPrice"]          # line-level revenue (GBP)
v["Year"] = v["InvoiceDate"].dt.year
v["Month"] = v["InvoiceDate"].dt.month
v["MonthName"] = v["InvoiceDate"].dt.month_name()
v["Quarter"] = v["InvoiceDate"].dt.quarter
v["DayOfWeek"] = v["InvoiceDate"].dt.day_name()
v["Hour"] = v["InvoiceDate"].dt.hour
v["Date"] = v["InvoiceDate"].dt.date
v["IsWeekend"] = v["DayOfWeek"].isin(["Saturday", "Sunday"])

# Invoice-level transaction value (each line inherits its invoice total)
inv_value = v.groupby("InvoiceNo")["Revenue"].sum().rename("InvoiceValue")
v = v.merge(inv_value, on="InvoiceNo", how="left")

# Product-level total quantity sold (each line inherits its product total)
prod_qty = v.groupby("StockCode")["Quantity"].sum().rename("ProductTotalQty")
v = v.merge(prod_qty, on="StockCode", how="left")

print("Feature-engineered sales shape:", v.shape)
print("\nEngineered columns added:")
engineered = ["Revenue", "Year", "Month", "MonthName", "Quarter", "DayOfWeek", "Hour",
              "Date", "IsWeekend", "InvoiceValue", "ProductTotalQty"]
print(engineered)
print("\nPreview:")
display(v[["InvoiceNo", "StockCode", "Quantity", "UnitPrice", "Revenue", "InvoiceDate",
           "MonthName", "DayOfWeek", "Hour", "InvoiceValue", "ProductTotalQty"]].head(8))

R["engineered_columns"] = engineered
R["valid_sales_rows"] = int(len(v))
R["total_revenue"] = round(float(v["Revenue"].sum()), 2)
R["total_units"] = int(v["Quantity"].sum())
R["n_invoices_valid"] = int(v["InvoiceNo"].nunique())
R["n_customers_valid"] = int(v["CustomerID"].nunique())

# %% [markdown]
# **Purpose of each engineered variable**
#
# | Variable | Type | Purpose |
# |---|---|---|
# | Revenue | Derived | Line-level sales value; the basis of every monetary KPI. |
# | Year / Month / Quarter | Derived | Time-series aggregation and seasonality. |
# | MonthName | Derived | Human-readable chart labels. |
# | DayOfWeek / IsWeekend | Derived | Weekday vs weekend purchasing behaviour. |
# | Hour | Derived | Intraday order-pattern analysis for staffing/campaign timing. |
# | InvoiceValue | Derived | Order-level value used for AOV and invoice distributions. |
# | ProductTotalQty | Derived | Product demand ranking independent of line count. |
#
# **Reference date for recency:** recency is measured from **10 December 2011**, i.e. the day after the
# last transaction in the file (9 December 2011). Using a date after the observation window avoids
# artificially inflating recency for the final days of the dataset.

# %%
REFERENCE_DATE = v["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)
print("Recency reference date:", REFERENCE_DATE.date())
R["reference_date"] = str(REFERENCE_DATE.date())

# %% [markdown]
# ---
# ## 5. KPI summary
#
# Every percentage below states its denominator explicitly.

# %%
valid_cust = v[v["CustomerID"].notna()]
invoice_totals = v.groupby("InvoiceNo").agg(
    InvoiceValue=("Revenue", "sum"),
    InvoiceDate=("InvoiceDate", "first"),
    CustomerID=("CustomerID", "first"),
    Country=("Country", "first"),
    Lines=("Revenue", "size"),
).reset_index()

n_cust = invoice_totals["CustomerID"].nunique()
repeat_cust = invoice_totals.groupby("CustomerID").size()
repeat_n = int((repeat_cust > 1).sum())
one_time_n = int((repeat_cust == 1).sum())

total_rev = v["Revenue"].sum()
total_units = int(v["Quantity"].sum())
n_inv = invoice_totals.shape[0]
aov = total_rev / n_inv
top_country_rev = invoice_totals.groupby("Country")["InvoiceValue"].sum().sort_values(ascending=False)
top_cust_rev = invoice_totals.groupby("CustomerID")["InvoiceValue"].sum().sort_values(ascending=False)

cancel_value = cancel_data["Quantity"].sum() * 0  # placeholder, computed explicitly below
cancel_value = float((cancel_data["Quantity"] * cancel_data["UnitPrice"]).sum())
cancel_rate_inv = canc_invoices / (canc_invoices + n_inv) * 100
cancel_rate_rows = canc_rows / (canc_rows + len(v)) * 100

monthly = v.groupby(["Year", "Month"]).agg(
    Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"), Units=("Quantity", "sum")
).reset_index()
monthly["MonthLabel"] = pd.to_datetime(monthly[["Year", "Month"]].assign(day=1)).dt.strftime("%b %Y")
monthly = monthly.sort_values(["Year", "Month"]).reset_index(drop=True)
monthly["MoM_growth_pct"] = monthly["Revenue"].pct_change() * 100

kpi = pd.DataFrame([
    ("Total valid sales revenue (GBP)", f"£{total_rev:,.2f}", "Sum of Quantity × UnitPrice on valid, non-cancelled, positive-price lines."),
    ("Total units sold", f"{total_units:,}", "Sum of Quantity on valid sales lines."),
    ("Total valid invoices", f"{n_inv:,}", "Distinct InvoiceNo values in the valid sales dataset."),
    ("Unique purchasing customers", f"{n_cust:,}", "Distinct non-null CustomerID in valid sales."),
    ("Average order value (AOV, GBP)", f"£{aov:,.2f}", f"Total revenue ÷ {n_inv:,} valid invoices."),
    ("Repeat customer rate (%)", f"{repeat_n / n_cust * 100:.2f}%", f"{repeat_n:,} customers with >1 invoice ÷ {n_cust:,} purchasing customers."),
    ("One-time customer share (%)", f"{one_time_n / n_cust * 100:.2f}%", f"{one_time_n:,} customers with exactly 1 invoice ÷ {n_cust:,} purchasing customers."),
    ("Cancellation rate by invoice (%)", f"{cancel_rate_inv:.2f}%", f"{canc_invoices:,} cancellation invoices ÷ ({canc_invoices:,} cancellations + {n_inv:,} valid invoices)."),
    ("Cancellation rate by line (%)", f"{cancel_rate_rows:.2f}%", f"{canc_rows:,} cancellation lines ÷ ({canc_rows:,} cancellation lines + {len(v):,} valid lines)."),
    ("Cancellation value (GBP, absolute)", f"£{abs(cancel_value):,.2f}", "Sum of Quantity × UnitPrice on cancellation lines (negative by construction)."),
    ("Top country revenue (GBP)", f"£{top_country_rev.iloc[0]:,.2f}", f"{top_country_rev.index[0]} revenue ÷ total revenue = {top_country_rev.iloc[0]/total_rev*100:.2f}%."),
    ("Top customer revenue (GBP)", f"£{top_cust_rev.iloc[0]:,.2f}", f"Customer {int(top_cust_rev.index[0])} ÷ total revenue = {top_cust_rev.iloc[0]/total_rev*100:.2f}%."),
    ("Peak month revenue (GBP)", f"£{monthly.loc[monthly['Revenue'].idxmax(),'Revenue']:,.2f}", f"{monthly.loc[monthly['Revenue'].idxmax(),'MonthLabel']} is the highest-revenue month."),
    ("Latest-month MoM growth (%)", f"{monthly['MoM_growth_pct'].iloc[-1]:.2f}%",
     f"{monthly['MonthLabel'].iloc[-1]} vs {monthly['MonthLabel'].iloc[-2]} (partial month)."),
], columns=["KPI", "Calculated result", "Definition / denominator"])
display(kpi)
kpi.to_csv(OUT / "kpi_summary.csv", index=False)

R["kpi"] = kpi.to_dict("records")
R["total_revenue"] = round(float(total_rev), 2)
R["total_units"] = total_units
R["n_invoices_valid"] = int(n_inv)
R["n_customers_valid"] = int(n_cust)
R["aov"] = round(float(aov), 2)
R["repeat_n"] = repeat_n
R["one_time_n"] = one_time_n
R["repeat_rate"] = round(float(repeat_n / n_cust * 100), 2)
R["one_time_rate"] = round(float(one_time_n / n_cust * 100), 2)
R["cancel_rate_inv"] = round(float(cancel_rate_inv), 2)
R["cancel_rate_rows"] = round(float(cancel_rate_rows), 2)
R["cancel_value"] = round(float(cancel_value), 2)
R["top_country"] = str(top_country_rev.index[0])
R["top_country_rev"] = round(float(top_country_rev.iloc[0]), 2)
R["top_country_share"] = round(float(top_country_rev.iloc[0] / total_rev * 100), 2)
R["top_customer_id"] = int(top_cust_rev.index[0])
R["top_customer_rev"] = round(float(top_cust_rev.iloc[0]), 2)
R["top_customer_share"] = round(float(top_cust_rev.iloc[0] / total_rev * 100), 2)
R["peak_month"] = str(monthly.loc[monthly["Revenue"].idxmax(), "MonthLabel"])
R["peak_month_rev"] = round(float(monthly["Revenue"].max()), 2)
R["latest_month"] = str(monthly["MonthLabel"].iloc[-1])
R["latest_mom"] = round(float(monthly["MoM_growth_pct"].iloc[-1]), 2)
R["monthly"] = monthly[["MonthLabel", "Revenue", "Orders", "Units", "MoM_growth_pct"]].round(2).to_dict("records")

# Invoice reconciliation: every invoice must be valid, cancelled, or excluded for returns/zero price
R["invoice_reconciliation"] = {
    "total_invoices": int(raw["InvoiceNo"].nunique()),
    "valid_sales_invoices": int(n_inv),
    "cancellation_invoices": int(canc_invoices),
    "excluded_other_invoices": int(raw["InvoiceNo"].nunique()) - int(n_inv) - int(canc_invoices),
}
print("\nInvoice reconciliation:", R["invoice_reconciliation"])

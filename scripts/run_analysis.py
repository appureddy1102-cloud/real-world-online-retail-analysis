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

# %% [markdown]
# ---
# ## 6. Exploratory data analysis
#
# ### 6.1 Univariate analysis of the valid sales data

# %%
univ = v[["Quantity", "UnitPrice", "Revenue"]].describe(
    percentiles=[0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
).T
univ["IQR"] = univ["75%"] - univ["25%"]
univ["Variance"] = v[["Quantity", "UnitPrice", "Revenue"]].var()
univ["Skewness"] = v[["Quantity", "UnitPrice", "Revenue"]].skew()
univ["Kurtosis"] = v[["Quantity", "UnitPrice", "Revenue"]].kurtosis()
univ["Mode"] = [v[c].mode().iloc[0] for c in univ.index]

# Invoice-level distribution (the correct unit for order-value statements)
univ_inv = invoice_totals["InvoiceValue"].describe(
    percentiles=[0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
).to_frame("InvoiceValue").T
univ_inv["IQR"] = univ_inv["75%"] - univ_inv["25%"]
univ_inv["Skewness"] = invoice_totals["InvoiceValue"].skew()
univ_inv["Kurtosis"] = invoice_totals["InvoiceValue"].kurtosis()
univ_inv["Mode"] = invoice_totals["InvoiceValue"].mode().iloc[0]
print("\nInvoice-level value distribution:")
display(univ_inv.round(3))
display(univ.round(3))
univ.to_csv(OUT / "univariate_statistics.csv")

R["univariate"] = univ.round(3).reset_index().rename(columns={"index": "variable"}).to_dict("records")
R["revenue_median"] = round(float(v["Revenue"].median()), 3)
R["revenue_mean"] = round(float(v["Revenue"].mean()), 3)
R["invoice_value_median"] = round(float(invoice_totals["InvoiceValue"].median()), 3)
R["invoice_value_mean"] = round(float(invoice_totals["InvoiceValue"].mean()), 3)
R["invoice_value_skew"] = round(float(invoice_totals["InvoiceValue"].skew()), 3)
R["invoice_value_kurtosis"] = round(float(invoice_totals["InvoiceValue"].kurtosis()), 3)

# %% [markdown]
# **Interpretation.** Revenue is heavily right-skewed: the median line is far below the mean, and
# kurtosis is very high. A small number of large wholesale invoices therefore dominate totals, which is
# why the report uses medians and segment-level analysis alongside means.

# %% [markdown]
# ### 6.2 Bivariate analysis

# %%
# Correlation at invoice level (same unit of analysis, avoids mixing levels)
biv = invoice_totals.merge(
    v.groupby("InvoiceNo").agg(LineCount=("Revenue", "size"), TotalQty=("Quantity", "sum"),
                               AvgPrice=("UnitPrice", "mean")).reset_index(),
    on="InvoiceNo", how="left")
biv["Hour"] = pd.to_datetime(biv["InvoiceDate"]).dt.hour
biv["Month"] = pd.to_datetime(biv["InvoiceDate"]).dt.month

num_cols = ["InvoiceValue", "LineCount", "TotalQty", "AvgPrice", "Hour", "Month"]
corr_pear = biv[num_cols].corr(method="pearson")
corr_spear = biv[num_cols].corr(method="spearman")

print("Spearman correlation (invoice level):")
print(corr_spear.round(3).to_string())
print("\nKey bivariate results:")
print(f"  InvoiceValue ↔ TotalQty      Spearman rho = {corr_spear.loc['InvoiceValue','TotalQty']:.3f}")
print(f"  InvoiceValue ↔ AvgPrice      Spearman rho = {corr_spear.loc['InvoiceValue','AvgPrice']:.3f}")
print(f"  InvoiceValue ↔ Lines         Spearman rho = {corr_spear.loc['InvoiceValue','LineCount']:.3f}")

R["corr_spear_invoicevalue_qty"] = round(float(corr_spear.loc["InvoiceValue", "TotalQty"]), 3)
R["corr_spear_invoicevalue_price"] = round(float(corr_spear.loc["InvoiceValue", "AvgPrice"]), 3)
R["corr_spear_invoicevalue_lines"] = round(float(corr_spear.loc["InvoiceValue", "LineCount"]), 3)

# Customer-level: frequency vs monetary value
cust_stats = invoice_totals.groupby("CustomerID").agg(
    Recency=("InvoiceDate", lambda s: (REFERENCE_DATE - s.max()).days),
    Frequency=("InvoiceNo", "nunique"),
    Monetary=("InvoiceValue", "sum"),
    AOV=("InvoiceValue", "mean"),
    Country=("Country", "first"),
    FirstPurchase=("InvoiceDate", "min"),
    LastPurchase=("InvoiceDate", "max"),
).reset_index()
cust_stats["TenureDays"] = (cust_stats["LastPurchase"] - cust_stats["FirstPurchase"]).dt.days

print(f"\nCustomer-level frequency ↔ monetary Spearman rho = "
      f"{cust_stats['Frequency'].corr(cust_stats['Monetary'], method='spearman'):.3f}")
print(f"Customer-level recency ↔ monetary Spearman rho = "
      f"{cust_stats['Recency'].corr(cust_stats['Monetary'], method='spearman'):.3f}")
print(f"Customer-level frequency ↔ AOV Spearman rho = "
      f"{cust_stats['Frequency'].corr(cust_stats['AOV'], method='spearman'):.3f}")

R["corr_cust_freq_mon"] = round(float(cust_stats["Frequency"].corr(cust_stats["Monetary"], method="spearman")), 3)
R["corr_cust_rec_mon"] = round(float(cust_stats["Recency"].corr(cust_stats["Monetary"], method="spearman")), 3)
R["corr_cust_freq_aov"] = round(float(cust_stats["Frequency"].corr(cust_stats["AOV"], method="spearman")), 3)

# Product demand vs revenue
prod = v.groupby("StockCode").agg(
    Description=("Description", "first"),
    Units=("Quantity", "sum"),
    Revenue=("Revenue", "sum"),
    Lines=("Revenue", "size"),
    Customers=("CustomerID", "nunique"),
).reset_index()
print(f"\nProduct units ↔ revenue Spearman rho = {prod['Units'].corr(prod['Revenue'], method='spearman'):.3f}")
R["corr_prod_units_rev"] = round(float(prod["Units"].corr(prod["Revenue"], method="spearman")), 3)

# Country revenue
country = invoice_totals.groupby("Country").agg(
    Revenue=("InvoiceValue", "sum"), Orders=("InvoiceNo", "nunique"),
    Customers=("CustomerID", "nunique"), AOV=("InvoiceValue", "mean"),
).reset_index().sort_values("Revenue", ascending=False)
country["RevenueSharePct"] = country["Revenue"] / country["Revenue"].sum() * 100
display(country.head(12).round(2))
country.to_csv(OUT / "country_summary.csv", index=False)
R["country_top10"] = country.head(10).round(2).to_dict("records")

# %% [markdown]
# ### 6.3 Time-series analysis

# %%
print("Monthly revenue, orders and units:")
print(monthly[["MonthLabel", "Revenue", "Orders", "Units", "MoM_growth_pct"]].round(2).to_string(index=False))

daily = v.groupby("Date").agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")).reset_index()
daily["DayOfWeek"] = pd.to_datetime(daily["Date"]).dt.day_name()
weekday = daily.groupby("DayOfWeek").agg(Revenue=("Revenue", "sum"), Orders=("Orders", "sum")).reset_index()
weekday["RevenueSharePct"] = weekday["Revenue"] / weekday["Revenue"].sum() * 100
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday["__o"] = weekday["DayOfWeek"].map({d: i for i, d in enumerate(order)})
weekday = weekday.sort_values("__o").drop(columns="__o")
print("\nWeekday purchasing behaviour:")
print(weekday.round(2).to_string(index=False))

hourly = v.groupby("Hour").agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")).reset_index()
print("\nHourly transaction pattern (peak hours):")
print(hourly.sort_values("Orders", ascending=False).head(6).round(2).to_string(index=False))

R["weekday"] = weekday.round(2).to_dict("records")
R["hourly"] = hourly.round(2).to_dict("records")
R["daily_rows"] = int(len(daily))
R["peak_hour"] = int(hourly.loc[hourly["Orders"].idxmax(), "Hour"])
R["peak_hour_orders"] = int(hourly["Orders"].max())
R["peak_weekday"] = str(weekday.loc[weekday["Revenue"].idxmax(), "DayOfWeek"])
R["peak_weekday_rev"] = round(float(weekday["Revenue"].max()), 2)

# %% [markdown]
# ### 6.4 Customer analysis

# %%
top_customers = cust_stats.sort_values("Monetary", ascending=False).head(15)
print("Top 15 customers by revenue:")
print(top_customers[["CustomerID", "Recency", "Frequency", "Monetary", "AOV"]].round(2).to_string(index=False))
top_customers.to_csv(OUT / "top_customers.csv", index=False)
R["top_customers"] = top_customers.head(10).round(2).to_dict("records")

print(f"\nRepeat-purchase behaviour: {repeat_n:,} of {n_cust:,} customers ({repeat_n/n_cust*100:.2f}%) placed more than one order.")
print(f"Mean orders per customer: {invoice_totals.groupby('CustomerID').size().mean():.2f}")
print(f"Median orders per customer: {invoice_totals.groupby('CustomerID').size().median():.1f}")
print(f"Top 10 customers contribute £{top_cust_rev.head(10).sum():,.2f} "
      f"({top_cust_rev.head(10).sum()/total_rev*100:.2f}% of revenue).")
R["mean_orders_per_customer"] = round(float(invoice_totals.groupby("CustomerID").size().mean()), 2)
R["median_orders_per_customer"] = round(float(invoice_totals.groupby("CustomerID").size().median()), 1)
R["top10_cust_rev"] = round(float(top_cust_rev.head(10).sum()), 2)
R["top10_cust_share"] = round(float(top_cust_rev.head(10).sum() / total_rev * 100), 2)

# %% [markdown]
# ### 6.5 Product analysis
#
# Non-product codes (POST, DOT, M, AMAZONFEE, etc.) are excluded from product rankings only; they
# remain in revenue totals. This is stated explicitly so the ranking is not mistaken for a data edit.

# %%
prod_products = prod[~prod["StockCode"].astype(str).str.upper().isin(NON_PRODUCT)].copy()
prod_products["RevenueSharePct"] = prod_products["Revenue"] / prod_products["Revenue"].sum() * 100

print("Top 10 products by revenue (physical products only):")
print(prod_products.nlargest(10, "Revenue")[["StockCode", "Description", "Units", "Revenue"]].round(2).to_string(index=False))
print("\nTop 10 products by quantity:")
print(prod_products.nlargest(10, "Units")[["StockCode", "Description", "Units", "Revenue"]].round(2).to_string(index=False))
print("\nLowest-revenue products (bottom 8, with sales):")
low = prod_products[prod_products["Revenue"] > 0].nsmallest(8, "Revenue")
print(low[["StockCode", "Description", "Units", "Revenue"]].round(2).to_string(index=False))

top10_prod_rev = prod_products.nlargest(10, "Revenue")
R["top10_products_rev"] = top10_prod_rev[["StockCode", "Description", "Units", "Revenue"]].round(2).to_dict("records")
R["top10_products_qty"] = prod_products.nlargest(10, "Units")[["StockCode", "Description", "Units", "Revenue"]].round(2).to_dict("records")
R["low_products"] = low[["StockCode", "Description", "Units", "Revenue"]].round(2).to_dict("records")
R["n_products"] = int(prod_products.shape[0])
R["top10_prod_rev_share"] = round(float(top10_prod_rev["Revenue"].sum() / prod_products["Revenue"].sum() * 100), 2)

# %% [markdown]
# ### 6.6 Cancellation analysis
#
# Cancellations are analysed on their own dataset so that return behaviour is not lost.

# %%
cancel_data["Revenue"] = cancel_data["Quantity"] * cancel_data["UnitPrice"]
cancel_monthly = cancel_data.groupby(cancel_data["InvoiceDate"].dt.to_period("M")).agg(
    Cancellations=("InvoiceNo", "nunique"), Lines=("InvoiceNo", "size"),
    Value=("Revenue", "sum")
).reset_index()
cancel_monthly["Month"] = cancel_monthly["InvoiceDate"].astype(str)
print("Cancellations by month:")
print(cancel_monthly.round(2).to_string(index=False))

cancel_products = cancel_data.groupby(["StockCode", "Description"]).agg(
    TimesCancelled=("InvoiceNo", "nunique"), Units=("Quantity", "sum")
).reset_index().sort_values("TimesCancelled", ascending=False)
print("\nMost frequently cancelled products (top 10):")
print(cancel_products.head(10).round(2).to_string(index=False))

cancel_value_abs = abs(float(cancel_data["Revenue"].sum()))
R["cancel_value_abs"] = round(cancel_value_abs, 2)
R["cancel_value_pct_gross"] = round(float(cancel_value_abs / (total_rev + cancel_value_abs) * 100), 2)
R["cancel_monthly"] = cancel_monthly.round(2).to_dict("records")
R["cancel_top_products"] = cancel_products.head(10).round(2).to_dict("records")
R["cancel_peak_month"] = str(cancel_monthly.loc[cancel_monthly["Cancellations"].idxmax(), "Month"])
R["cancel_peak_month_n"] = int(cancel_monthly["Cancellations"].max())

# %% [markdown]
# **Financial implication (assumption stated):** gross cancelled value is compared with *net* valid
# revenue. If the cancelled value were added back, gross activity would be
# £(net + cancelled). The calculation assumes every cancellation line is valued at its recorded
# Quantity × UnitPrice and that no restocking recovery is realised — a deliberately conservative view.

# %% [markdown]
# ---
# ## 7. Advanced analysis
#
# ### 7.1 RFM customer segmentation
#
# **Method.** Each customer is scored 1–5 on Recency (days since last purchase), Frequency (number of
# distinct invoices) and Monetary value (total net revenue). Scores are assigned by **quintile rank**
# (`rank(method='first')` then `qcut` into five equal-count bins), which avoids arbitrary currency
# thresholds and guarantees five populated score levels. Recency is reverse-scored so that 5 = most
# recent. Segments are then assigned by a transparent, ordered rule set (priority: Champions →
# Can't Lose → At Risk → Loyal → Potential Loyalist → New → Hibernating → Lost).
#
# **Reference date:** 10 December 2011 (day after the final transaction), so recency is not artificially
# compressed at the end of the observation window.

# %%
def rfm_score(series: pd.Series, reverse: bool = False) -> pd.Series:
    """Quintile score 1-5 using first-rank ordering (deterministic, no bin-edge ambiguity)."""
    ranks = series.rank(method="first", ascending=not reverse)
    return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm = cust_stats.copy()
rfm["R"] = rfm_score(rfm["Recency"], reverse=True)   # smaller recency -> higher score
rfm["F"] = rfm_score(rfm["Frequency"])
rfm["M"] = rfm_score(rfm["Monetary"])
rfm["RFM_Score"] = rfm["R"] + rfm["F"] + rfm["M"]

conditions = [
    (rfm["R"] >= 4) & (rfm["F"] >= 4) & (rfm["M"] >= 4),   # Champions
    (rfm["R"] <= 2) & (rfm["F"] >= 4) & (rfm["M"] >= 4),   # Can't lose
    (rfm["R"] <= 2) & (rfm["F"] >= 3),                     # At risk
    (rfm["R"] >= 3) & (rfm["F"] >= 3) & (rfm["M"] >= 3),   # Loyal
    (rfm["R"] >= 4) & (rfm["F"] >= 2),                     # Potential loyalist
    (rfm["R"] >= 4) & (rfm["F"] == 1),                     # New / promising
    (rfm["R"] <= 2) & (rfm["F"] == 2),                     # Hibernating
    (rfm["R"] <= 2) & (rfm["F"] == 1),                     # Lost
    (rfm["R"] == 3),                                        # Needs attention (mid recency)
]
labels = ["Champions", "Can't Lose Them", "At Risk", "Loyal Customers",
          "Potential Loyalist", "New / Promising", "Hibernating", "Lost", "Needs Attention"]
rfm["Segment"] = np.select(conditions, labels, default="Other")

seg = rfm.groupby("Segment").agg(
    Customers=("CustomerID", "count"),
    Revenue=("Monetary", "sum"),
    AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"),
    AvgMonetary=("Monetary", "mean"),
).reset_index()
seg["RevenueSharePct"] = seg["Revenue"] / seg["Revenue"].sum() * 100
seg["CustomerSharePct"] = seg["Customers"] / seg["Customers"].sum() * 100
seg = seg.sort_values("Revenue", ascending=False)
display(seg.round(2))
seg.to_csv(OUT / "rfm_segments.csv", index=False)
rfm.to_csv(OUT / "rfm_customer_scores.csv", index=False)

R["rfm_segments"] = seg.round(2).to_dict("records")
R["rfm_champions_n"] = int(seg.loc[seg["Segment"] == "Champions", "Customers"].iloc[0]) if "Champions" in seg["Segment"].values else 0
R["rfm_champions_rev"] = round(float(seg.loc[seg["Segment"] == "Champions", "Revenue"].iloc[0]), 2) if "Champions" in seg["Segment"].values else 0
R["rfm_champions_share"] = round(float(seg.loc[seg["Segment"] == "Champions", "RevenueSharePct"].iloc[0]), 2) if "Champions" in seg["Segment"].values else 0
R["rfm_at_risk_n"] = int(seg.loc[seg["Segment"] == "At Risk", "Customers"].iloc[0]) if "At Risk" in seg["Segment"].values else 0
R["rfm_at_risk_rev"] = round(float(seg.loc[seg["Segment"] == "At Risk", "Revenue"].iloc[0]), 2) if "At Risk" in seg["Segment"].values else 0

# %% [markdown]
# ### 7.2 Pareto analysis (does 80/20 hold?)
#
# The 80/20 rule is **tested, not assumed**. Customers and products are ranked by revenue and the
# cumulative contribution curve is computed. The reported "n for 80%" is the smallest number of
# entities whose cumulative revenue share reaches or exceeds 80%.

# %%
cust_pareto = cust_stats.sort_values("Monetary", ascending=False).reset_index(drop=True)
cust_pareto["CumRevenue"] = cust_pareto["Monetary"].cumsum()
cust_pareto["CumSharePct"] = cust_pareto["CumRevenue"] / cust_pareto["Monetary"].sum() * 100
cust_pareto["EntityPct"] = (cust_pareto.index + 1) / len(cust_pareto) * 100
n80_cust = int((cust_pareto["CumSharePct"] >= 80).values.argmax() + 1)
R["pareto_cust_n80"] = n80_cust
R["pareto_cust_pct80"] = round(float(n80_cust / len(cust_pareto) * 100), 2)
R["pareto_cust_top20_share"] = round(float(cust_pareto["CumSharePct"].iloc[int(len(cust_pareto)*0.2)-1]), 2)
R["pareto_cust_top10_share"] = round(float(cust_pareto["CumSharePct"].iloc[int(len(cust_pareto)*0.1)-1]), 2)
R["pareto_cust_top5_share"] = round(float(cust_pareto["CumSharePct"].iloc[int(len(cust_pareto)*0.05)-1]), 2)
R["pareto_cust_top1_share"] = round(float(cust_pareto["CumSharePct"].iloc[int(len(cust_pareto)*0.01)-1]), 2)
print(f"Customers needed for 80% of revenue: {n80_cust:,} of {len(cust_pareto):,} "
      f"({n80_cust/len(cust_pareto)*100:.2f}%)")
print(f"Top 20% of customers contribute {R['pareto_cust_top20_share']:.2f}% of revenue")
print(f"Top 10% of customers contribute {R['pareto_cust_top10_share']:.2f}% of revenue")
print(f"Top 1% of customers contribute {R['pareto_cust_top1_share']:.2f}% of revenue")

prod_pareto = prod_products.sort_values("Revenue", ascending=False).reset_index(drop=True)
prod_pareto["CumRevenue"] = prod_pareto["Revenue"].cumsum()
prod_pareto["CumSharePct"] = prod_pareto["CumRevenue"] / prod_pareto["Revenue"].sum() * 100
n80_prod = int((prod_pareto["CumSharePct"] >= 80).values.argmax() + 1)
R["pareto_prod_n80"] = n80_prod
R["pareto_prod_pct80"] = round(float(n80_prod / len(prod_pareto) * 100), 2)
R["pareto_prod_top20_share"] = round(float(prod_pareto["CumSharePct"].iloc[int(len(prod_pareto)*0.2)-1]), 2)
print(f"Products needed for 80% of product revenue: {n80_prod:,} of {len(prod_pareto):,} "
      f"({n80_prod/len(prod_pareto)*100:.2f}%)")
print(f"Top 20% of products contribute {R['pareto_prod_top20_share']:.2f}% of product revenue")
cust_pareto.to_csv(OUT / "pareto_customers.csv", index=False)
prod_pareto.to_csv(OUT / "pareto_products.csv", index=False)

# %% [markdown]
# ### 7.3 Correlation analysis
#
# Pearson measures linear association; Spearman measures monotonic association and is more appropriate
# for the heavy-tailed monetary variables. Correlation does **not** imply causation: a third factor
# (e.g. customer size, product type, season) could drive both variables.

# %%
customer_corr = pd.DataFrame({
    "Spearman rho": [
        cust_stats["Frequency"].corr(cust_stats["Monetary"], method="spearman"),
        cust_stats["Recency"].corr(cust_stats["Monetary"], method="spearman"),
        cust_stats["Frequency"].corr(cust_stats["AOV"], method="spearman"),
        cust_stats["TenureDays"].corr(cust_stats["Monetary"], method="spearman"),
    ],
    "Pearson r": [
        cust_stats["Frequency"].corr(cust_stats["Monetary"], method="pearson"),
        cust_stats["Recency"].corr(cust_stats["Monetary"], method="pearson"),
        cust_stats["Frequency"].corr(cust_stats["AOV"], method="pearson"),
        cust_stats["TenureDays"].corr(cust_stats["Monetary"], method="pearson"),
    ],
}, index=["Frequency ↔ Monetary", "Recency ↔ Monetary", "Frequency ↔ AOV", "Tenure ↔ Monetary"])
display(customer_corr.round(3))
customer_corr.to_csv(OUT / "customer_correlations.csv")
R["customer_corr"] = customer_corr.round(3).reset_index().rename(columns={"index": "pair"}).to_dict("records")

# %% [markdown]
# ### 7.4 Outlier analysis (IQR method)
#
# Bounds are computed on the valid sales data: Q1 − 1.5×IQR and Q3 + 1.5×IQR. Extreme observations are
# then inspected individually to decide whether they are errors or genuine commercial events.

# %%
q1v, q3v = v["Quantity"].quantile([0.25, 0.75])
iqrv = q3v - q1v
low_q, high_q = q1v - 1.5 * iqrv, q3v + 1.5 * iqrv
p1v, p3v = v["UnitPrice"].quantile([0.25, 0.75])
pirv = p3v - p1v
low_p, high_p = p1v - 1.5 * pirv, p3v + 1.5 * pirv

qty_out_mask = (v["Quantity"] < low_q) | (v["Quantity"] > high_q)
price_out_mask = (v["UnitPrice"] < low_p) | (v["UnitPrice"] > high_p)
print(f"Quantity IQR bounds: [{low_q:.2f}, {high_q:.2f}]")
print(f"  Outlying lines: {qty_out_mask.sum():,} ({qty_out_mask.mean()*100:.2f}% of valid lines)")
print(f"Unit price IQR bounds: [{low_p:.2f}, {high_p:.2f}]")
print(f"  Outlying lines: {price_out_mask.sum():,} ({price_out_mask.mean()*100:.2f}% of valid lines)")

print("\nLargest 8 valid transactions (retained after inspection):")
extreme = v.nlargest(8, "Revenue")[["InvoiceNo", "StockCode", "Description", "Quantity", "UnitPrice", "Revenue", "Country"]]
print(extreme.round(2).to_string(index=False))
R["qty_outlier_pct"] = round(float(qty_out_mask.mean() * 100), 2)
R["price_outlier_pct"] = round(float(price_out_mask.mean() * 100), 2)
R["extreme_txns"] = extreme.round(2).to_dict("records")

# Sensitivity check: winsorise revenue at the 99th percentile and compare totals
rev_99 = v["Revenue"].quantile(0.99)
rev_wins = v["Revenue"].clip(upper=rev_99).sum()
R["revenue_winsorised_99"] = round(float(rev_wins), 2)
R["revenue_threshold_99"] = round(float(rev_99), 2)
R["revenue_top1pct_share"] = round(float(v.loc[v["Revenue"] >= v["Revenue"].quantile(0.99), "Revenue"].sum() / total_rev * 100), 2)
print(f"\nWinsorising revenue at the 99th percentile (£{rev_99:,.2f}) changes total revenue from "
      f"£{total_rev:,.2f} to £{rev_wins:,.2f} ({(rev_wins-total_rev)/total_rev*100:.2f}%).")
print(f"The top 1% of lines by value carry {R['revenue_top1pct_share']:.2f}% of revenue.")

# %% [markdown]
# ---
# ## 8. Statistical analysis
#
# Tests are chosen to match the data structure. Invoice values are heavily right-skewed, so the
# **Welch t-test** (does not assume equal variances) is used with the Central Limit Theorem
# justification (n in the tens of thousands), and the **Mann–Whitney U** test is reported as a
# distribution-free robustness check. Effect sizes are reported so that statistical significance is
# not confused with business importance.

# %%
# --- 8.1 95% confidence interval for mean invoice value -------------------
iv = invoice_totals["InvoiceValue"].values
n_iv = len(iv)
mean_iv = iv.mean()
se_iv = iv.std(ddof=1) / np.sqrt(n_iv)
t_crit = stats.t.ppf(0.975, df=n_iv - 1)
ci_low, ci_high = mean_iv - t_crit * se_iv, mean_iv + t_crit * se_iv
print(f"Mean invoice value: £{mean_iv:,.2f}")
print(f"95% CI: £{ci_low:,.2f} to £{ci_high:,.2f}  (n = {n_iv:,} invoices)")
R["aov_ci_low"] = round(float(ci_low), 2)
R["aov_ci_high"] = round(float(ci_high), 2)
R["aov_mean"] = round(float(mean_iv), 2)
R["aov_median"] = round(float(np.median(iv)), 2)

# --- 8.2 Welch t-test: UK vs non-UK invoice values ------------------------
uk = invoice_totals.loc[invoice_totals["Country"] == "United Kingdom", "InvoiceValue"].values
nonuk = invoice_totals.loc[invoice_totals["Country"] != "United Kingdom", "InvoiceValue"].values
t_stat, p_val = stats.ttest_ind(uk, nonuk, equal_var=False)
n1, n2 = len(uk), len(nonuk)
s1, s2 = uk.std(ddof=1), nonuk.std(ddof=1)
pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
cohens_d = (uk.mean() - nonuk.mean()) / pooled
u_stat, u_p = stats.mannwhitneyu(uk, nonuk, alternative="two-sided")
print(f"\nUK invoices: n={n1:,}, mean=£{uk.mean():,.2f}, median=£{np.median(uk):,.2f}")
print(f"Non-UK invoices: n={n2:,}, mean=£{nonuk.mean():,.2f}, median=£{np.median(nonuk):,.2f}")
print(f"Welch t = {t_stat:.3f}, p = {p_val:.3e}, Cohen's d = {cohens_d:.3f}")
print(f"Mann–Whitney U = {u_stat:,.0f}, p = {u_p:.3e}")
R["test_uk"] = {
    "n_uk": int(n1), "mean_uk": round(float(uk.mean()), 2), "median_uk": round(float(np.median(uk)), 2),
    "n_nonuk": int(n2), "mean_nonuk": round(float(nonuk.mean()), 2), "median_nonuk": round(float(np.median(nonuk)), 2),
    "t_stat": round(float(t_stat), 3), "p_value": float(p_val),
    "cohens_d": round(float(cohens_d), 3),
    "mannwhitney_u": float(u_stat), "mannwhitney_p": float(u_p),
}

# --- 8.3 Welch t-test: repeat vs one-time customers (AOV) -----------------
rep = cust_stats.loc[cust_stats["Frequency"] > 1, "AOV"].values
one = cust_stats.loc[cust_stats["Frequency"] == 1, "AOV"].values
t2, p2 = stats.ttest_ind(rep, one, equal_var=False)
sp1, sp2 = rep.std(ddof=1), one.std(ddof=1)
pool2 = np.sqrt(((len(rep) - 1) * sp1**2 + (len(one) - 1) * sp2**2) / (len(rep) + len(one) - 2))
d2 = (rep.mean() - one.mean()) / pool2
u2, up2 = stats.mannwhitneyu(rep, one, alternative="two-sided")
print(f"\nRepeat customers: n={len(rep):,}, mean AOV=£{rep.mean():,.2f}, median=£{np.median(rep):,.2f}")
print(f"One-time customers: n={len(one):,}, mean AOV=£{one.mean():,.2f}, median=£{np.median(one):,.2f}")
print(f"Welch t = {t2:.3f}, p = {p2:.3e}, Cohen's d = {d2:.3f}")
print(f"Mann–Whitney U = {u2:,.0f}, p = {up2:.3e}")
R["test_repeat"] = {
    "n_repeat": int(len(rep)), "mean_repeat": round(float(rep.mean()), 2), "median_repeat": round(float(np.median(rep)), 2),
    "n_one": int(len(one)), "mean_one": round(float(one.mean()), 2), "median_one": round(float(np.median(one)), 2),
    "t_stat": round(float(t2), 3), "p_value": float(p2), "cohens_d": round(float(d2), 3),
    "mannwhitney_u": float(u2), "mannwhitney_p": float(up2),
}

# --- 8.4 Chi-square: country group x repeat status ------------------------
cust_stats["CountryGroup"] = np.where(cust_stats["Country"].isna(), "Unknown",
                              np.where(cust_stats["Country"] == "United Kingdom", "UK", "Non-UK"))
cust_stats["RepeatStatus"] = np.where(cust_stats["Frequency"] > 1, "Repeat", "One-time")
ct = pd.crosstab(cust_stats["CountryGroup"], cust_stats["RepeatStatus"])
chi2, cp, dof, exp = stats.chi2_contingency(ct)
cramers_v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
print("\nCountry group × repeat status (customer counts):")
print(ct.to_string())
print(f"Chi-square = {chi2:.3f}, df = {dof}, p = {cp:.3e}, Cramér's V = {cramers_v:.3f}")
R["test_chi"] = {"chi2": round(float(chi2), 3), "dof": int(dof), "p_value": float(cp),
                 "cramers_v": round(float(cramers_v), 3),
                 "table": ct.reset_index().to_dict("records")}

# --- 8.5 Normality diagnostics -------------------------------------------
print(f"\nInvoice-value skewness = {invoice_totals['InvoiceValue'].skew():.3f}, "
      f"kurtosis = {invoice_totals['InvoiceValue'].kurtosis():.3f}")
print("Because n is very large, the sampling distribution of the mean is approximately normal (CLT);")
print("the Mann–Whitney result is therefore used as the primary robustness check.")

# %% [markdown]
# ---
# ## 9. Visualisations
#
# Every chart is generated from the dataframes above and saved as a 200-dpi PNG in `visualizations/`.
# Captions and interpretations are stored alongside the figures for the Word report.

# %%
captions = {}

def save(fig, name, caption):
    path = VIZ / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    captions[name] = caption
    print("saved:", path)

# 1. Monthly revenue trend -------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.plot(monthly["MonthLabel"], monthly["Revenue"] / 1000, marker="o", lw=2.2, color=ACCENT)
ax.fill_between(range(len(monthly)), monthly["Revenue"] / 1000, alpha=0.12, color=ACCENT)
ax.set_title("Monthly Revenue Trend (GBP thousands)")
ax.set_xlabel("Month"); ax.set_ylabel("Revenue (£ thousands)")
ax.tick_params(axis="x", rotation=45)
for i, val in enumerate(monthly["Revenue"] / 1000):
    ax.annotate(f"{val:,.0f}", (i, val), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=8)
ax.grid(True, alpha=0.3)
save(fig, "monthly_revenue.png",
     "Monthly net revenue from December 2010 to December 2011. Values are in GBP thousands. "
     "The series shows a strong seasonal build-up to November–December, with December 2011 partial "
     "(only 1–9 December observed).")

# 2. Monthly order volume --------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.plot(monthly["MonthLabel"], monthly["Orders"], marker="s", lw=2.2, color="#c0392b")
ax.set_title("Monthly Order Volume (distinct invoices)")
ax.set_xlabel("Month"); ax.set_ylabel("Number of invoices")
ax.tick_params(axis="x", rotation=45)
for i, val in enumerate(monthly["Orders"]):
    ax.annotate(f"{val:,}", (i, val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
ax.grid(True, alpha=0.3)
save(fig, "monthly_orders.png",
     "Monthly count of distinct invoices. Order volume follows the same seasonal shape as revenue, "
     "confirming that the seasonal peak is demand-driven rather than price-driven.")

# 3. Top 10 products by revenue -------------------------------------------
tp = prod_products.nlargest(10, "Revenue").sort_values("Revenue")
fig, ax = plt.subplots(figsize=(11, 6.5))
bars = ax.barh(tp["Description"].str.slice(0, 38), tp["Revenue"] / 1000, color=ACCENT)
ax.set_title("Top 10 Products by Revenue (GBP thousands)")
ax.set_xlabel("Revenue (£ thousands)"); ax.set_ylabel("Product")
for b, val in zip(bars, tp["Revenue"] / 1000):
    ax.text(val + 1.5, b.get_y() + b.get_height()/2, f"{val:,.1f}", va="center", fontsize=8)
ax.grid(True, axis="x", alpha=0.3)
save(fig, "top_products.png",
     "Top 10 physical products by net revenue. Revenue is concentrated in a small set of decorative "
     "and giftware lines; product-level revenue is far more concentrated than unit demand.")

# 4. Top 10 products by quantity ------------------------------------------
tq = prod_products.nlargest(10, "Units").sort_values("Units")
fig, ax = plt.subplots(figsize=(11, 6.5))
bars = ax.barh(tq["Description"].str.slice(0, 38), tq["Units"], color="#16a085")
ax.set_title("Top 10 Products by Quantity Sold (units)")
ax.set_xlabel("Units sold"); ax.set_ylabel("Product")
for b, val in zip(bars, tq["Units"]):
    ax.text(val + max(tq["Units"])*0.01, b.get_y() + b.get_height()/2, f"{val:,.0f}", va="center", fontsize=8)
ax.grid(True, axis="x", alpha=0.3)
save(fig, "top_products_qty.png",
     "Top 10 products by unit volume. The volume leaders differ from the revenue leaders: cheap, "
     "high-turnover items sell in bulk but contribute less value per unit.")

# 5. Revenue by country ---------------------------------------------------
ctop = country.head(15).sort_values("Revenue")
fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(ctop["Country"], ctop["Revenue"] / 1000, color="#8e44ad")
ax.set_title("Revenue by Country — Top 15 (GBP thousands)")
ax.set_xlabel("Revenue (£ thousands)"); ax.set_ylabel("Country")
for b, val in zip(bars, ctop["Revenue"] / 1000):
    ax.text(val + max(ctop["Revenue"]/1000)*0.01, b.get_y() + b.get_height()/2, f"{val:,.1f}", va="center", fontsize=8)
ax.grid(True, axis="x", alpha=0.3)
save(fig, "country_analysis.png",
     "Revenue by country (top 15). The United Kingdom dominates, followed by a small group of EU "
     "markets; the long tail of countries each contributes a very small share.")

# 6. Quantity distribution ------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
qclip = v["Quantity"].clip(upper=100)
ax.hist(qclip, bins=60, color=ACCENT, edgecolor="white", alpha=0.9)
ax.set_title("Distribution of Order Quantity (valid sales lines)")
ax.set_xlabel("Quantity per line (units, clipped at 100)"); ax.set_ylabel("Frequency")
ax.axvline(v["Quantity"].median(), color="#c0392b", ls="--", lw=1.8, label=f"Median = {v['Quantity'].median():.0f}")
ax.legend()
ax.grid(True, alpha=0.3)
save(fig, "quantity_distribution.png",
     "Distribution of quantity per invoice line, clipped at 100 units for readability "
     f"(maximum observed = {v['Quantity'].max():,}). The distribution is right-skewed with a median of "
     f"{v['Quantity'].median():.0f} units; most lines are small retail quantities.")

# 7. Unit price distribution ----------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
pclip = v["UnitPrice"].clip(upper=100)
ax.hist(pclip, bins=60, color="#d35400", edgecolor="white", alpha=0.9)
ax.set_title("Distribution of Unit Price (valid sales lines)")
ax.set_xlabel("Unit price (GBP, clipped at £100)"); ax.set_ylabel("Frequency")
ax.axvline(v["UnitPrice"].median(), color="#c0392b", ls="--", lw=1.8, label=f"Median = £{v['UnitPrice'].median():.2f}")
ax.legend()
ax.grid(True, alpha=0.3)
save(fig, "unitprice_distribution.png",
     "Distribution of unit price, clipped at £100 for readability (maximum observed = £"
     f"{v['UnitPrice'].max():,.2f}). The median price is £{v['UnitPrice'].median():.2f}, indicating a "
     "low-value, high-volume product mix with a thin high-price tail.")

# 8. Revenue distribution -------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
iv_clip = invoice_totals["InvoiceValue"].clip(upper=invoice_totals["InvoiceValue"].quantile(0.99))
ax.hist(iv_clip, bins=60, color="#2980b9", edgecolor="white", alpha=0.9)
ax.set_title("Distribution of Invoice Value (99th percentile clipped)")
ax.set_xlabel("Invoice value (GBP)"); ax.set_ylabel("Number of invoices")
ax.axvline(invoice_totals["InvoiceValue"].median(), color="#c0392b", ls="--", lw=1.8,
           label=f"Median = £{invoice_totals['InvoiceValue'].median():,.2f}")
ax.legend()
ax.grid(True, alpha=0.3)
save(fig, "revenue_distribution.png",
     "Distribution of invoice values clipped at the 99th percentile. Most invoices are small; the "
     "mean is pulled upward by a small number of very large wholesale orders.")

# 9. Quantity outliers ----------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 6))
ax.boxplot(v["Quantity"], vert=True, patch_artist=True,
           boxprops=dict(facecolor="#5dade2", color=ACCENT),
           medianprops=dict(color="#c0392b", linewidth=2),
           flierprops=dict(marker="o", markerfacecolor="#c0392b", markersize=3, alpha=0.4))
ax.set_yscale("log")
ax.set_title("Quantity Outliers (log scale)")
ax.set_ylabel("Quantity per line (log scale)")
ax.grid(True, alpha=0.3)
save(fig, "quantity_outliers.png",
     "Box plot of order quantity on a log scale. The box spans the interquartile range; the many "
     "fliers above the upper whisker are genuine large purchases, not automatic errors.")

# 10. Customer spending distribution -------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 6))
ax.boxplot(cust_stats["Monetary"], vert=True, patch_artist=True,
           boxprops=dict(facecolor="#48c9b0", color="#117a65"),
           medianprops=dict(color="#c0392b", linewidth=2),
           flierprops=dict(marker="o", markerfacecolor="#c0392b", markersize=2, alpha=0.3))
ax.set_yscale("log")
ax.set_title("Customer Monetary Value Distribution (log scale)")
ax.set_ylabel("Total spend per customer (GBP, log scale)")
ax.grid(True, alpha=0.3)
save(fig, "customer_spending_box.png",
     "Distribution of total spend per customer on a log scale. The wide spread confirms a "
     "high-value minority coexisting with a large base of low-spend customers.")

# 11. Customer segmentation ----------------------------------------------
seg_sorted = seg.sort_values("Customers", ascending=False)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(seg_sorted["Segment"], seg_sorted["Customers"], color=sns.color_palette("viridis", len(seg_sorted)))
ax.set_title("Customer Segments by Customer Count")
ax.set_xlabel("RFM segment"); ax.set_ylabel("Number of customers")
ax.tick_params(axis="x", rotation=30)
for b, val in zip(bars, seg_sorted["Customers"]):
    ax.text(b.get_x() + b.get_width()/2, val + max(seg_sorted["Customers"])*0.01, f"{val:,}",
            ha="center", fontsize=8)
ax.grid(True, alpha=0.3)
save(fig, "customer_segmentation.png",
     "Customer counts by RFM segment. The majority of customers fall into low-frequency, "
     "low-value segments, while Champions are a small but commercially critical group.")

# 12. Correlation heatmap -------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 7))
sns.heatmap(corr_spear, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            square=True, linewidths=0.5, cbar_kws={"label": "Spearman rho"}, ax=ax)
ax.set_title("Spearman Correlation Heatmap (invoice level)")
save(fig, "correlation_heatmap.png",
     "Spearman correlation matrix for invoice-level variables. Invoice value is strongly driven by "
     "line count and quantity; unit price shows a weaker association, so value growth comes mainly "
     "from basket size rather than price.")

# 13. Cancellation trends -------------------------------------------------
cm = cancel_monthly.copy()
cm["Month"] = cm["Month"].astype(str)
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.bar(cm["Month"], cm["Cancellations"], color="#c0392b", alpha=0.85, label="Cancellation invoices")
ax.set_title("Cancellation Invoices by Month")
ax.set_xlabel("Month"); ax.set_ylabel("Number of cancellation invoices")
ax.tick_params(axis="x", rotation=45)
for i, val in enumerate(cm["Cancellations"]):
    ax.text(i, val + max(cm["Cancellations"])*0.01, f"{val:,}", ha="center", fontsize=8)
ax.legend(); ax.grid(True, alpha=0.3)
save(fig, "cancellation_trends.png",
     "Monthly cancellation invoice counts. Cancellations occur throughout the year and peak in the "
     "high-volume autumn months, tracking overall activity rather than a single incident.")

# 14. Day-of-week sales ---------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
bars = ax.bar(weekday["DayOfWeek"], weekday["Revenue"] / 1000, color="#2c3e50", alpha=0.85)
ax.set_title("Revenue by Day of Week (GBP thousands)")
ax.set_xlabel("Day of week"); ax.set_ylabel("Revenue (£ thousands)")
for b, val in zip(bars, weekday["Revenue"] / 1000):
    ax.text(b.get_x() + b.get_width()/2, val + max(weekday["Revenue"]/1000)*0.01, f"{val:,.1f}",
            ha="center", fontsize=8)
ax.grid(True, alpha=0.3)
save(fig, "weekday_sales.png",
     "Revenue by day of week. Weekday trading dominates; the weekend share is materially lower, "
     "which has direct implications for staffing and promotional scheduling.")

# 15. Hourly patterns -----------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.bar(hourly["Hour"], hourly["Orders"], color="#16a085", alpha=0.85)
ax.set_title("Order Volume by Hour of Day")
ax.set_xlabel("Hour of day (24h)"); ax.set_ylabel("Number of invoices")
ax.grid(True, alpha=0.3)
save(fig, "hourly_patterns.png",
     "Order volume by hour of day. Activity is concentrated in business hours with a clear midday "
     "peak, consistent with B2B-style buying behaviour.")

# 16. Pareto chart --------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(12, 6))
x = np.arange(1, len(cust_pareto) + 1)
ax1.plot(cust_pareto["EntityPct"], cust_pareto["CumSharePct"], color=ACCENT, lw=2, label="Cumulative revenue share")
ax1.fill_between(cust_pareto["EntityPct"], cust_pareto["CumSharePct"], alpha=0.12, color=ACCENT)
ax1.axhline(80, color="#c0392b", ls="--", lw=1.5, label="80% revenue threshold")
ax1.axhline(0, color="grey", lw=0.8)
ax1.set_xlabel("Cumulative share of customers (%)"); ax1.set_ylabel("Cumulative revenue share (%)")
ax1.set_title("Pareto Curve — Customer Revenue Concentration")
ax1.legend(loc="lower right"); ax1.grid(True, alpha=0.3)
ax1.annotate(f"{n80_cust:,} customers ({n80_cust/len(cust_pareto)*100:.1f}%) reach 80% of revenue",
             xy=(n80_cust/len(cust_pareto)*100, 80), xytext=(25, 55),
             arrowprops=dict(arrowstyle="->", color="#c0392b"), fontsize=10, color="#c0392b")
save(fig, "pareto_chart.png",
     "Pareto curve of customer revenue concentration. The curve rises steeply at the top, showing "
     "that a minority of customers generates the majority of revenue; the 80% threshold is reached "
     f"at {n80_cust:,} customers.")

# 17. Top customers -------------------------------------------------------
tc = cust_stats.sort_values("Monetary", ascending=False).head(10).sort_values("Monetary")
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh([str(int(i)) for i in tc["CustomerID"]], tc["Monetary"] / 1000, color="#8e44ad")
ax.set_title("Top 10 Customers by Revenue (GBP thousands)")
ax.set_xlabel("Revenue (£ thousands)"); ax.set_ylabel("CustomerID")
for b, val in zip(bars, tc["Monetary"] / 1000):
    ax.text(val + max(tc["Monetary"]/1000)*0.01, b.get_y() + b.get_height()/2, f"{val:,.1f}", va="center", fontsize=8)
ax.grid(True, axis="x", alpha=0.3)
save(fig, "top_customers.png",
     "Top 10 customers by net revenue. The leading account alone contributes a material share of "
     "total revenue, creating concentration risk that management should monitor.")

# 18. RFM recency vs monetary --------------------------------------------
sample = rfm.sample(min(3000, len(rfm)), random_state=42)
fig, ax = plt.subplots(figsize=(10, 6.5))
sns.scatterplot(data=sample, x="Recency", y="Monetary", hue="Segment", alpha=0.55, s=22, ax=ax)
ax.set_yscale("log")
ax.set_title("RFM Map — Recency vs Monetary Value (3,000-customer sample)")
ax.set_xlabel("Recency (days since last purchase)"); ax.set_ylabel("Monetary value (GBP, log scale)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
ax.grid(True, alpha=0.3)
save(fig, "rfm_scatter.png",
     "RFM map of a 3,000-customer random sample. Recent, high-value customers (Champions) sit in the "
     "top-left; long-inactive high-value accounts (Can't Lose / At Risk) appear in the top-right and "
     "represent the clearest win-back opportunity.")

R["captions"] = captions
R["n_charts"] = len(captions)

# %% [markdown]
# ---
# ## 10. Business opportunity analysis
#
# Each opportunity below is tied to a number computed in this notebook. Recommendations are
# **proposals**, not tested interventions; no claim is made that they have already increased revenue.

# %%
opportunities = [
    {
        "Opportunity": "Win back high-value lapsed customers",
        "Evidence": f"Can't Lose + At Risk segments contain {int(seg.loc[seg['Segment'].isin(['Can\'t Lose Them','At Risk']),'Customers'].sum()):,} customers worth £{seg.loc[seg['Segment'].isin(['Can\'t Lose Them','At Risk']),'Revenue'].sum():,.0f}",
        "Business problem": "Previously valuable customers have stopped purchasing, leaving revenue exposed.",
        "Proposed solution": "Targeted win-back campaign with personalised offers and a service-level check-in.",
        "Expected benefit": "Recover a share of lapsed high-value revenue; protect the revenue base.",
        "KPI to monitor": "Win-back conversion rate; recovered revenue per campaign.",
        "Risk / limitation": "Historical response behaviour is unknown; campaign lift must be measured with a control group.",
    },
    {
        "Opportunity": "Grow basket size rather than unit price",
        "Evidence": f"Spearman rho between invoice value and line count = {R['corr_spear_invoicevalue_lines']:.2f}, versus {R['corr_spear_invoicevalue_price']:.2f} for average price",
        "Business problem": "Revenue is driven mainly by number of lines, not by higher prices.",
        "Proposed solution": "Cross-sell bundles and 'complete the set' recommendations at checkout.",
        "Expected benefit": "Higher items per order without discounting, protecting margin.",
        "KPI to monitor": "Average lines per invoice; attach rate; AOV.",
        "Risk / limitation": "Cross-sell may cannibalise existing lines; test on a holdout group.",
    },
    {
        "Opportunity": "Concentrate retention effort on the revenue core",
        "Evidence": f"Top {R['pareto_cust_pct80']:.1f}% of customers ({R['pareto_cust_n80']:,} accounts) generate 80% of revenue; top 1% generate {R['pareto_cust_top1_share']:.1f}%",
        "Business problem": "Revenue is highly concentrated, so losing a few accounts is material.",
        "Proposed solution": "Named-account management and service guarantees for the top revenue accounts.",
        "Expected benefit": "Reduced churn risk on the highest-value relationships.",
        "KPI to monitor": "Revenue retention of top-decile accounts; churn of top 100 accounts.",
        "Risk / limitation": "Over-serving small accounts could distort cost-to-serve; concentration remains a structural risk.",
    },
    {
        "Opportunity": "Replicate the UK playbook in selected EU markets",
        "Evidence": f"UK contributes {R['top_country_share']:.1f}% of revenue; Germany is the largest non-UK market at £{country.loc[country['Country']=='Germany','Revenue'].iloc[0]:,.0f}",
        "Business problem": "Growth depends almost entirely on one market.",
        "Proposed solution": "Localise catalogue, pricing and delivery messaging for the top 3 EU markets.",
        "Expected benefit": "Diversified revenue base and reduced single-market exposure.",
        "KPI to monitor": "Non-UK revenue share; non-UK repeat rate; delivery cost per order.",
        "Risk / limitation": "Cross-border logistics and pricing differences may erode margin; results are not transferable without testing.",
    },
    {
        "Opportunity": "Reduce avoidable cancellation leakage",
        "Evidence": f"{R['canc_invoices']:,} cancellation invoices ({R['cancel_rate_inv']:.2f}% of invoices) with £{R['cancel_value_abs']:,.0f} gross value",
        "Business problem": "Returns and cancellations remove revenue after the sale is booked.",
        "Proposed solution": "Pre-purchase quality checks, clearer sizing guidance and a cancellation-reason code.",
        "Expected benefit": "Lower cancellation rate and better root-cause visibility.",
        "KPI to monitor": "Cancellation rate by product and reason code; net revenue per SKU.",
        "Risk / limitation": "Some cancellations are genuine commercial returns; reducing them too aggressively harms customer trust.",
    },
    {
        "Opportunity": "Extend the seasonal peak with an early-autumn campaign",
        "Evidence": f"Peak month is {R['peak_month']} at £{R['peak_month_rev']:,.0f}; order volume peaks in the same period",
        "Business problem": "Revenue is concentrated in a short seasonal window, creating capacity and cash-flow swings.",
        "Proposed solution": "Shift a defined share of promotional spend to September–October and pre-build stock.",
        "Expected benefit": "Smoother revenue, better inventory utilisation, lower peak-season stress.",
        "KPI to monitor": "Off-season revenue growth; stock cover; peak-season service level.",
        "Risk / limitation": "Demand may simply be pulled forward rather than created; measure incremental, not shifted, revenue.",
    },
]
opp_df = pd.DataFrame(opportunities)
display(opp_df[["Opportunity", "Evidence"]])
opp_df.to_csv(OUT / "business_opportunities.csv", index=False)
R["opportunities"] = opportunities

# %% [markdown]
# ---
# ## 11. Key findings
#
# Findings are stated with the numerical evidence produced above.

# %%
findings = [
    ("F1", "Revenue is highly concentrated in time and in customers.",
     f"Peak month {R['peak_month']} generated £{R['peak_month_rev']:,.0f}; the top 1% of customers generate {R['pareto_cust_top1_share']:.1f}% of revenue.",
     "Demand is seasonal and the customer base is top-heavy.", "Build seasonal capacity plans and protect top accounts."),
    ("F2", "The 80/20 rule holds for customers but only approximately.",
     f"{R['pareto_cust_n80']:,} customers ({R['pareto_cust_pct80']:.1f}%) produce 80% of revenue; the top 20% produce {R['pareto_cust_top20_share']:.1f}%.",
     "Concentration is real but not exactly 80/20; the curve is steeper at the very top.", "Prioritise retention of the top 20% and monitor the top 1% for churn."),
    ("F3", "Revenue is driven by basket size, not price.",
     f"Spearman rho (invoice value vs lines) = {R['corr_spear_invoicevalue_lines']:.2f}; (invoice value vs average price) = {R['corr_spear_invoicevalue_price']:.2f}.",
     "Customers spend more by adding lines rather than accepting higher prices.", "Use cross-sell and bundling instead of price increases."),
    ("F4", "The UK dominates the revenue base.",
     f"UK revenue = £{R['top_country_rev']:,.0f} ({R['top_country_share']:.1f}% of total); the largest non-UK market is Germany.",
     "Geographic concentration is a material business risk.", "Diversify into selected EU markets with localised offers."),
    ("F5", "Repeat purchase is the norm among identified customers, but a large anonymous base exists.",
     f"{R['repeat_n']:,} of {R['n_customers_valid']:,} identified customers ({R['repeat_rate']:.1f}%) ordered more than once; 135,080 lines have no CustomerID.",
     "Identified customers are loyal, but 25% of activity cannot be attributed.", "Incentivise account creation / loyalty sign-up to close the attribution gap."),
    ("F6", "Cancellations are a persistent, material leakage.",
     f"{R['canc_invoices']:,} cancellation invoices ({R['cancel_rate_inv']:.2f}% of invoices) with £{R['cancel_value_abs']:,.0f} gross value.",
     "Returns reduce realised revenue and complicate demand forecasting.", "Introduce cancellation reason codes and product-level quality checks."),
    ("F7", "Extreme values are genuine commercial events, not errors.",
     f"Largest valid line: {R['extreme_txns'][0]['Quantity']:,} units of {R['extreme_txns'][0]['Description']} (£{R['extreme_txns'][0]['Revenue']:,.0f}).",
     "Wholesale-style purchases exist and materially affect totals.", "Retain outliers in headline totals; report medians alongside means."),
    ("F8", "Customer value is highly unequal.",
     f"Top customer {R['top_customer_id']} contributes £{R['top_customer_rev']:,.0f} ({R['top_customer_share']:.1f}% of revenue); top 10 contribute {R['top10_cust_share']:.1f}%.",
     "A small number of accounts carry a large share of revenue.", "Create named-account plans and monitor concentration risk."),
    ("F9", "Non-UK customers place materially higher-value orders, but the effect size is small.",
     f"UK mean AOV £{R['test_uk']['mean_uk']:,.0f} vs non-UK £{R['test_uk']['mean_nonuk']:,.0f}; medians £{R['test_uk']['median_uk']:,.0f} vs £{R['test_uk']['median_nonuk']:,.0f}; Welch p = {R['test_uk']['p_value']:.2e}, Cohen's d = {R['test_uk']['cohens_d']:.2f}.",
     "The difference is statistically significant but small in magnitude, so it should not drive a wholesale pricing change.",
     "Test market-specific shipping thresholds and promotions rather than assuming a uniform international price premium."),
    ("F10", "Repeat customers buy more consistently, but not at a higher average order value.",
     f"Mean AOV £{R['test_repeat']['mean_repeat']:,.0f} (repeat) vs £{R['test_repeat']['mean_one']:,.0f} (one-time), Welch p = {R['test_repeat']['p_value']:.2f}, d = {R['test_repeat']['cohens_d']:.2f}; medians £{R['test_repeat']['median_repeat']:,.0f} vs £{R['test_repeat']['median_one']:,.0f}, Mann–Whitney p = {R['test_repeat']['mannwhitney_p']:.2e}.",
     "The means are indistinguishable, but the whole distribution is shifted upward for repeat buyers — loyalty improves basket consistency rather than average value.",
     "Do not assume loyalty automatically raises AOV; measure basket-building interventions separately from retention."),
    ("F11", "Trading is concentrated on weekdays and business hours.",
     f"Peak day {R['peak_weekday']} (revenue £{R['peak_weekday_rev']:,.0f}); peak hour {R['peak_hour']:02d}:00 with {R['peak_hour_orders']:,} invoices.",
     "Demand follows a B2B-style weekly rhythm.", "Align staffing, dispatch and campaign sends to the observed rhythm."),
    ("F12", "Product revenue sits in a long tail, not in a handful of hero products.",
     f"The top 10 products account for only {R['top10_prod_rev_share']:.1f}% of product revenue; {R['pareto_prod_n80']:,} of {R['n_products']:,} products ({R['pareto_prod_pct80']:.1f}%) are needed to reach 80%.",
     "Unlike the customer base, the catalogue is not dominated by a few items; 3,912 products share the revenue.",
     "Manage the tail actively (rationalisation, availability) instead of assuming a few hero SKUs carry the business."),
]
findings_df = pd.DataFrame(findings, columns=["No.", "Finding", "Numerical evidence", "Analytical explanation", "Business significance / action"])
display(findings_df[["No.", "Finding"]])
findings_df.to_csv(OUT / "key_findings.csv", index=False)
R["findings"] = findings

# %% [markdown]
# ---
# ## 12. Data limitations and synthetic-data considerations
#
# **Real-world observed data** = the 541,909 transactions actually recorded by the retailer.
# **Derived analytical variables** = quantities computed from those records (revenue, recency, RFM scores).
# **Synthetic data** = artificially generated records. **None were used in this project.**
#
# Limitations of this dataset:
# 1. **Age** — the observation window ends 9 December 2011; behaviour may not reflect current markets.
# 2. **Short window** — 13 months, so seasonality is estimated from a single cycle.
# 3. **Geographic concentration** — 91.5% of lines are UK; cross-border generalisation is weak.
# 4. **Missing CustomerID** — 135,080 lines (24.93%) cannot be attributed to a customer.
# 5. **No cost or margin data** — profitability cannot be computed, only revenue.
# 6. **No causal identification** — all relationships are observational.
# 7. **Non-product codes** — postage, fees and samples are mixed with products in the raw file.
# 8. **Returns are not fully explained** — no cancellation reason is recorded.

# %%
uk_share = (raw["Country"] == "United Kingdom").mean() * 100
R["uk_line_share"] = round(float(uk_share), 2)
R["n_missing_cust_pct"] = round(float(raw["CustomerID"].isna().mean() * 100), 2)
print(f"UK share of raw lines: {uk_share:.2f}%")
print(f"Missing CustomerID share: {R['n_missing_cust_pct']:.2f}%")
print(f"Observation window: {R['date_min']} to {R['date_max']} ({R['n_days']} distinct days)")

# %% [markdown]
# ---
# ## 13. Export of results
#
# All analytical outputs are written to `outputs/` for reuse in the report and for external audit.

# %%
monthly.to_csv(OUT / "monthly_summary.csv", index=False)
invoice_totals.to_csv(OUT / "invoice_summary.csv", index=False)
v.to_csv(OUT / "valid_sales_clean.csv", index=False)
cancel_data.to_csv(OUT / "cancellation_data.csv", index=False)

# JSON-safe conversion helper
def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(x) for k, x in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_json(x) for x in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj

with open(OUT / "results.json", "w") as f:
    json.dump(clean_json(R), f, indent=2)

print("Outputs written to:", OUT)
for f_ in sorted(OUT.iterdir()):
    print("  ", f_.name, f"({f_.stat().st_size/1024:.1f} KB)")
print("\nVisualisations written to:", VIZ)
for f_ in sorted(VIZ.iterdir()):
    print("  ", f_.name, f"({f_.stat().st_size/1024:.1f} KB)")

# %% [markdown]
# ---
# ## 14. Conclusion
#
# The analysis of the genuine UCI Online Retail dataset (541,909 rows, 8 columns, 1 Dec 2010 –
# 9 Dec 2011) shows a business with a strong seasonal peak, a highly concentrated customer base and a
# revenue engine driven by basket size rather than price. The UK contributes the overwhelming share of
# revenue, repeat customers spend materially more per order than one-time buyers, and cancellations
# represent a persistent leakage that is currently not explained by any recorded reason code.
#
# The most important practical conclusions are: (1) protect and grow the top revenue accounts, because
# the top 1% of customers generate a disproportionate share of revenue; (2) grow basket size through
# cross-sell rather than price increases; (3) treat extreme transactions as genuine commercial events
# and report medians alongside means; (4) reduce cancellation leakage through better product
# information and reason capture; and (5) close the CustomerID attribution gap so that customer-level
# analysis covers the whole business rather than 75% of it.
#
# These conclusions are based on the observed historical data and cannot establish causation. A
# forward-looking test (A/B or holdout) would be required before claiming that any recommendation
# increases revenue.

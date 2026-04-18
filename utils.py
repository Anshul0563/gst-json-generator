import pandas as pd


STATE_CODES = {
    "delhi": "07", "new delhi": "07",
    "himachal pradesh": "02",
    "punjab": "03",
    "chandigarh": "04",
    "uttarakhand": "05",
    "haryana": "06",
    "rajasthan": "08",
    "uttar pradesh": "09", "up": "09",
    "bihar": "10",
    "sikkim": "11",
    "arunachal pradesh": "12",
    "nagaland": "13",
    "manipur": "14",
    "mizoram": "15",
    "tripura": "16",
    "meghalaya": "17",
    "assam": "18",
    "west bengal": "19",
    "jharkhand": "20",
    "odisha": "21", "orissa": "21",
    "chhattisgarh": "22",
    "madhya pradesh": "23",
    "gujarat": "24",
    "maharashtra": "27",
    "karnataka": "29",
    "goa": "30",
    "kerala": "32",
    "tamil nadu": "33",
    "puducherry": "34",
    "telangana": "36",
    "andhra pradesh": "37",
    "ladakh": "38",
}


def num(v):
    return pd.to_numeric(v, errors="coerce").fillna(0)


def clean_cols(df):
    df = df.copy()
    df.columns = [
        str(c).strip().lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        for c in df.columns
    ]
    return df


def state_to_code(v):
    if pd.isna(v):
        return None

    s = str(v).strip().lower()
    s = " ".join(s.split())

    if s.isdigit() and len(s) == 2:
        return s

    return STATE_CODES.get(s)


def first_match(columns, keywords):
    for c in columns:
        for k in keywords:
            if k in c:
                return c
    return None


def safe_docs(series):
    vals = (
        series.dropna()
        .astype(str)
        .str.strip()
    )
    vals = vals[vals != ""].unique().tolist()
    vals = sorted(vals)

    if not vals:
        return []

    return [{
        "from": vals[0],
        "to": vals[-1],
        "totnum": len(vals)
    }]


def remove_duplicates(df):
    keys = [c for c in ["platform", "invoice_no", "order_id", "txn_type"] if c in df.columns]
    if not keys:
        return df
    return df.drop_duplicates(subset=keys, keep="first")


def summarize(df):
    if df.empty:
        return {
            "rows": [],
            "total_taxable": 0,
            "total_igst": 0,
            "total_cgst": 0,
            "total_sgst": 0
        }

    df = df[df["pos"].notna()].copy()

    g = (
        df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ]
        .sum()
        .round(2)
    )

    return {
        "rows": g.to_dict("records"),
        "total_taxable": float(g["taxable_value"].sum()),
        "total_igst": float(g["igst"].sum()),
        "total_cgst": float(g["cgst"].sum()),
        "total_sgst": float(g["sgst"].sum())
    }
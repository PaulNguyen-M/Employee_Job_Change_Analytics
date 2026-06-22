"""
Xu ly du lieu cho bai toan du doan nhan vien co y dinh doi viec hay khong.

File nay lo phan:
- doc file csv goc
- lam sach du lieu (sua loi Oct-49, tach so nam kinh nghiem...)
- tao pipeline tien xu ly (dien thieu + scale + encode) dung chung cho cac model
- chia train/test

Chay truc tiep file nay (python ml/data_preprocessing.py) thi no se in thong tin
du lieu va xuat ra file da lam sach.

target = 1: dang muon doi viec
target = 0: khong muon doi viec
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

# duong dan tinh theo vi tri file nay, de chay o dau cung khong bi sai path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "dataset" / "aug_train.csv"
# Xuat ra Excel (.xlsx) da lam sach + lam giau them cot phuc vu dashboard
CLEAN_PATH = PROJECT_ROOT / "dataset" / "aug_train_cleaned.xlsx"

RANDOM_STATE = 42
TEST_SIZE = 0.20
TARGET = "target"

# thu tu cua cac cot dang co thu bac (de encode theo thu tu cho dung)
EDUCATION_ORDER = [
    "Primary School",
    "High School",
    "Graduate",
    "Masters",
    "Phd",
]
COMPANY_SIZE_ORDER = [
    "<10",
    "10-49",
    "50-99",
    "100-500",
    "500-999",
    "1000-4999",
    "5000-9999",
    "10000+",
]

# chia cot theo nhom de xu ly cho tien
NUMERIC_FEATURES = [
    "city_development_index",
    "training_hours",
    "experience",       # da doi sang so o ham clean_data
    "last_new_job",     # da doi sang so o ham clean_data
]
ORDINAL_FEATURES = {
    "education_level": EDUCATION_ORDER,
    "company_size": COMPANY_SIZE_ORDER,
}
NOMINAL_FEATURES = [
    "gender",
    "relevent_experience",
    "enrolled_university",
    "major_discipline",
    "company_type",
    "city",
]

UNKNOWN = "Unknown"

# Cac dac trung duoc tao them o buoc Feature Engineering (Muc 3 - toi uu hoa).
# Tat ca deu KHONG dung den cot target nen khong gay ro ri du lieu (data leakage).
ENGINEERED_FEATURES = [
    "training_per_exp",     # so gio dao tao tren moi nam kinh nghiem
    "exp_minus_lastjob",    # so nam kinh nghiem tru di so nam ke tu lan doi viec gan nhat
    "cdi_x_training",       # tuong tac giua chi so phat trien do thi va gio dao tao
]


def load_raw(path=RAW_PATH):
    """Doc file csv goc."""
    return pd.read_csv(path)


def _parse_experience(value):
    # cot experience co gia tri kieu '>20', '<1' nen phai doi tay sang so
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if value == ">20":
        return 21.0
    if value == "<1":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return np.nan


def _parse_last_new_job(value):
    # tuong tu experience: 'never' = 0, '>4' coi nhu 5
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if value == "never":
        return 0.0
    if value == ">4":
        return 5.0
    try:
        return float(value)
    except ValueError:
        return np.nan


def clean_data(df):
    """Lam sach du lieu (chi lam may buoc don gian, khong dung thong ke
    cua tap du lieu de tranh anh huong ket qua sau nay)."""
    df = df.copy()

    # bo dong trung neu co
    df = df.drop_duplicates()

    # luc import excel no tu nhan dien "10-49" thanh ngay "Oct-49", sua lai
    df["company_size"] = df["company_size"].replace({"Oct-49": "10-49"})

    # bo khoang trang thua, o nao rong thi coi nhu thieu (NaN)
    obj_cols = df.select_dtypes(exclude="number").columns
    df[obj_cols] = df[obj_cols].apply(lambda s: s.str.strip())
    df = df.replace({"": np.nan})

    # doi 2 cot dang chu sang so
    df["experience"] = df["experience"].apply(_parse_experience)
    df["last_new_job"] = df["last_new_job"].apply(_parse_last_new_job)

    return df


# ---------------------------------------------------------------------------
# Lam giau du lieu cho DASHBOARD (Power BI): them cot nhan + cot phan nhom.
# Day la cac thuoc tinh bi THIEU trong file goc nhung dashboard rat can de
# loc va ve bieu do (file goc chi co gia tri tho 0/1, so nam le...).
# ---------------------------------------------------------------------------
def _bucket_experience(x):
    if pd.isna(x):
        return "Khong ro"
    if x <= 2:
        return "0-2 nam"
    if x <= 5:
        return "3-5 nam"
    if x <= 10:
        return "6-10 nam"
    if x <= 15:
        return "11-15 nam"
    if x <= 20:
        return "16-20 nam"
    return ">20 nam"


def _bucket_training(x):
    if pd.isna(x):
        return "Khong ro"
    if x <= 25:
        return "0-25h"
    if x <= 50:
        return "26-50h"
    if x <= 100:
        return "51-100h"
    if x <= 200:
        return "101-200h"
    return ">200h"


def _bucket_cdi(x):
    if pd.isna(x):
        return "Khong ro"
    if x < 0.70:
        return "Thap (<0.70)"
    if x < 0.90:
        return "Trung binh (0.70-0.90)"
    return "Cao (>=0.90)"


def _bucket_last_new_job(x):
    if pd.isna(x):
        return "Khong ro"
    if x == 0:
        return "Chua tung"
    if x == 1:
        return "1 nam"
    if x <= 3:
        return "2-3 nam"
    if x == 4:
        return "4 nam"
    return ">4 nam"


# cac cot phan loai se dien "Unknown" cho o thieu de slicer khong bi o trong
CATEGORICAL_FILL = [
    "gender", "enrolled_university", "education_level",
    "major_discipline", "company_size", "company_type",
]


def enrich_for_dashboard(df):
    """Them cot nhan/nhom phuc vu dashboard. Khong dung cho phan train model,
    chi de xuat file Excel va ve Power BI."""
    df = df.copy()

    # nhan de doc thay cho gia tri 0/1, *_label
    df["target_label"] = df[TARGET].map({0: "O lai", 1: "Doi viec"})

    # cac cot phan nhom (bucket)
    df["experience_group"] = df["experience"].apply(_bucket_experience)
    df["training_group"] = df["training_hours"].apply(_bucket_training)
    df["cdi_group"] = df["city_development_index"].apply(_bucket_cdi)
    df["last_new_job_group"] = df["last_new_job"].apply(_bucket_last_new_job)

    # dien Unknown cho o phan loai con thieu
    for c in CATEGORICAL_FILL:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown")

    return df


def add_engineered_features(df):
    """Feature Engineering: tao them vai dac trung moi tu cac cot san co.
    Cac cong thuc nay khong dung target nen an toan, NaN se duoc imputer xu ly
    trong pipeline (chi fit tren tap train -> khong ro ri du lieu)."""
    df = df.copy()
    df["training_per_exp"] = df["training_hours"] / (df["experience"] + 1)
    df["exp_minus_lastjob"] = df["experience"] - df["last_new_job"]
    df["cdi_x_training"] = df["city_development_index"] * df["training_hours"]
    return df


def build_preprocessor(numeric_features=None):
    """Tao pipeline tien xu ly.
    - cot so: dien gia tri thieu bang trung vi roi chuan hoa
    - cot co thu bac: dien bang gia tri hay gap roi encode theo thu tu
    - cot phan loai: dien 'Unknown' roi one-hot
    Gom chung vao model luon nen file pkl luu ra dung duoc ngay.

    numeric_features: cho phep truyen them danh sach cot so (vi du khi da
    bat Feature Engineering). Mac dinh dung NUMERIC_FEATURES goc.
    """
    if numeric_features is None:
        numeric_features = NUMERIC_FEATURES

    numeric_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )

    ordinal_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "encode",
                OrdinalEncoder(
                    categories=[ORDINAL_FEATURES[c] for c in ORDINAL_FEATURES],
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
            ),
        ]
    )

    nominal_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="constant", fill_value=UNKNOWN)),
            # min_frequency de gom may gia tri qua hiem lai, tranh qua nhieu cot
            # sparse_output=False de dau ra la mang dac (dense): Naive Bayes
            # va PCA deu yeu cau dau vao dac, du lieu nho nen khong ton bo nho
            ("encode", OneHotEncoder(handle_unknown="ignore", min_frequency=20,
                                     sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_features),
            ("ord", ordinal_pipe, list(ORDINAL_FEATURES.keys())),
            ("nom", nominal_pipe, NOMINAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def get_feature_frame(df, use_engineered=False):
    """Tach ra X (cac cot dung de hoc) va y (cot can du doan).
    use_engineered=True se them cac dac trung Feature Engineering."""
    numeric = list(NUMERIC_FEATURES)
    if use_engineered:
        df = add_engineered_features(df)
        numeric = numeric + ENGINEERED_FEATURES
    feature_cols = numeric + list(ORDINAL_FEATURES.keys()) + NOMINAL_FEATURES
    X = df[feature_cols].copy()
    y = df[TARGET].astype(int)
    return X, y


def get_train_test_split(test_size=TEST_SIZE, random_state=RANDOM_STATE,
                         use_engineered=False):
    """Ham nay cac file model goi vao de lay san train/test (da lam sach,
    chua encode vi encode nam trong pipeline cua tung model)."""
    df = clean_data(load_raw())
    X, y = get_feature_frame(df, use_engineered=use_engineered)
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,  # giu nguyen ti le 75/25 o ca 2 tap
    )


def get_train_val_test_split(val_size=0.20, test_size=0.20,
                             random_state=RANDOM_STATE, use_engineered=False):
    """Chia 3 tap Train / Validation / Test theo yeu cau Muc 1.
    Mac dinh: 60% train, 20% validation, 20% test (deu stratify giu ti le lop).

    Cach lam: tach test truoc (20%), phan con lai (80%) tach tiep ra
    validation sao cho validation chiem 20% tong the (= 0.25 cua phan 80%).
    """
    df = clean_data(load_raw())
    X, y = get_feature_frame(df, use_engineered=use_engineered)

    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    # ti le validation tinh lai tren phan con lai
    val_ratio = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio,
        random_state=random_state, stratify=y_temp
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def profile(df):
    """Tom tat nhanh tinh trang du lieu tung cot (thieu bao nhieu, bao nhieu gia tri...)."""
    summary = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "n_missing": df.isna().sum(),
            "pct_missing": (df.isna().mean() * 100).round(2),
            "n_unique": df.nunique(dropna=True),
        }
    )
    return summary.sort_values("pct_missing", ascending=False)


def main():
    raw = load_raw()
    print(f"Du lieu goc: {raw.shape[0]} dong, {raw.shape[1]} cot")
    print("\nTinh trang thieu du lieu tung cot:")
    print(profile(raw).to_string())

    clean = clean_data(raw)
    print("\nTi le target (0 = o lai, 1 = doi viec):")
    print(clean[TARGET].value_counts(normalize=True).round(4).to_string())

    # lam giau them cot phuc vu dashboard roi luu ra Excel
    enriched = enrich_for_dashboard(clean)
    enriched.to_excel(CLEAN_PATH, index=False, sheet_name="aug_train_cleaned")
    print(f"\nDa luu file sach (Excel): {CLEAN_PATH} "
          f"({enriched.shape[0]} dong, {enriched.shape[1]} cot)")
    print("Cot them cho dashboard:", ", ".join(
        ["target_label", "experience_group", "training_group",
         "cdi_group", "last_new_job_group"]))

    # thu chay pipeline cho chac chan no khong loi
    X, y = get_feature_frame(clean)
    n_features = build_preprocessor().fit_transform(X).shape[1]
    print(f"Sau khi xu ly co {n_features} cot dac trung.")


if __name__ == "__main__":
    main()

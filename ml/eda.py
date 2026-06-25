"""
Phan tich kham pha du lieu (EDA): thong ke mo ta + truc quan hoa.
Chay: python ml/eda.py
Ket qua:
- In thong ke mo ta ra console
- Luu cac bieu do vao report/figures/
- Luu bang thong ke mo ta vao ml/eda_summary.json (de dua vao bao cao Word)
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # khong can man hinh, chi xuat file anh
import matplotlib.pyplot as plt
import seaborn as sns

from data_preprocessing import (
    NUMERIC_FEATURES,
    TARGET,
    clean_data,
    load_raw,
    profile,
)
from utils import FIGURES_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sns.set_theme(style="whitegrid")


def describe_numeric(df):
    """Thong ke mo ta cho cac cot so."""
    return df[NUMERIC_FEATURES].describe().T


def plot_target_distribution(df):
    counts = df[TARGET].value_counts().sort_index()
    plt.figure(figsize=(5, 4))
    ax = sns.barplot(x=["0 - O lai", "1 - Doi viec"], y=counts.values,
                     palette=["#4C72B0", "#DD8452"])
    for i, v in enumerate(counts.values):
        ax.text(i, v + 100, f"{v}\n({v / len(df) * 100:.1f}%)",
                ha="center", fontsize=10)
    plt.title("Phan bo bien muc tieu (target)")
    plt.ylabel("So luong")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "target_distribution.png", dpi=120)
    plt.close()


def plot_numeric_distributions(df):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, col in zip(axes.ravel(), NUMERIC_FEATURES):
        sns.histplot(data=df, x=col, hue=TARGET, kde=True, ax=ax,
                     palette=["#4C72B0", "#DD8452"], bins=30)
        ax.set_title(f"Phan bo {col} theo target")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "numeric_distributions.png", dpi=120)
    plt.close()


def plot_target_rate_by_category(df):
    """Ti le doi viec theo mot so nhom phan loai quan trong."""
    cat_cols = ["relevent_experience", "enrolled_university", "education_level"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, col in zip(axes, cat_cols):
        rate = df.groupby(col)[TARGET].mean().sort_values(ascending=False)
        sns.barplot(x=rate.values, y=rate.index, ax=ax, palette="viridis")
        ax.axvline(df[TARGET].mean(), color="red", ls="--", lw=1,
                   label=f"TB chung {df[TARGET].mean():.2f}")
        ax.set_title(f"Ti le doi viec theo\n{col}")
        ax.set_xlabel("Ti le target=1")
        ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "target_rate_by_category.png", dpi=120)
    plt.close()


def plot_correlation(df):
    num = df[NUMERIC_FEATURES + [TARGET]].corr()
    plt.figure(figsize=(6, 5))
    sns.heatmap(num, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Ma tran tuong quan (cac bien so + target)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "correlation_heatmap.png", dpi=120)
    plt.close()


def main():
    raw = load_raw()
    df = clean_data(raw)

    print("=== KICH THUOC DU LIEU ===")
    print(f"{df.shape[0]} dong, {df.shape[1]} cot\n")

    print("=== TINH TRANG THIEU DU LIEU ===")
    prof = profile(df)
    print(prof.to_string())

    print("\n=== THONG KE MO TA CAC BIEN SO ===")
    num_desc = describe_numeric(df)
    print(num_desc.round(2).to_string())

    print("\n=== TI LE TARGET ===")
    target_rate = df[TARGET].value_counts(normalize=True).round(4)
    print(target_rate.to_string())

    # ve bieu do
    plot_target_distribution(df)
    plot_numeric_distributions(df)
    plot_target_rate_by_category(df)
    plot_correlation(df)
    print(f"\nDa luu cac bieu do EDA vao {FIGURES_DIR}")

    # luu thong ke ra json de dung trong bao cao
    summary = {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "target_rate": {str(k): float(v) for k, v in target_rate.items()},
        "missing": {
            col: {"pct_missing": float(prof.loc[col, "pct_missing"]),
                  "n_unique": int(prof.loc[col, "n_unique"])}
            for col in prof.index
        },
        "numeric_describe": num_desc.round(4).to_dict(orient="index"),
    }
    out = PROJECT_ROOT / "ml" / "eda_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"Da luu thong ke mo ta: {out}")


if __name__ == "__main__":
    main()

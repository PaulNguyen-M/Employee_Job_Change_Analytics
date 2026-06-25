"""
Huan luyen, so sanh va toi uu hoa cac mo hinh hoc may cho bai toan
du doan nhan vien co y dinh doi viec (phan lop nhi phan, du lieu mat can bang ~75/25).

Bao phu day du 3 muc yeu cau:
- MUC 1 (Co ban): >= 3 mo hinh co so (LR, Decision Tree, KNN, Naive Bayes, SVM).
- MUC 2 (So sanh): >= 5 mo hinh (them Random Forest, Gradient Boosting, AdaBoost,
  XGBoost, LightGBM) -> bang + bieu do.
- MUC 3 (Toi uu): 5 ky thuat -> Feature Engineering, Xu ly mat can bang (SMOTE +
  Class Weight), Hyperparameter Tuning, PCA, Ensemble Learning.

Danh gia: Accuracy, Precision, Recall, F1, Specificity, ROC-AUC, Confusion Matrix.
Cross-Validation: Stratified K-Fold (k=5), bao cao Mean +/- Std.

Chay: python ml/train_models.py
Ket qua: ml/results.json + cac bieu do trong report/figures/ + model tot nhat trong ml/saved_models/
"""

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_validate,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from data_preprocessing import (
    ENGINEERED_FEATURES,
    NUMERIC_FEATURES,
    ORDINAL_FEATURES,
    RANDOM_STATE,
    build_preprocessor,
    get_train_val_test_split,
)
from utils import (
    FIGURES_DIR,
    evaluate,
    format_metrics_row,
    get_proba,
    save_model,
)

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ty le lop am/lop duong de can bang cho XGBoost/LightGBM
SCALE_POS_WEIGHT = 0.7507 / 0.2493  # ~3.01

# danh sach cot so khi da bat Feature Engineering
NUMERIC_WITH_ENG = NUMERIC_FEATURES + ENGINEERED_FEATURES


def make_pipeline(model, numeric_features=NUMERIC_WITH_ENG):
    """Gan buoc tien xu ly truoc moi mo hinh."""
    return Pipeline([
        ("prep", build_preprocessor(numeric_features)),
        ("model", model),
    ])


def get_models():
    """Tap mo hinh dung de so sanh (Muc 1 + Muc 2).
    Da bat san xu ly mat can bang bang Class Weight o nhung mo hinh ho tro."""
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8, class_weight="balanced", random_state=RANDOM_STATE),
        "KNN": KNeighborsClassifier(n_neighbors=25),
        "Naive Bayes": GaussianNB(),
        "SVM (RBF)": SVC(
            kernel="rbf", class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=12, class_weight="balanced",
            n_jobs=-1, random_state=RANDOM_STATE),
        "Gradient Boosting": GradientBoostingClassifier(
            random_state=RANDOM_STATE),
        "AdaBoost": AdaBoostClassifier(random_state=RANDOM_STATE),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.1,
            subsample=0.9, colsample_bytree=0.9,
            scale_pos_weight=SCALE_POS_WEIGHT, eval_metric="logloss",
            random_state=RANDOM_STATE, n_jobs=-1),
        "LightGBM": LGBMClassifier(
            n_estimators=300, max_depth=-1, learning_rate=0.05,
            class_weight="balanced", random_state=RANDOM_STATE,
            n_jobs=-1, verbose=-1),
    }


# ----------------------------------------------------------------------------
# MUC 1 + 2: huan luyen va so sanh nhieu mo hinh
# ----------------------------------------------------------------------------
def compare_models(X_train, y_train, X_val, y_val):
    print("\n" + "=" * 70)
    print("MUC 1 + 2: HUAN LUYEN & SO SANH CAC MO HINH (danh gia tren VALIDATION)")
    print("=" * 70)
    results = {}
    fitted = {}
    for name, model in get_models().items():
        pipe = make_pipeline(model)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_val)
        y_proba = get_proba(pipe, X_val)
        m = evaluate(y_val, y_pred, y_proba)
        results[name] = m
        fitted[name] = pipe
        print(format_metrics_row(name, m))
    return results, fitted


# ----------------------------------------------------------------------------
# Cross Validation (K-Fold, k=5) - bao cao Mean +/- Std
# ----------------------------------------------------------------------------
def run_cross_validation(X, y, k=5):
    print("\n" + "=" * 70)
    print(f"K-FOLD CROSS VALIDATION (k={k}) - Mean +/- Std tren tap Train+Val")
    print("=" * 70)
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=RANDOM_STATE)
    scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    cv_results = {}
    for name, model in get_models().items():
        pipe = make_pipeline(model)
        scores = cross_validate(pipe, X, y, cv=skf, scoring=scoring, n_jobs=-1)
        entry = {}
        for s in scoring:
            arr = scores[f"test_{s}"]
            entry[f"{s}_mean"] = float(arr.mean())
            entry[f"{s}_std"] = float(arr.std())
        cv_results[name] = entry
        print(f"{name:<22} ROC-AUC = {entry['roc_auc_mean']:.3f} "
              f"+/- {entry['roc_auc_std']:.3f}   "
              f"F1 = {entry['f1_mean']:.3f} +/- {entry['f1_std']:.3f}")
    return cv_results


# ----------------------------------------------------------------------------
# MUC 3: cac ky thuat toi uu hoa (danh gia tren VALIDATION)
# ----------------------------------------------------------------------------
def run_optimizations(X_train, y_train, X_val, y_val):
    print("\n" + "=" * 70)
    print("MUC 3: CAC KY THUAT TOI UU HOA (danh gia tren VALIDATION)")
    print("=" * 70)
    opt = {}
    extra = {}

    # --- (0) Mo hinh nen de doi chieu: XGBoost mac dinh ---
    base = make_pipeline(XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9,
        scale_pos_weight=SCALE_POS_WEIGHT, eval_metric="logloss",
        random_state=RANDOM_STATE, n_jobs=-1))
    base.fit(X_train, y_train)
    opt["Nen: XGBoost (FE + class weight)"] = evaluate(
        y_val, base.predict(X_val), get_proba(base, X_val))

    # --- (1) Xu ly mat can bang bang SMOTE (thay cho class weight) ---
    smote_pipe = ImbPipeline([
        ("prep", build_preprocessor(NUMERIC_WITH_ENG)),
        ("smote", SMOTE(random_state=RANDOM_STATE)),
        ("model", XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.1,
            subsample=0.9, colsample_bytree=0.9,
            eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1)),
    ])
    smote_pipe.fit(X_train, y_train)
    opt["(1) SMOTE oversampling"] = evaluate(
        y_val, smote_pipe.predict(X_val), get_proba(smote_pipe, X_val))

    # --- (2) PCA giam chieu (giu 95% phuong sai) ---
    pca = PCA(n_components=0.95, random_state=RANDOM_STATE)
    pca_pipe = Pipeline([
        ("prep", build_preprocessor(NUMERIC_WITH_ENG)),
        ("pca", pca),
        ("model", LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)),
    ])
    pca_pipe.fit(X_train, y_train)
    opt["(2) PCA(95%) + Logistic"] = evaluate(
        y_val, pca_pipe.predict(X_val), get_proba(pca_pipe, X_val))
    # bieu do phuong sai tich luy cua PCA
    fitted_pca = pca_pipe.named_steps["pca"]
    extra["pca_n_components"] = int(fitted_pca.n_components_)
    extra["pca_cumvar"] = np.cumsum(
        fitted_pca.explained_variance_ratio_).tolist()
    plot_pca_variance(extra["pca_cumvar"])

    # --- (3) Hyperparameter Tuning (RandomizedSearchCV cho XGBoost) ---
    param_dist = {
        "model__n_estimators": [200, 300, 400, 500],
        "model__max_depth": [3, 4, 5, 6],
        "model__learning_rate": [0.03, 0.05, 0.1, 0.15],
        "model__subsample": [0.7, 0.8, 0.9, 1.0],
        "model__colsample_bytree": [0.7, 0.8, 0.9, 1.0],
        "model__min_child_weight": [1, 3, 5],
    }
    search_pipe = make_pipeline(XGBClassifier(
        scale_pos_weight=SCALE_POS_WEIGHT, eval_metric="logloss",
        random_state=RANDOM_STATE, n_jobs=-1))
    search = RandomizedSearchCV(
        search_pipe, param_dist, n_iter=25, scoring="roc_auc",
        cv=3, random_state=RANDOM_STATE, n_jobs=-1)
    search.fit(X_train, y_train)
    tuned = search.best_estimator_
    opt["(3) XGBoost + Tuning"] = evaluate(
        y_val, tuned.predict(X_val), get_proba(tuned, X_val))
    extra["tuning_best_params"] = {
        k.replace("model__", ""): v for k, v in search.best_params_.items()}
    print("  -> Tham so tot nhat (Tuning):", extra["tuning_best_params"])

    # --- (4) Ensemble Learning: Stacking + Voting ---
    estimators = [
        ("xgb", XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.1,
            scale_pos_weight=SCALE_POS_WEIGHT, eval_metric="logloss",
            random_state=RANDOM_STATE, n_jobs=-1)),
        ("rf", RandomForestClassifier(
            n_estimators=300, max_depth=12, class_weight="balanced",
            n_jobs=-1, random_state=RANDOM_STATE)),
        ("lr", LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)),
    ]
    stack = Pipeline([
        ("prep", build_preprocessor(NUMERIC_WITH_ENG)),
        ("model", StackingClassifier(
            estimators=estimators,
            final_estimator=LogisticRegression(max_iter=2000),
            cv=3, n_jobs=-1)),
    ])
    stack.fit(X_train, y_train)
    opt["(4a) Stacking Ensemble"] = evaluate(
        y_val, stack.predict(X_val), get_proba(stack, X_val))

    vote = Pipeline([
        ("prep", build_preprocessor(NUMERIC_WITH_ENG)),
        ("model", VotingClassifier(estimators=estimators, voting="soft",
                                   n_jobs=-1)),
    ])
    vote.fit(X_train, y_train)
    opt["(4b) Voting Ensemble"] = evaluate(
        y_val, vote.predict(X_val), get_proba(vote, X_val))

    for name, m in opt.items():
        print(format_metrics_row(name, m))

    # giu lai cac pipeline da fit de chon ban tot nhat danh gia tren test
    fitted_opt = {
        "Nen: XGBoost (FE + class weight)": base,
        "(1) SMOTE oversampling": smote_pipe,
        "(2) PCA(95%) + Logistic": pca_pipe,
        "(3) XGBoost + Tuning": tuned,
        "(4a) Stacking Ensemble": stack,
        "(4b) Voting Ensemble": vote,
    }
    return opt, fitted_opt, extra


# ----------------------------------------------------------------------------
# Bieu do
# ----------------------------------------------------------------------------
def plot_model_comparison(results):
    metrics = ["accuracy", "precision", "recall", "f1", "specificity", "roc_auc"]
    names = list(results.keys())
    data = np.array([[results[n][m] for m in metrics] for n in names])
    x = np.arange(len(names))
    w = 0.13
    plt.figure(figsize=(14, 6))
    for i, m in enumerate(metrics):
        plt.bar(x + i * w, data[:, i], w, label=m)
    plt.xticks(x + w * 2.5, names, rotation=30, ha="right")
    plt.ylabel("Gia tri")
    plt.title("So sanh cac mo hinh (tap Validation)")
    plt.legend(ncol=6, fontsize=9)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_comparison.png", dpi=120)
    plt.close()


def plot_roc_curves(fitted, X_val, y_val):
    plt.figure(figsize=(8, 7))
    for name, pipe in fitted.items():
        proba = get_proba(pipe, X_val)
        if proba is None:
            continue
        from sklearn.metrics import roc_auc_score
        fpr, tpr, _ = roc_curve(y_val, proba)
        plt.plot(fpr, tpr, lw=1.6,
                 label=f"{name} (AUC={roc_auc_score(y_val, proba):.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1)
    plt.xlabel("False Positive Rate (1 - Specificity)")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title("Duong cong ROC cac mo hinh (Validation)")
    plt.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "roc_curves.png", dpi=120)
    plt.close()


def plot_confusion_matrices(fitted, X_val, y_val, top_names):
    n = len(top_names)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4.2))
    if n == 1:
        axes = [axes]
    for ax, name in zip(axes, top_names):
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_val, fitted[name].predict(X_val), labels=[0, 1])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Du doan 0", "Du doan 1"],
                    yticklabels=["That 0", "That 1"])
        ax.set_title(name)
    plt.suptitle("Confusion Matrix (Validation)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "confusion_matrices.png", dpi=120)
    plt.close()


def plot_cv_results(cv_results):
    names = list(cv_results.keys())
    means = [cv_results[n]["roc_auc_mean"] for n in names]
    stds = [cv_results[n]["roc_auc_std"] for n in names]
    order = np.argsort(means)
    names = [names[i] for i in order]
    means = [means[i] for i in order]
    stds = [stds[i] for i in order]
    plt.figure(figsize=(9, 6))
    plt.barh(names, means, xerr=stds, capsize=4, color="#4C72B0")
    plt.xlabel("ROC-AUC (Mean +/- Std qua 5 fold)")
    plt.title("Cross-Validation: do on dinh ROC-AUC cua cac mo hinh")
    plt.xlim(0.5, 0.9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "cv_results.png", dpi=120)
    plt.close()


def plot_optimization_comparison(opt):
    names = list(opt.keys())
    metrics = ["f1", "recall", "roc_auc"]
    data = np.array([[opt[n][m] for m in metrics] for n in names])
    x = np.arange(len(names))
    w = 0.25
    plt.figure(figsize=(12, 6))
    for i, m in enumerate(metrics):
        plt.bar(x + i * w, data[:, i], w, label=m)
    plt.xticks(x + w, names, rotation=20, ha="right")
    plt.ylabel("Gia tri")
    plt.title("Muc 3: So sanh cac ky thuat toi uu hoa (Validation)")
    plt.legend()
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "optimization_comparison.png", dpi=120)
    plt.close()


def plot_pca_variance(cumvar):
    plt.figure(figsize=(7, 5))
    plt.plot(range(1, len(cumvar) + 1), cumvar, marker=".")
    plt.axhline(0.95, color="red", ls="--", label="Nguong 95%")
    plt.xlabel("So thanh phan chinh")
    plt.ylabel("Phuong sai tich luy")
    plt.title("PCA: phuong sai tich luy theo so thanh phan")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "pca_variance.png", dpi=120)
    plt.close()


def plot_final_confusion(y_test, y_pred, name):
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    plt.figure(figsize=(5, 4.2))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=["Du doan 0", "Du doan 1"],
                yticklabels=["That 0", "That 1"])
    plt.title(f"Confusion Matrix mo hinh cuoi cung\n{name} (tap TEST)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "final_confusion_matrix.png", dpi=120)
    plt.close()


# ----------------------------------------------------------------------------
def main():
    (X_train, X_val, X_test,
     y_train, y_val, y_test) = get_train_val_test_split(use_engineered=True)
    print(f"Chia du lieu -> Train: {len(X_train)} | "
          f"Validation: {len(X_val)} | Test: {len(X_test)}")
    print(f"So dac trung dau vao (truoc encode): {X_train.shape[1]} "
          f"(da gom {len(ENGINEERED_FEATURES)} dac trung Feature Engineering)")

    # MUC 1 + 2
    comp, fitted = compare_models(X_train, y_train, X_val, y_val)
    plot_model_comparison(comp)
    plot_roc_curves(fitted, X_val, y_val)
    top3 = sorted(comp, key=lambda n: comp[n]["roc_auc"], reverse=True)[:3]
    plot_confusion_matrices(fitted, X_val, y_val, top3)

    # Cross Validation tren Train+Val
    import pandas as pd
    X_tv = pd.concat([X_train, X_val])
    y_tv = pd.concat([y_train, y_val])
    cv_results = run_cross_validation(X_tv, y_tv, k=5)
    plot_cv_results(cv_results)

    # MUC 3
    opt, fitted_opt, extra = run_optimizations(X_train, y_train, X_val, y_val)
    plot_optimization_comparison(opt)

    # ---- Chon mo hinh tot nhat (theo ROC-AUC tren validation, gop ca baseline va optimized) ----
    all_val = {**comp, **opt}
    best_name = max(all_val, key=lambda n: all_val[n]["roc_auc"])
    best_pipe = {**fitted, **fitted_opt}[best_name]
    print(f"\n>>> Mo hinh tot nhat tren Validation: {best_name} "
          f"(ROC-AUC={all_val[best_name]['roc_auc']:.3f})")

    # ---- Danh gia LAN CUOI tren tap TEST (chua he dung den) ----
    print("\n" + "=" * 70)
    print(f"DANH GIA CUOI CUNG TREN TAP TEST: {best_name}")
    print("=" * 70)
    y_pred = best_pipe.predict(X_test)
    final = evaluate(y_test, y_pred, get_proba(best_pipe, X_test))
    print(format_metrics_row(best_name, final))
    plot_final_confusion(y_test, y_pred, best_name)
    save_model(best_pipe, "best_model")

    # ---- Luu tat ca ket qua ----
    results = {
        "split": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
        "n_input_features": int(X_train.shape[1]),
        "comparison_val": comp,
        "cv": cv_results,
        "optimization_val": opt,
        "best_model": best_name,
        "best_val_metrics": all_val[best_name],
        "final_test": final,
        "extra": extra,
    }
    out = PROJECT_ROOT / "ml" / "results.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"\nDa luu ket qua: {out}")
    print(f"Da luu mo hinh tot nhat: ml/saved_models/best_model.pkl")


if __name__ == "__main__":
    main()

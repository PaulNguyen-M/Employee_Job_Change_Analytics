"""
Ham dung chung cho viec danh gia va luu/doc model.

Gom day du cac chi so theo yeu cau bai toan PHAN LOAI:
- Accuracy, Precision, Recall, F1-score
- Specificity (do dac hieu - ti le bat dung lop 0)
- ROC-AUC
- Confusion Matrix
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "report" / "figures"
MODELS_DIR = PROJECT_ROOT / "ml" / "saved_models"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def specificity_score(y_true, y_pred):
    """Specificity = TN / (TN + FP): trong so nguoi KHONG doi viec (lop 0),
    mo hinh bat dung bao nhieu phan tram."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0


def evaluate(y_true, y_pred, y_proba=None):
    """Tinh tat ca chi so cho mot lan du doan. Tra ve dict.
    y_proba la xac suat thuoc lop 1 (de tinh ROC-AUC)."""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "specificity": specificity_score(y_true, y_pred),
    }
    if y_proba is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_proba)
    else:
        metrics["roc_auc"] = float("nan")
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    metrics["confusion_matrix"] = {"tn": int(tn), "fp": int(fp),
                                   "fn": int(fn), "tp": int(tp)}
    return metrics


def get_proba(model, X):
    """Lay xac suat lop 1 cho ca model co predict_proba lan model chi co
    decision_function (vi du SVM)."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        # chuan hoa ve [0,1] de tinh ROC-AUC (ROC-AUC chi can thu tu nen ok)
        smin, smax = scores.min(), scores.max()
        return (scores - smin) / (smax - smin) if smax > smin else scores
    return None


def save_model(model, name):
    path = MODELS_DIR / f"{name}.pkl"
    joblib.dump(model, path)
    return path


def load_model(name):
    return joblib.load(MODELS_DIR / f"{name}.pkl")


def format_metrics_row(name, m):
    """In gon mot dong ket qua ra console."""
    return (f"{name:<22} acc={m['accuracy']:.3f}  prec={m['precision']:.3f}  "
            f"rec={m['recall']:.3f}  f1={m['f1']:.3f}  "
            f"spec={m['specificity']:.3f}  auc={m['roc_auc']:.3f}")

"""分析产物读写门面（API / Agent 共用）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from digital_marketing.core.paths import resolve_under_root
from digital_marketing.data.clean import add_quality_flags
from digital_marketing.features.schema import load_feature_config
from digital_marketing.models.classify import _predict_proba_positive


class ArtifactError(Exception):
    """产物缺失或无效。"""

    def __init__(self, code: str, message: str, detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}


def processed_dir() -> Path:
    return resolve_under_root("outputs/processed")


def metrics_dir() -> Path:
    return resolve_under_root("outputs/metrics")


def models_dir() -> Path:
    return resolve_under_root("outputs/models")


def explain_dir() -> Path:
    return resolve_under_root("outputs/explain")


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", f"缺少产物: {path.name}", {"path": str(path)})
    return json.loads(path.read_text(encoding="utf-8"))


def get_quality_profile() -> dict[str, Any]:
    return load_json(processed_dir() / "quality_profile.json")


def get_feature_schema() -> dict[str, Any]:
    return load_json(processed_dir() / "feature_schema.json")


def get_overview() -> dict[str, Any]:
    """总览：优先 quality_profile + clean_meta + splits。"""
    profile = get_quality_profile()
    meta_path = processed_dir() / "clean_meta.json"
    splits_path = processed_dir() / "splits.json"
    meta = load_json(meta_path) if meta_path.is_file() else {}
    splits = load_json(splits_path) if splits_path.is_file() else {}
    return {
        "n_rows": profile.get("n_rows") or meta.get("rows"),
        "n_columns": profile.get("n_columns"),
        "positive_rate": profile.get("positive_rate") or meta.get("positive_rate"),
        "issues": profile.get("issues") or [],
        "issue_count": len(profile.get("issues") or []),
        "channel_stats": profile.get("channel_stats") or [],
        "email_inconsistent_count": meta.get("email_inconsistent_count"),
        "invalid_web_metrics_count": meta.get("invalid_web_metrics_count"),
        "splits": {
            "n_train": splits.get("n_train"),
            "n_valid": splits.get("n_valid"),
            "n_test": splits.get("n_test"),
        }
        if splits
        else None,
        "notes": {
            "metrics_not_in_sqlite": True,
            "customer_id_never_in_model": True,
        },
    }


def list_metrics() -> list[dict[str, Any]]:
    board = metrics_dir() / "leaderboard.json"
    if board.is_file():
        return load_json(board)
    rows = []
    d = metrics_dir()
    if not d.is_dir():
        return []
    for p in sorted(d.glob("*.json")):
        if p.name == "leaderboard.json":
            continue
        rows.append(load_json(p))
    rows.sort(key=lambda r: (r.get("pr_auc") is not None, r.get("pr_auc") or 0), reverse=True)
    return rows


def get_metrics(run_id: str) -> dict[str, Any]:
    path = metrics_dir() / f"{run_id}.json"
    return load_json(path)


def pick_default_run_id() -> str:
    """选默认 run：非 Dummy 中 PR-AUC 最高；同分偏好 LightGBM/树模型。"""
    rows = list_metrics()
    if not rows:
        raise ArtifactError("MODEL_NOT_LOADED", "尚无训练 metrics，请运行 python scripts/02_train_classify.py")
    non_dummy = [r for r in rows if str(r.get("exp_id", "")).upper() != "E0"]
    pool = non_dummy or rows

    def _score(r: dict[str, Any]) -> tuple:
        pr = float(r.get("pr_auc") or 0)
        name = f"{r.get('model_name', '')} {r.get('run_id', '')} {r.get('exp_id', '')}".lower()
        # 近并列时偏好树模型（便于 pred_contrib / SHAP）
        tree_bonus = 1 if any(k in name for k in ("lightgbm", "lgbm", "forest", "e3")) else 0
        return (round(pr, 3), tree_bonus)

    best = max(pool, key=_score)
    run_id = best.get("run_id")
    if not run_id:
        raise ArtifactError("MODEL_NOT_LOADED", "leaderboard 无有效 run_id")
    return str(run_id)


def load_runtime(run_id: str | None = None) -> dict[str, Any]:
    """加载 model + transformer + meta。"""
    rid = run_id or pick_default_run_id()
    run_dir = models_dir() / rid
    meta_path = run_dir / "meta.json"
    model_path = run_dir / "model.joblib"
    if not meta_path.is_file() or not model_path.is_file():
        raise ArtifactError("MODEL_NOT_LOADED", f"模型未加载: {rid}", {"run_id": rid})
    meta = load_json(meta_path)
    model = joblib.load(model_path)
    schema = get_feature_schema()
    tr_path = Path(schema.get("transformer_path") or (processed_dir() / "feature_transformer.joblib"))
    if not tr_path.is_file():
        # meta 内可能有绝对路径
        tr_path = Path((meta.get("feature_schema") or {}).get("transformer_path", ""))
    if not tr_path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少 feature_transformer.joblib")
    transformer = joblib.load(tr_path)
    return {
        "run_id": rid,
        "model": model,
        "meta": meta,
        "transformer": transformer,
        "schema": schema,
        "feature_names": list(schema.get("feature_names_out") or []),
        "raw_feature_cols": list(schema.get("feature_columns_raw") or []),
    }


def _row_dataframe_from_features(features: dict[str, Any]) -> pd.DataFrame:
    """从 API 特征 dict 构造单行 DataFrame，并补 flag。"""
    cfg = load_feature_config()
    row = dict(features)
    # 若缺 flag 则按规则计算
    df = pd.DataFrame([row])
    if "email_inconsistent" not in df.columns or "invalid_web_metrics_flag" not in df.columns:
        # 需要邮件/访问列才能算
        need = ["EmailOpens", "EmailClicks", "WebsiteVisits", "PagesPerVisit", "TimeOnSite"]
        if all(c in df.columns for c in need):
            df = add_quality_flags(df)
        else:
            df["email_inconsistent"] = int(row.get("email_inconsistent", 0))
            df["invalid_web_metrics_flag"] = int(row.get("invalid_web_metrics_flag", 0))
    # 保证 schema 列存在
    for c in cfg.feature_columns():
        if c not in df.columns:
            df[c] = np.nan
    return df


def lookup_customer_row(customer_id: int) -> pd.DataFrame:
    clean = processed_dir() / "clean.csv"
    if not clean.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少 clean.csv，请先 python scripts/01_clean_data.py")
    df = pd.read_csv(clean)
    hit = df[df["CustomerID"] == customer_id]
    if hit.empty:
        raise ArtifactError("CUSTOMER_NOT_FOUND", f"未找到 CustomerID={customer_id}", {"customer_id": customer_id})
    return hit.iloc[[0]].copy()


def predict_row(
    *,
    customer_id: int | None = None,
    features: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    rt = load_runtime(run_id)
    if customer_id is not None:
        df = lookup_customer_row(customer_id)
    elif features:
        df = _row_dataframe_from_features(features)
    else:
        raise ArtifactError("VALIDATION_ERROR", "需要 customer_id 或 features")

    cols = rt["raw_feature_cols"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ArtifactError("VALIDATION_ERROR", f"特征缺列: {missing}", {"missing": missing})
    X = rt["transformer"].transform(df[cols])
    proba = float(_predict_proba_positive(rt["model"], X)[0])
    thr = float(rt["meta"].get("threshold", 0.5))
    label = int(proba >= thr)
    return {
        "proba": proba,
        "label": label,
        "threshold": thr,
        "run_id": rt["run_id"],
        "model_name": rt["meta"].get("model_name") or rt["run_id"],
        "customer_id": customer_id,
        "_X": X,
        "_df": df,
        "_runtime": rt,
    }


def explain_customer(
    *,
    customer_id: int | None = None,
    features: dict[str, Any] | None = None,
    run_id: str | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    from digital_marketing.explain.local_shap import compute_local_shap

    pred = predict_row(customer_id=customer_id, features=features, run_id=run_id)
    rt = pred["_runtime"]
    X = pred["_X"]
    # 背景：train 子集若存在
    bg = None
    train_path = processed_dir() / "train.csv"
    if train_path.is_file():
        train = pd.read_csv(train_path)
        cols = rt["raw_feature_cols"]
        n = min(80, len(train))
        bg = rt["transformer"].transform(train[cols].iloc[:n])
    names = rt["feature_names"]
    # 展开后特征值用变换矩阵
    local = compute_local_shap(
        rt["model"],
        X[0],
        names,
        feature_values=[float(v) for v in np.asarray(X[0]).reshape(-1)],
        background=bg,
        top_k=top_k,
    )
    return {
        "run_id": pred["run_id"],
        "model_name": pred["model_name"],
        "proba": pred["proba"],
        "label": pred["label"],
        "threshold": pred["threshold"],
        "customer_id": customer_id,
        "method": local["method"],
        "top_features": local["top_features"],
    }


def get_global_explain(run_id: str | None = None) -> dict[str, Any]:
    rid = run_id or pick_default_run_id()
    path = explain_dir() / f"global_{rid}.json"
    if path.is_file():
        data = load_json(path)
        data["run_id"] = rid
        return data
    raise ArtifactError(
        "ARTIFACT_MISSING",
        f"缺少全局 SHAP: global_{rid}.json，请运行 python scripts/03_explain_shap.py 或 run_all",
        {"run_id": rid},
    )


def meta_features() -> dict[str, Any]:
    schema = get_feature_schema()
    cfg = load_feature_config()
    return {
        "target": schema.get("target") or cfg.target,
        "feature_columns_raw": schema.get("feature_columns_raw") or cfg.feature_columns(),
        "feature_names_out": schema.get("feature_names_out") or [],
        "drop_features": schema.get("drop_features") or cfg.drop_features,
        "never_features": schema.get("never_features") or cfg.never_features,
        "categorical_features": cfg.categorical_features,
        "numeric_features": cfg.numeric_features,
        "flag_features": cfg.flag_features,
        "sample_defaults": {
            "Age": 35,
            "Gender": "Female",
            "Income": 50000,
            "CampaignChannel": "Email",
            "CampaignType": "Awareness",
            "AdSpend": 1000.0,
            "ClickThroughRate": 0.1,
            "WebsiteVisits": 5,
            "PagesPerVisit": 2.0,
            "TimeOnSite": 5.0,
            "SocialShares": 1,
            "EmailOpens": 3,
            "EmailClicks": 1,
            "PreviousPurchases": 1,
            "LoyaltyPoints": 100,
        },
    }

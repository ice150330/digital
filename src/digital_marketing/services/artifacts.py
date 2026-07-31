"""分析产物读写门面（API / Agent 共用）。"""

from __future__ import annotations

import json
from functools import lru_cache
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


def _is_ablation_run(r: dict[str, Any]) -> bool:
    """消融/泄漏实验 run（E5 含 ConversionRate、E6 去 flag 等）不参选默认 run。

    leaderboard 新行自带标记；旧产物回退读 run 目录 meta.json 判定。
    """
    if r.get("includes_conversion_rate") or r.get("ablation"):
        return True
    run_id = r.get("run_id")
    if not run_id:
        return False
    meta_path = models_dir() / str(run_id) / "meta.json"
    if not meta_path.is_file():
        return False
    try:
        meta = load_json(meta_path)
    except ArtifactError:
        return False
    if meta.get("includes_conversion_rate") or meta.get("ablation"):
        return True
    cols = (meta.get("feature_schema") or {}).get("feature_columns_raw") or []
    return "ConversionRate" in cols


def pick_default_run_id() -> str:
    """选默认 run：非 Dummy、非消融 run 中 PR-AUC 最高；同分偏好 LightGBM/树模型。"""
    rows = list_metrics()
    if not rows:
        raise ArtifactError("MODEL_NOT_LOADED", "尚无训练 metrics，请运行 python scripts/02_train_classify.py")
    non_dummy = [r for r in rows if str(r.get("exp_id", "")).upper() != "E0"]
    eligible = [r for r in non_dummy if not _is_ablation_run(r)]
    pool = eligible or non_dummy or rows

    def _score(r: dict[str, Any]) -> tuple:
        pr = float(r.get("pr_auc") or 0)
        name = f"{r.get('model_name', '')} {r.get('run_id', '')} {r.get('exp_id', '')}".lower()
        # 近并列（0.01 窗口，差异远在 bootstrap CI 内）时偏好纯树模型（便于 pred_contrib / SHAP）；
        # stacking 含 lgbm 基学习器但不是纯树，不享解释友好加成
        tree_bonus = (
            1
            if ("stacking" not in name and any(k in name for k in ("lightgbm", "lgbm", "forest")))
            else 0
        )
        return (round(pr, 2), tree_bonus, pr)

    best = max(pool, key=_score)
    run_id = best.get("run_id")
    if not run_id:
        raise ArtifactError("MODEL_NOT_LOADED", "leaderboard 无有效 run_id")
    return str(run_id)


def load_runtime(run_id: str | None = None) -> dict[str, Any]:
    """加载 model + transformer + meta（Stage 1：按 run_id 进程内缓存）。

    transformer 解析顺序：run 目录 per-run transformer（E5/E6 等特征变体）
    → 全局 processed/feature_transformer.joblib → meta 内快照路径。
    特征列/展开名以 meta.feature_schema 快照为准（变体 run 列集合不同）。

    返回 dict 为共享只读引用（调用方不得 mutate）；重训后同进程须
    clear_runtime_cache()。predict_batch 等热路径不再重复 joblib.load。
    """
    rid = run_id or pick_default_run_id()
    # 缓存键含产物根路径：测试会 monkeypatch 目录函数，路径入键防跨根污染
    return _load_runtime_cached(str(models_dir()), rid)


@lru_cache(maxsize=8)
def _load_runtime_cached(models_root: str, rid: str) -> dict[str, Any]:
    run_dir = Path(models_root) / rid
    meta_path = run_dir / "meta.json"
    model_path = run_dir / "model.joblib"
    if not meta_path.is_file() or not model_path.is_file():
        raise ArtifactError("MODEL_NOT_LOADED", f"模型未加载: {rid}", {"run_id": rid})
    meta = load_json(meta_path)
    model = joblib.load(model_path)
    schema = get_feature_schema()
    meta_schema = meta.get("feature_schema") or {}

    run_tr_path = run_dir / "transformer.joblib"
    if run_tr_path.is_file():
        transformer = joblib.load(run_tr_path)
    else:
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
        "feature_names": list(meta_schema.get("feature_names_out") or schema.get("feature_names_out") or []),
        "raw_feature_cols": list(
            meta_schema.get("feature_columns_raw") or schema.get("feature_columns_raw") or []
        ),
    }


def clear_runtime_cache() -> None:
    """清空模型运行时缓存（训练脚本结尾 / 测试重训场景调用）。"""
    _load_runtime_cached.cache_clear()
    _clean_df_cached.cache_clear()


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


@lru_cache(maxsize=4)
def _clean_df_cached(clean_path: str) -> pd.DataFrame:
    """clean.csv 只读全表缓存（8k 行，供 lookup_customer_row 复用）。

    键为解析后的文件路径：测试会 monkeypatch processed_dir，路径入键防跨根污染。
    """
    return pd.read_csv(Path(clean_path))


def lookup_customer_row(customer_id: int) -> pd.DataFrame:
    clean = processed_dir() / "clean.csv"
    if not clean.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少 clean.csv，请先 python scripts/01_clean_data.py")
    df = _clean_df_cached(str(clean))
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


# 批量预测条数上限（防止误用扫全库）
BATCH_PREDICT_MAX = 200


def predict_batch(
    *,
    customer_ids: list[int] | None = None,
    rows: list[dict[str, Any]] | None = None,
    run_id: str | None = None,
    max_items: int = BATCH_PREDICT_MAX,
) -> dict[str, Any]:
    """批量预测：customer_ids 或 features 行列表，超限报错。"""
    items_in: list[tuple[int | None, dict[str, Any] | None]] = []
    if customer_ids:
        items_in.extend((int(cid), None) for cid in customer_ids)
    if rows:
        for r in rows:
            if "customer_id" in r and len(r) == 1:
                items_in.append((int(r["customer_id"]), None))
            else:
                cid = r.get("customer_id")
                feats = {k: v for k, v in r.items() if k != "customer_id"}
                items_in.append((int(cid) if cid is not None else None, feats or None))
    if not items_in:
        raise ArtifactError("VALIDATION_ERROR", "需要 customer_ids 或 rows")
    if len(items_in) > max_items:
        raise ArtifactError(
            "VALIDATION_ERROR",
            f"批量条数超过上限 {max_items}，当前 {len(items_in)}",
            {"max_items": max_items, "n": len(items_in)},
        )

    rt = load_runtime(run_id)
    thr = float(rt["meta"].get("threshold", 0.5))
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for cid, feats in items_in:
        try:
            raw = predict_row(customer_id=cid, features=feats, run_id=rt["run_id"])
            results.append(
                {
                    "proba": raw["proba"],
                    "label": raw["label"],
                    "threshold": thr,
                    "run_id": raw["run_id"],
                    "model_name": raw["model_name"],
                    "customer_id": raw.get("customer_id") if raw.get("customer_id") is not None else cid,
                }
            )
        except ArtifactError as e:
            errors.append({"customer_id": cid, "code": e.code, "message": e.message})
    return {
        "run_id": rt["run_id"],
        "model_name": rt["meta"].get("model_name") or rt["run_id"],
        "threshold": thr,
        "n_requested": len(items_in),
        "n_ok": len(results),
        "n_error": len(errors),
        "items": results,
        "errors": errors,
        "max_items": max_items,
        "note": "批量预测仅供名单筛选参考，非因果 uplift",
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


# ---------------------------------------------------------------------------
# 阶段9：增强评估 / 高级解释 / 模拟器门面
# ---------------------------------------------------------------------------


def _resolve_run_id(run_id: str | None) -> str:
    return run_id or pick_default_run_id()


def get_curves(run_id: str | None = None) -> dict[str, Any]:
    """PR/ROC 曲线点 + bootstrap CI（来自 metrics 产物）。"""
    rid = _resolve_run_id(run_id)
    m = get_metrics(rid)
    if "pr_curve" not in m or "roc_curve" not in m:
        raise ArtifactError(
            "ARTIFACT_MISSING",
            f"run {rid} 缺少曲线产物，请运行 python scripts/06_train_full.py",
            {"run_id": rid},
        )
    return {
        "run_id": rid,
        "pr_auc": m.get("pr_auc"),
        "roc_auc": m.get("roc_auc"),
        "ci": m.get("ci") or {},
        "cv": m.get("cv") or {},
        "pr_curve": m["pr_curve"],
        "roc_curve": m["roc_curve"],
    }


def get_calibration(run_id: str | None = None) -> dict[str, Any]:
    """校准前后对比（calibration_<run_id>.json 产物）。"""
    rid = _resolve_run_id(run_id)
    path = metrics_dir() / f"calibration_{rid}.json"
    if not path.is_file():
        raise ArtifactError(
            "ARTIFACT_MISSING",
            f"缺少校准产物 calibration_{rid}.json（仅 calibrate 实验产生，如 E8）",
            {"run_id": rid},
        )
    return load_json(path)


def get_lift(run_id: str | None = None) -> dict[str, Any]:
    rid = _resolve_run_id(run_id)
    m = get_metrics(rid)
    if "lift_deciles" not in m:
        raise ArtifactError(
            "ARTIFACT_MISSING",
            f"run {rid} 缺少 lift 产物，请运行 python scripts/06_train_full.py",
            {"run_id": rid},
        )
    return {
        "run_id": rid,
        "lift_deciles": m["lift_deciles"],
        "note": "按预测概率降序十分位；capture_rate 为累计正类捕获率，lift 为相对全量基准的倍数",
    }


def get_threshold_scan(run_id: str | None = None) -> dict[str, Any]:
    rid = _resolve_run_id(run_id)
    m = get_metrics(rid)
    if "threshold_scan" not in m:
        raise ArtifactError(
            "ARTIFACT_MISSING",
            f"run {rid} 缺少阈值扫描产物，请运行 python scripts/06_train_full.py",
            {"run_id": rid},
        )
    scan = dict(m["threshold_scan"])
    scan["run_id"] = rid
    scan["current_threshold"] = m.get("threshold")
    return scan


def get_pdp(run_id: str | None = None, feature: str | None = None) -> dict[str, Any]:
    """PDP/ICE 产物；feature 指定则只返回单特征。"""
    rid = _resolve_run_id(run_id)
    path = explain_dir() / f"pdp_{rid}.json"
    if not path.is_file():
        raise ArtifactError(
            "ARTIFACT_MISSING",
            f"缺少 PDP 产物 pdp_{rid}.json，请运行 python scripts/07_explain_advanced.py",
            {"run_id": rid},
        )
    bundle = load_json(path)
    if feature:
        item = (bundle.get("features") or {}).get(feature)
        if item is None:
            raise ArtifactError(
                "VALIDATION_ERROR",
                f"PDP 不含特征 {feature}；可选: {list((bundle.get('features') or {}).keys())}",
                {"feature": feature},
            )
        return {"run_id": rid, **item}
    return bundle


def counterfactual_customer(
    *,
    customer_id: int | None = None,
    features: dict[str, Any] | None = None,
    feature: str | None = None,
    target_proba: float | None = None,
    run_id: str | None = None,
    grid_size: int = 25,
    max_steps: int = 8,
) -> dict[str, Any]:
    """反事实（模型行为口径）：单特征扰动曲线 + 可选贪心达标路径。"""
    from digital_marketing.explain.counterfactual import (
        greedy_counterfactual,
        single_feature_curve,
    )

    rt = load_runtime(run_id)
    if customer_id is not None:
        df = lookup_customer_row(customer_id)
    elif features:
        df = _row_dataframe_from_features(features)
    else:
        raise ArtifactError("VALIDATION_ERROR", "需要 customer_id 或 features")
    raw_cols = rt["raw_feature_cols"]
    missing = [c for c in raw_cols if c not in df.columns]
    if missing:
        raise ArtifactError("VALIDATION_ERROR", f"特征缺列: {missing}", {"missing": missing})

    out: dict[str, Any] = {"run_id": rt["run_id"], "customer_id": customer_id}
    if feature:
        out["curve"] = single_feature_curve(
            rt["model"], rt["transformer"], df, raw_cols, feature, grid_size=grid_size
        )
    if target_proba is not None:
        cfg = load_feature_config()
        numeric = [c for c in cfg.numeric_features if c in raw_cols]
        out["counterfactual"] = greedy_counterfactual(
            rt["model"],
            rt["transformer"],
            df,
            raw_cols,
            numeric,
            target_proba=float(target_proba),
            max_steps=max_steps,
        )
    if not feature and target_proba is None:
        raise ArtifactError("VALIDATION_ERROR", "需要 feature 或 target_proba 之一")
    return out


def simulate_budget(
    *,
    budget: float | None = None,
    value_per_conversion: float = 10.0,
    cost_per_contact: float = 4.0,
    run_id: str | None = None,
    export: bool = False,
    n_points: int = 25,
) -> dict[str, Any]:
    """预算分配模拟（test 集现算）：期望价值排序 + K 扫描曲线。"""
    from digital_marketing.models.classify import _predict_proba_positive
    from digital_marketing.simulate.budget import expected_value_curve, reach_list

    rt = load_runtime(run_id)
    test_path = processed_dir() / "test.csv"
    if not test_path.is_file():
        raise ArtifactError("ARTIFACT_MISSING", "缺少 test.csv，请先 python scripts/01_clean_data.py")
    test = pd.read_csv(test_path)
    X = rt["transformer"].transform(test[rt["raw_feature_cols"]])
    proba = _predict_proba_positive(rt["model"], X)
    result = expected_value_curve(
        proba,
        value_per_conversion=value_per_conversion,
        cost_per_contact=cost_per_contact,
        budget=budget,
        n_points=n_points,
    )
    result["run_id"] = rt["run_id"]
    result["calibrated"] = bool(rt["meta"].get("calibrated"))
    # 内联 Top 名单预览（最多 50 条，供前端名单表；全量走 export CSV）
    preview_k = min(int(result.get("recommended_k") or 0), 50)
    if preview_k > 0:
        preview = reach_list(
            test,
            proba,
            k=preview_k,
            value_per_conversion=value_per_conversion,
            cost_per_contact=cost_per_contact,
        )
        result["top_list"] = preview.round(6).to_dict(orient="records")
    else:
        result["top_list"] = []
    if export and result.get("recommended_k"):
        names = reach_list(
            test,
            proba,
            k=int(result["recommended_k"]),
            value_per_conversion=value_per_conversion,
            cost_per_contact=cost_per_contact,
        )
        from digital_marketing.core.paths import ensure_dir

        out_dir = ensure_dir(resolve_under_root("outputs/simulate"))
        path = out_dir / f"reach_list_{rt['run_id']}.csv"
        names.to_csv(path, index=False)
        result["export_path"] = str(path)
    return result


def get_segments_compare() -> dict[str, Any]:
    path = resolve_under_root("outputs/segments") / "compare.json"
    if not path.is_file():
        raise ArtifactError(
            "ARTIFACT_MISSING",
            "缺少分群对比产物 compare.json，请运行 python scripts/09_cluster_compare.py",
        )
    return load_json(path)


def get_segments_projection() -> dict[str, Any]:
    compare = get_segments_compare()
    proj = compare.get("projection") or {}
    return {
        "method": proj.get("method", "pca"),
        "explained_variance": proj.get("explained_variance") or [],
        "n_points": proj.get("n_points") or 0,
        "points": proj.get("points") or [],
        "disclaimer": compare.get("disclaimer"),
    }

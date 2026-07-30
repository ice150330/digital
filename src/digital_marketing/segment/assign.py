"""单样本簇分配（阶段 6 完整实现前可报缺产物）。"""

from __future__ import annotations

from typing import Any

from digital_marketing.services.artifacts import ArtifactError
from digital_marketing.core.paths import resolve_under_root
from digital_marketing.services import artifacts


def assign_one(
    *,
    customer_id: int | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = resolve_under_root("outputs/segments/model.joblib")
    meta_path = resolve_under_root("outputs/segments/summary.json")
    if not path.is_file() or not meta_path.is_file():
        raise ArtifactError(
            "ARTIFACT_MISSING",
            "缺少分群模型，请运行 python scripts/04_train_cluster.py",
        )
    import joblib
    import numpy as np
    import pandas as pd

    from digital_marketing.segment.train import build_segment_matrix

    bundle = joblib.load(path)
    model = bundle["model"]
    cols = bundle["feature_columns"]
    if customer_id is not None:
        df = artifacts.lookup_customer_row(customer_id)
    elif features:
        df = pd.DataFrame([features])
    else:
        raise ArtifactError("VALIDATION_ERROR", "需要 customer_id 或 features")
    X, _ = build_segment_matrix(df, feature_columns=cols, fit=False, transformer=bundle.get("transformer"))
    cid = int(model.predict(X)[0])
    dist = None
    if hasattr(model, "transform"):
        dist = float(np.min(model.transform(X)[0]))
    summary = artifacts.load_json(meta_path)
    cluster_meta = next(
        (c for c in (summary.get("clusters") or []) if int(c.get("cluster_id", -1)) == cid),
        None,
    )
    return {
        "cluster_id": cid,
        "distance": dist,
        "customer_id": customer_id,
        "cluster": cluster_meta,
        "disclaimer": "分群训练不含 Conversion；转化为事后统计",
    }

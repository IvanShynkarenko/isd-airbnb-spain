"""Baseline required by the brief: median train price for the same room type and number of guests."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BaselineModel:
    by_room_acc: dict
    by_room: dict
    global_median: float

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        out = []
        for rt, acc in zip(df["room_type"], df["accommodates"]):
            key = (rt, None if pd.isna(acc) else int(acc))
            if key in self.by_room_acc:
                out.append(self.by_room_acc[key])
            elif rt in self.by_room:
                out.append(self.by_room[rt])
            else:
                out.append(self.global_median)
        return np.asarray(out, dtype=float)


def fit_baseline(train: pd.DataFrame) -> BaselineModel:
    t = train.dropna(subset=["price"])
    by_ra = t.dropna(subset=["accommodates"]).groupby(["room_type", t["accommodates"].dropna().astype(int)])["price"].median()
    return BaselineModel(
        by_room_acc={(rt, int(a)): float(v) for (rt, a), v in by_ra.items()},
        by_room=t.groupby("room_type")["price"].median().astype(float).to_dict(),
        global_median=float(t["price"].median()),
    )

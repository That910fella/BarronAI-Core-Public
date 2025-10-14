from __future__ import annotations
from typing import Any, Callable
import yaml, pandas as pd, math

def _apply_rule(df: pd.DataFrame, rule: dict) -> pd.Series:
    if "expr" in rule:
        # safe eval: only allow df column names and math funcs
        local = {c: df[c] for c in df.columns if c.isidentifier()}
        local.update({"abs":abs, "math":math})
        return eval(rule["expr"], {"__builtins__":{}}, local)
    f, op, val = rule["field"], rule["op"], rule["value"]
    s = df[f]
    if op == "between": return s.between(val[0], val[1])
    if op == ">" : return s >  val
    if op == ">=": return s >= val
    if op == "<" : return s <  val
    if op == "<=": return s <= val
    if op == "==" : return s == val
    raise ValueError(f"Unknown op {op}")

def run_preset(df: pd.DataFrame, preset: dict) -> pd.DataFrame:
    if df.empty: return df
    m = pd.Series(True, index=df.index)
    for rule in preset.get("filters", []):
        m &= _apply_rule(df, rule)
    return df[m].copy()

def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

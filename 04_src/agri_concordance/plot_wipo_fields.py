"""wipo-agri 특허의 IPCR을 WIPO 기술 연계표(2026-03)에 붙인다.

녹색기술 연계표는 쓰지 않는다. IPC 기호 하나는 가장 긴 패턴 하나의 분야로만 간다.
한 문헌에 분야가 여러 개면 각 분야에 1/n을 준다. 합은 분야가 하나라도 붙은 문헌 수다.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
PATENTS = ROOT / "05_data" / "agri" / "wipo-agri.csv"
CONCORDANCE = ROOT / "06_references" / "need-response" / "2026-03_wipo_ipc-technology.csv"
OUT_DIR = Path(__file__).resolve().parent / "figures"
FONT = "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf"

SECTOR_COLOR = {
    "Electrical engineering": "#4C78A8",
    "Instruments": "#F58518",
    "Chemistry": "#54A24B",
    "Mechanical engineering": "#E45756",
    "Other fields": "#B279A2",
}


def norm(symbol: str) -> str:
    return symbol.replace(" ", "").upper()


def load_patterns(path: Path) -> list[tuple[str, str, str, str]]:
    patterns: list[tuple[str, str, str, str]] = []
    seen: dict[str, tuple[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            prefix = norm(row["IPC_code"]).rstrip("%")
            field = f"{int(row['Field_number']):02d} {row['Field_en']}"
            sector = row["Sector_en"]
            previous = seen.get(prefix)
            if previous is not None and previous != (field, sector):
                raise ValueError(f"같은 IPC 패턴이 두 분야에 있다: {prefix}")
            seen[prefix] = (field, sector)
            patterns.append((prefix, field, sector, row["Field_number"]))
    patterns.sort(key=lambda item: len(item[0]), reverse=True)
    return patterns


def match_field(symbol: str, patterns: list[tuple[str, str, str, str]]) -> tuple[str, str] | None:
    token = norm(symbol)
    for prefix, field, sector, _number in patterns:
        if token.startswith(prefix):
            return field, sector
    return None


def split_ipcr(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";;") if part.strip()]


def fractional_counts(patterns: list[tuple[str, str, str, str]]) -> tuple[Counter, dict[str, str], dict[str, int]]:
    weights: Counter = Counter()
    sector_of: dict[str, str] = {}
    stats = {"patents": 0, "no_ipcr": 0, "unmatched": 0, "matched": 0}
    with PATENTS.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            stats["patents"] += 1
            symbols = split_ipcr(row.get("IPCR Classifications") or "")
            if not symbols:
                stats["no_ipcr"] += 1
                stats["unmatched"] += 1
                continue
            fields: dict[str, str] = {}
            for symbol in symbols:
                hit = match_field(symbol, patterns)
                if hit is not None:
                    fields[hit[0]] = hit[1]
            if not fields:
                stats["unmatched"] += 1
                continue
            stats["matched"] += 1
            share = 1.0 / len(fields)
            for field, sector in fields.items():
                weights[field] += share
                sector_of[field] = sector
    return weights, sector_of, stats


def write_table(path: Path, weights: Counter, sector_of: dict[str, str], matched: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "sector", "fractional_count", "share_of_matched"])
        for field, count in weights.most_common():
            writer.writerow([field, sector_of[field], f"{count:.4f}", f"{count / matched:.6f}"])


def plot(path: Path, weights: Counter, sector_of: dict[str, str], stats: dict[str, int]) -> None:
    font_manager.fontManager.addfont(FONT)
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
    plt.rcParams["axes.unicode_minus"] = False

    ranked = weights.most_common()
    labels = [field for field, _count in ranked][::-1]
    values = [count for _field, count in ranked][::-1]
    colors = [SECTOR_COLOR[sector_of[field]] for field in labels]

    fig, ax = plt.subplots(figsize=(11, 10), dpi=140)
    ax.barh(labels, values, color=colors, height=0.72)
    span = max(values) if values else 1
    for y, value in enumerate(values):
        ax.text(value + span * 0.01, y, f"{value:,.1f}", va="center", fontsize=8, color="#333333")
    ax.set_xlabel("분할 건수")
    ax.set_xlim(0, span * 1.12)
    matched = stats["matched"]
    ax.set_title(
        "농식품 특허의 WIPO 기술 분야\n"
        f"IPCR, 문헌 분할 집계 · 붙은 문헌 {matched:,} / {stats['patents']:,}"
        f" · 안 붙은 문헌 {stats['unmatched']:,}",
        loc="left",
        fontsize=13,
        pad=12,
    )
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=sector)
        for sector, color in SECTOR_COLOR.items()
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    patterns = load_patterns(CONCORDANCE)
    weights, sector_of, stats = fractional_counts(patterns)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_table(OUT_DIR / "wipo_fields_fractional.csv", weights, sector_of, stats["matched"])
    plot(OUT_DIR / "wipo_fields_fractional.png", weights, sector_of, stats)
    by_sector: dict[str, float] = defaultdict(float)
    for field, count in weights.items():
        by_sector[sector_of[field]] += count
    print("patents", stats["patents"], "matched", stats["matched"], "unmatched", stats["unmatched"])
    for sector, count in sorted(by_sector.items(), key=lambda item: -item[1]):
        print(f"{count:8.1f}  {sector}")
    print("figure", OUT_DIR / "wipo_fields_fractional.png")


if __name__ == "__main__":
    main()

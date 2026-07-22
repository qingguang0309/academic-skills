"""共享合成显微结构:所有面板 import 本模块,保证跨面板同一视场、同一相场。
相:0=孔隙 1=C-(A)-S-H凝胶 2=SCM颗粒 3=未水化熟料。
关键设定:SCM 与凝胶灰度刻意重叠(0.58 vs 0.52)以呈现"仅凭 BSE 不可分"。"""
import numpy as np
from scipy.ndimage import gaussian_filter

PALETTE = {"pore": "#2F2F2F", "csh": "#56B4E9", "scm": "#009E73", "clinker": "#E69F00"}
PHASE_COLORS = [PALETTE["pore"], PALETTE["csh"], PALETTE["scm"], PALETTE["clinker"]]
PHASE_NAMES = ["孔隙", "C-(A)-S-H 凝胶", "SCM 颗粒", "未水化熟料"]
GRAYS = [0.08, 0.52, 0.58, 0.92]
N = 384
_SEED = 11


def make_field(n: int = N):
    """返回 (phase[int 0..3], gray[float 0..1]),确定性。"""
    rng = np.random.default_rng(_SEED)

    def blobs(sig, frac):
        b = gaussian_filter(rng.standard_normal((n, n)), sig)
        return b > np.quantile(b, 1 - frac)

    phase = np.ones((n, n), dtype=int)          # 基体 = C-(A)-S-H
    phase[blobs(9, 0.20)] = 2                   # SCM 颗粒
    phase[blobs(12, 0.14)] = 3                  # 未水化熟料
    phase[blobs(4.5, 0.08)] = 0                 # 孔隙(最后覆盖)
    gray = np.asarray(GRAYS)[phase]
    gray = gray + 0.045 * gaussian_filter(rng.standard_normal((n, n)), 2.5) \
                + 0.018 * rng.standard_normal((n, n))
    gray = gaussian_filter(np.clip(gray, 0, 1), 0.6)
    return phase, gray


def eds_points(n_points: int = 46, n: int = N):
    """稀疏 EDS 采样点(仅固相),返回 (xs, ys, phase_ids),确定性。"""
    rng = np.random.default_rng(_SEED + 1)
    phase, _ = make_field(n)
    ys, xs = np.where(phase > 0)
    pick = rng.choice(len(xs), n_points, replace=False)
    return xs[pick], ys[pick], phase[ys[pick], xs[pick]]

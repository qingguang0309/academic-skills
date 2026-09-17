"""生成评测题目用的合成数据(固定随机种子,重跑结果逐字节一致)。

数据是物理上合理的合成数据,只用于测 skill 的出图能力,不代表任何真实样品。
改动本文件会改变题目,history.jsonl 里之前的分数就不再可比——除非确有必要,不要改。

    python3 make_data.py          # 写入 tasks/*/data/
"""

from __future__ import annotations

import csv
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _write(task, name, header, rows):
    path = os.path.join(HERE, "tasks", task, "data", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def _fmt(v, nd):
    return f"{v:.{nd}f}"


# ------------------------------------------------------------------ t1 XRD

def xrd():
    rng = np.random.default_rng(101)
    tt = np.round(np.arange(10.0, 80.0 + 1e-9, 0.05), 2)
    # 锐钛矿 TiO2(JCPDS 21-1272)
    ref = [(25.28, 100, "(101)"), (36.95, 10, "(103)"), (37.80, 20, "(004)"), (38.58, 10, "(112)"),
           (48.05, 35, "(200)"), (53.89, 20, "(105)"), (55.06, 20, "(211)"), (62.69, 14, "(204)"),
           (68.76, 6, "(116)"), (70.31, 6, "(220)"), (75.03, 10, "(215)")]

    def pv(x, x0, fwhm, eta=0.5):
        g = np.exp(-4 * np.log(2) * (x - x0) ** 2 / fwhm ** 2)
        lo = 1 / (1 + 4 * (x - x0) ** 2 / fwhm ** 2)
        return eta * lo + (1 - eta) * g

    def pattern(shift, fwhm, scale, extra=()):
        y = 40 + 900 * np.exp(-tt / 9.0)          # 低角背底
        for x0, inten, _ in ref:
            y += scale * inten * 12 * pv(tt, x0 - shift, fwhm)
        for x0, inten in extra:
            y += inten * pv(tt, x0, 0.30)
        y = rng.poisson(np.clip(y, 1, None)).astype(float)
        return y

    cols = {
        "TiO2": pattern(0.00, 0.38, 1.00),
        "Nb2-TiO2": pattern(0.06, 0.46, 0.82),
        "Nb5-TiO2": pattern(0.12, 0.58, 0.66, extra=[(27.45, 210.0), (36.09, 70.0), (54.32, 90.0)]),
    }
    rows = [[_fmt(t, 2)] + [str(int(cols[k][i])) for k in cols] for i, t in enumerate(tt)]
    _write("t1_xrd", "xrd_counts.csv", ["two_theta_deg"] + list(cols), rows)
    _write("t1_xrd", "anatase_JCPDS_21-1272.csv", ["two_theta_deg", "rel_intensity", "hkl"],
           [[_fmt(a, 2), b, c] for a, b, c in ref])


# ------------------------------------------------------------------ t2 CV + EIS

def cv_eis():
    rng = np.random.default_rng(202)
    rows = []
    for v in (10, 20, 50, 100):                     # mV s-1
        up = np.linspace(1.00, 1.60, 301)
        E = np.concatenate([up, up[::-1][1:]])
        direction = np.concatenate([np.ones(301), -np.ones(300)])
        cdl = 0.0022 * v                            # 双电层电容电流 mA
        k = np.sqrt(v / 10.0)
        ox = 1.9 * k * np.exp(-((E - 1.38 - 0.004 * k) / 0.035) ** 2)
        red = -1.5 * k * np.exp(-((E - 1.31 + 0.004 * k) / 0.035) ** 2)
        oer = 0.012 * np.exp((E - 1.50) / 0.030)
        i = direction * cdl + np.where(direction > 0, ox, red) + oer
        i += rng.normal(0, 0.004, E.size)
        rows += [[v, _fmt(e, 4), _fmt(c, 4)] for e, c in zip(E, i)]
    _write("t2_cv_eis", "cv.csv", ["scan_rate_mV_s", "potential_V_vs_RHE", "current_mA"], rows)

    f = np.logspace(5, -1, 61)
    w = 2 * np.pi * f
    Rs, Rct, Cdl, sigma = 1.8, 24.5, 2.0e-5, 6.0
    Zw = sigma * w ** -0.5 * (1 - 1j)
    Z = Rs + 1 / (1 / (Rct + Zw) + 1j * w * Cdl)
    Z += rng.normal(0, 0.08, f.size) + 1j * rng.normal(0, 0.08, f.size)
    _write("t2_cv_eis", "eis.csv", ["freq_Hz", "Z_real_ohm", "Z_imag_ohm"],
           [[f"{a:.4g}", _fmt(z.real, 3), _fmt(z.imag, 3)] for a, z in zip(f, Z)])


# ------------------------------------------------------------------ t3 N2 等温线

def isotherm():
    rng = np.random.default_rng(303)
    p_ads = np.round(np.concatenate([np.geomspace(0.005, 0.1, 10), np.linspace(0.14, 0.99, 30)]), 4)
    p_des = np.round(np.linspace(0.99, 0.30, 24), 4)
    rows, psd = [], []
    for name, qm, cap, p_step in (("NC-800", 95.0, 120.0, 0.62), ("Co-SA/NC", 148.0, 190.0, 0.56)):
        def branch(p, shift):
            lang = qm * 12 * p / (1 + 12 * p)
            multi = 25 * p
            cond = cap / (1 + np.exp(-(p - (p_step - shift)) / 0.035))
            return lang + multi + cond + 60 * np.exp((p - 1) / 0.02)
        for p in p_ads:
            rows.append([name, "adsorption", _fmt(p, 4), _fmt(branch(p, 0.0) + rng.normal(0, 0.6), 2)])
        for p in p_des:
            rows.append([name, "desorption", _fmt(p, 4), _fmt(branch(p, 0.13) + rng.normal(0, 0.6), 2)])
        d = np.round(np.geomspace(1.7, 60, 40), 3)
        peak = 4.2 if name == "NC-800" else 3.6
        dv = 0.9 * np.exp(-(np.log(d / peak) / 0.22) ** 2) + 0.05 * np.exp(-d / 30)
        psd += [[name, _fmt(a, 3), _fmt(max(b + rng.normal(0, 0.01), 0), 4)] for a, b in zip(d, dv)]
    _write("t3_isotherm", "n2_isotherm_77K.csv", ["sample", "branch", "p_over_p0", "quantity_cm3_g_STP"], rows)
    _write("t3_isotherm", "bjh_pore_size.csv", ["sample", "pore_width_nm", "dV_dlogD_cm3_g"], psd)


if __name__ == "__main__":
    xrd()
    cv_eis()
    isotherm()
    print("data written")

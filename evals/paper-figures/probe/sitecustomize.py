"""评测探针:重跑交付脚本时自动加载(放在 PYTHONPATH 最前面)。

每张图第一次 savefig 时拍一张"快照"写进 $EVAL_PROBE_OUT(jsonl):
尺寸、所有文字与字号、坐标轴标签/比例/线型、色标,以及用被测版本的
paperfig.check_layout 重新体检的结果。脚本用没用 paperfig、有没有
strict=False 绕过体检,都逃不过这一次独立体检。
"""

import json
import os
import sys


def _install():
    out = os.environ.get("EVAL_PROBE_OUT")
    checker_path = os.environ.get("EVAL_CHECKER")
    if not out:
        return
    os.environ.setdefault("MPLBACKEND", "Agg")
    import importlib.util

    import matplotlib.figure as mfig

    orig = mfig.Figure.savefig
    seen = {}

    def _checker():
        if "mod" not in seen:
            seen["mod"] = None
            if checker_path and os.path.exists(checker_path):
                spec = importlib.util.spec_from_file_location("_eval_paperfig", checker_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                seen["mod"] = mod
        return seen["mod"]

    def _snapshot(fig):
        from matplotlib.lines import Line2D
        from matplotlib.text import Text

        issues, check_error = [], None
        mod = _checker()
        if mod is not None:
            try:
                for it in mod.check_layout(fig):
                    it = mod._as_issue(it)
                    issues.append(it.to_dict())
            except Exception as exc:  # 体检自身崩溃也要记下来
                check_error = f"{type(exc).__name__}: {exc}"
        fig.canvas.draw()
        texts = []
        for t in fig.findobj(Text):
            s = t.get_text()
            if s and s.strip() and t.get_visible():
                texts.append({"s": s, "size": float(t.get_fontsize())})
        axes = []
        for ax in fig.findobj(lambda o: isinstance(o, __import__("matplotlib").axes.Axes)):
            bb = ax.get_window_extent()
            lines = []
            for ln in ax.get_lines():
                lines.append({"marker": str(ln.get_marker()), "mfc": str(ln.get_markerfacecolor()),
                              "ls": str(ln.get_linestyle()), "n": int(len(ln.get_xdata()))})
            dashed = any(str(c.get_linestyle()) not in ("solid", "-", "None", "[(None, None)]")
                         and "(0.0, None)" not in str(c.get_linestyle())
                         for c in ax.collections if hasattr(c, "get_linestyle"))
            cmaps = [im.get_cmap().name for im in ax.get_images()]
            cmaps += [c.get_cmap().name for c in ax.collections
                      if getattr(c, "get_array", lambda: None)() is not None]
            axes.append({
                "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
                "titles": [ax.get_title(loc=l) for l in ("left", "center", "right")],
                "xlim": list(map(float, ax.get_xlim())), "ylim": list(map(float, ax.get_ylim())),
                "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
                "axis_on": bool(ax.axison), "px": [float(bb.width), float(bb.height)],
                "lines": lines, "dashed_collection": dashed, "cmaps": cmaps,
            })
        dashed_fig = False
        for a in fig.findobj(lambda o: hasattr(o, "get_linestyle") and not isinstance(o, Text)):
            try:
                ls = a.get_linestyle()
            except Exception:
                continue
            if isinstance(a, Line2D):
                if ls in ("--", ":", "-."):
                    dashed_fig = True
            elif ls in ("dashed", "dotted", "dashdot", "--", ":", "-."):
                dashed_fig = True
        return {"size_in": list(map(float, fig.get_size_inches())), "texts": texts, "axes": axes,
                "dashed": dashed_fig, "issues": issues, "check_error": check_error,
                "script": os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None}

    def savefig(self, fname, *args, **kwargs):
        key = id(self)
        rec = None
        if key not in seen:
            try:
                rec = _snapshot(self)
            except Exception as exc:
                rec = {"snapshot_error": f"{type(exc).__name__}: {exc}"}
            seen[key] = rec
        res = orig(self, fname, *args, **kwargs)
        path = os.path.abspath(os.fspath(fname)) if isinstance(fname, (str, os.PathLike)) else None
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"fig": key, "pid": os.getpid(), "path": path,
                                 "dpi": kwargs.get("dpi"), "snapshot": rec}, ensure_ascii=False) + "\n")
        return res

    mfig.Figure.savefig = savefig


try:
    _install()
except Exception as _exc:  # 探针绝不能让被测脚本崩掉
    sys.stderr.write(f"[eval probe] 未安装: {_exc}\n")

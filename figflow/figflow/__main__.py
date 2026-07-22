import sys

from .compose import compose_spec

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("用法:python -m figflow <figure_spec.json> [输出.png]")
    out = compose_spec(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"合成完成:{out}")

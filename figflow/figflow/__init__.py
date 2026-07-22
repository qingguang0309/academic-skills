"""figflow — 分治出图工作流:并行面板生成 + 确定性锚点排版 + 审图回炉。"""
from .compose import Composer, compose_spec

__all__ = ["Composer", "compose_spec"]
__version__ = "0.1.0"

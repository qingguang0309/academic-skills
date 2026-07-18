"""LLM 后端抽象:anthropic SDK / claude CLI / fixture(离线测试)三种可插拔实现。

写作节点只依赖 complete(stage, system, prompt) -> str 这一个接口。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

DEFAULT_MODEL = "claude-opus-4-8"


class BackendError(RuntimeError):
    pass


class AnthropicBackend:
    """官方 anthropic SDK。零参客户端自动解析 ANTHROPIC_API_KEY / ant auth login 档案。"""

    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL):
        import anthropic  # 延迟导入,fixture 模式无需安装

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, stage: str, system: str, prompt: str) -> str:
        a = self._anthropic
        try:
            # 章节起草可能输出很长,统一走流式避免 HTTP 超时
            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                msg = stream.get_final_message()
        except a.AuthenticationError as e:
            raise BackendError(
                "Anthropic 认证失败:请设置 ANTHROPIC_API_KEY,或运行 `ant auth login`。"
            ) from e
        except a.RateLimitError as e:
            raise BackendError("触发限流,请稍后重试(SDK 已自动重试过)。") from e
        except a.APIConnectionError as e:
            raise BackendError("网络错误:无法连接 Anthropic API。") from e
        if msg.stop_reason == "refusal":
            raise BackendError(f"请求被安全策略拒绝(stage={stage})。")
        return "".join(b.text for b in msg.content if b.type == "text")


class ClaudeCLIBackend:
    """claude CLI 无头模式(claude -p),复用本机 Claude Code 登录态。"""

    name = "claude-cli"

    def __init__(self, model: str | None = None):
        self.bin = shutil.which("claude")
        if not self.bin:
            raise BackendError("未找到 claude CLI:npm install -g @anthropic-ai/claude-code")
        self.model = model

    def complete(self, stage: str, system: str, prompt: str) -> str:
        cmd = [self.bin, "-p", f"{system}\n\n---\n\n{prompt}"]
        if self.model:
            cmd += ["--model", self.model]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired as e:
            raise BackendError(f"claude CLI 超时(stage={stage})") from e
        if r.returncode != 0:
            raise BackendError(
                f"claude CLI 失败(stage={stage}):{r.stderr.strip()[:300]}\n"
                "如提示认证问题,请先运行 `claude login`。"
            )
        return r.stdout.strip()


class FixtureBackend:
    """从 workdir/fixtures/{stage}.md 读取预置内容。用于离线测试与回归。"""

    name = "fixture"

    def __init__(self, workdir: str | Path):
        self.dir = Path(workdir) / "fixtures"
        if not self.dir.is_dir():
            raise BackendError(f"fixture 目录不存在:{self.dir}")

    def complete(self, stage: str, system: str, prompt: str) -> str:
        f = self.dir / f"{stage}.md"
        if not f.is_file():
            raise BackendError(
                f"缺少 fixture:{f}\n该阶段需要 LLM 后端(anthropic / claude-cli)或补齐 fixture 文件。"
            )
        return f.read_text(encoding="utf-8")


def make_backend(name: str, workdir: str | Path, model: str | None = None):
    """按名称构造后端;auto 优先 anthropic(有凭据),其次 claude CLI,最后 fixture。"""
    if name == "anthropic":
        return AnthropicBackend(model or DEFAULT_MODEL)
    if name == "claude-cli":
        return ClaudeCLIBackend(model)
    if name == "fixture":
        return FixtureBackend(workdir)
    if name == "auto":
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return AnthropicBackend(model or DEFAULT_MODEL)
        if shutil.which("claude"):
            return ClaudeCLIBackend(model)
        if (Path(workdir) / "fixtures").is_dir():
            return FixtureBackend(workdir)
        raise BackendError(
            "没有可用后端:请设置 ANTHROPIC_API_KEY、安装并登录 claude CLI,或提供 fixtures 目录。"
        )
    raise BackendError(f"未知后端:{name}")

from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager


class _OrderAspect:
    def __init__(self, seen: list[str], name: str) -> None:
        self.seen = seen
        self.name = name

    def before(self, ctx: AdviceContext) -> None:
        self.seen.append(f"before:{self.name}")

    def around(self, ctx: AdviceContext, call):  # type: ignore[no-untyped-def]
        self.seen.append(f"around:{self.name}")
        return call()

    def after(self, ctx: AdviceContext, result, error):  # type: ignore[no-untyped-def]
        self.seen.append(f"after:{self.name}")


def test_manager_ordering() -> None:
    seen: list[str] = []
    a1 = _OrderAspect(seen, "a1")
    a2 = _OrderAspect(seen, "a2")
    m = AspectManager([a1, a2])
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    out = m.run(ctx, lambda: "ok")
    assert out == "ok"
    assert seen[0].startswith("before:") and seen[0].endswith("a1")
    assert seen[1].startswith("before:") and seen[1].endswith("a2")
    # around is applied inner-most last (a2 wraps a1 wraps call)
    assert [x for x in seen if x.startswith("around:")] == ["around:a1", "around:a2"]
    assert seen[-1] == "after:a2"

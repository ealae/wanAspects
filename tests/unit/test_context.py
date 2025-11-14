from wanaspects.core.context import AdviceContext


def test_advice_context_basics() -> None:
    ctx = AdviceContext(step_name="s", container_shape="single", boundary="none")
    assert ctx.step_name == "s"
    assert ctx.container_shape == "single"
    assert ctx.boundary == "none"

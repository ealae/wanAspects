from wanaspects.aspects.context import ContextPropagationAspect
from wanaspects.context import current_context
from wanaspects.core.context import AdviceContext
from wanaspects.manager import AspectManager


def test_context_propagation_sets_and_resets_context() -> None:
    aspect = ContextPropagationAspect()
    manager = AspectManager([aspect])
    ctx = AdviceContext(step_name="ctx", container_shape="single")

    def check() -> str:
        assert current_context() == ctx
        return "ok"

    assert manager.run(ctx, check) == "ok"
    assert current_context() is None

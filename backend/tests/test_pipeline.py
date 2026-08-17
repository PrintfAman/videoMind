from app.services.pipeline import Pipeline, PipelineStage, ProcessingContext


class DummyStage(PipelineStage):
    def __init__(self, name, mark):
        self.name = name
        self.mark = mark

    def execute(self, ctx: ProcessingContext):
        ctx.results.setdefault("order", []).append(self.mark)


def test_pipeline_execution_order():
    stages = [DummyStage("s1", "one"), DummyStage("s2", "two"), DummyStage("s3", "three")]
    pipeline = Pipeline(stages)
    ctx = ProcessingContext(video_id="v1", video_path="/tmp/v1.mp4")
    pipeline.run(ctx)
    assert ctx.results["order"] == ["one", "two", "three"]
    assert ctx.processing_status == "completed"

from pathlib import Path
import pytest
from agent.pipeline import ScholarshipDailyPipeline


def test_full_pipeline_run(tmp_path):
    pipeline = ScholarshipDailyPipeline()
    # Run pipeline with verify_links=False so it runs lightning fast without real HTTP delays
    results = pipeline.run(dry_run=True, verify_links=False)

    assert "run_id" in results
    assert results["public_opportunities"] > 0
    assert results["private_opportunities"] > 0
    assert len(results["generated_files"]) == 8  # 4 for public, 4 for private

    # Verify each generated file exists and is non-empty
    for f in results["generated_files"]:
        path = Path(f)
        assert path.exists()
        assert path.stat().st_size > 0

import shutil
from pathlib import Path
import pytest
from agent.pipeline import ScholarshipDailyPipeline


def test_full_pipeline_run(tmp_path):
    pipeline = ScholarshipDailyPipeline()
    pipeline.reports_dir = tmp_path / "reports"
    pipeline.data_dir = tmp_path / "data"
    pipeline.data_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pipeline.workspace_root / "data" / "scholarships.json", pipeline.data_dir / "scholarships.json")

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

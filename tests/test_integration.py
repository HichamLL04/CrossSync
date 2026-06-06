import os
import pysrt
from src.aligner import SemanticAligner
from src.sync_pipeline import SubSyncPipeline

def test_full_pipeline_without_llm_fallback():
    unsynced = "tests/data/unsynced_santa.srt"
    synced = "tests/data/synced_santa.srt"
    output = "tests/data/output_santa.srt"
    
    if os.path.exists(output):
        os.remove(output)

    # Use a multilingual embedding model since the text is in Spanish
    aligner = SemanticAligner(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    # Use fallback splitting (no LLM client passed)
    pipeline = SubSyncPipeline(aligner=aligner)
    
    pipeline.sync(unsynced, synced, output)
    
    assert os.path.exists(output)
    
    out_subs = pysrt.open(output)
    ref_subs = pysrt.open(synced)
    
    # The output file should have exactly the number of lines as B (7 lines)
    assert len(out_subs) == len(ref_subs)
    # Check that timestamps match B
    assert out_subs[0].start == ref_subs[0].start
    assert out_subs[-1].end == ref_subs[-1].end

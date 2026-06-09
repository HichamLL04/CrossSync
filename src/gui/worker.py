import os
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
from src.translations import TRANSLATIONS

# Sync worker running in background
class SyncWorker(QThread):
    finished_signal = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)

    def __init__(self, mode, params):
        super().__init__()
        self.mode = mode  # "individual" or "batch"
        self.params = params
        self.lang = params.get("lang", "es")

    def tr(self, key):
        return TRANSLATIONS[self.lang].get(key, key)

    def run(self):
        try:
            from src.aligner import SemanticAligner
            from src.llm_client import LLMClient
            from src.sync_pipeline import SubSyncPipeline
            from sync import parse_id

            self.log_signal.emit(self.tr("loading_embeddings"))
            aligner = SemanticAligner(model_name=self.params["embedding_model"])

            llm_client = None
            if self.params["llm_provider"] and self.params["llm_provider"] != "none":
                self.log_signal.emit(self.tr("initializing_llm").format(provider=self.params['llm_provider']))
                llm_client = LLMClient(
                    provider=self.params["llm_provider"],
                    model=self.params["llm_model"],
                    api_key=self.params["api_key"],
                    url=self.params["ollama_url"]
                )

            pipeline = SubSyncPipeline(aligner=aligner, llm_client=llm_client)

            if self.mode == "batch":
                unsynced_dir = self.params["unsynced_dir"]
                synced_dir = self.params["synced_dir"]
                output_dir = self.params["output_dir"]

                os.makedirs(output_dir, exist_ok=True)
                unsynced_files = sorted([os.path.join(unsynced_dir, f) for f in os.listdir(unsynced_dir) if f.endswith('.srt')])
                synced_files = sorted([os.path.join(synced_dir, f) for f in os.listdir(synced_dir) if f.endswith('.srt')])

                synced_map = {}
                for sf in synced_files:
                    fid = parse_id(sf)
                    if fid:
                        synced_map[fid] = sf

                total_files = len(unsynced_files)
                self.log_signal.emit(self.tr("found_files").format(count=total_files))

                matched_count = 0
                for idx, uf in enumerate(unsynced_files):
                    fid = parse_id(uf)
                    if fid and fid in synced_map:
                        out_name = os.path.basename(uf)
                        out_path = os.path.join(output_dir, out_name)
                        self.log_signal.emit(f"\n[{idx+1}/{total_files}] " + self.tr("syncing_file").format(name=os.path.basename(uf)))
                        pipeline.sync(uf, synced_map[fid], out_path)
                        matched_count += 1
                    else:
                        self.log_signal.emit(self.tr("sync_warning_match").format(name=os.path.basename(uf), fid=fid))

                self.finished_signal.emit(True, self.tr("batch_completed").format(matched=matched_count, total=total_files))
            else:
                unsynced = self.params["unsynced"]
                synced = self.params["synced"]
                output = self.params["output"]

                self.log_signal.emit(self.tr("syncing_indiv").format(name=os.path.basename(unsynced)))
                pipeline.sync(unsynced, synced, output)
                self.finished_signal.emit(True, self.tr("single_completed"))
        except Exception as e:
            tb = traceback.format_exc()
            self.finished_signal.emit(False, self.tr("sync_error_msg").format(e=str(e), tb=tb))

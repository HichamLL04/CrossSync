import pysrt
import numpy as np
import unicodedata
from src.cleaner import clean_text
from src.aligner import SemanticAligner, align_sequences
from src.decision_engine import parse_dtw_path
from src.llm_client import LLMClient

def validate_and_clean_parts(parts: list[str], original_text: str) -> list[str]:
    def normalize_word(word: str) -> str:
        word_nfd = unicodedata.normalize('NFD', word.lower())
        stripped = "".join(c for c in word_nfd if not unicodedata.combining(c))
        return "".join(c for c in stripped if c.isalnum())

    orig_words = set(normalize_word(w) for w in original_text.split())
    orig_words = {w for w in orig_words if w}

    cleaned_parts = []
    for part in parts:
        part_words = part.split()
        valid_words = []
        for word in part_words:
            w_norm = normalize_word(word)
            if not w_norm or w_norm in orig_words:
                valid_words.append(word)
        cleaned_parts.append(" ".join(valid_words))
    return cleaned_parts


class SubSyncPipeline:
    def __init__(self, aligner: SemanticAligner, llm_client: LLMClient = None):
        self.aligner = aligner
        self.llm_client = llm_client

    def sync(self, unsynced_path: str, synced_path: str, output_path: str):
        subs_a = pysrt.open(unsynced_path)
        subs_b = pysrt.open(synced_path)

        if not subs_a or not subs_b:
            raise ValueError("Input subtitle files cannot be empty.")

        # Extract cleaned text
        clean_a = [clean_text(sub.text) for sub in subs_a]
        clean_b = [clean_text(sub.text) for sub in subs_b]

        # Calculate semantic alignment
        embs_a = self.aligner.get_embeddings(clean_a)
        embs_b = self.aligner.get_embeddings(clean_b)
        cost_mat = self.aligner.compute_cost_matrix(embs_a, embs_b)
        path = align_sequences(cost_mat)
        groups = parse_dtw_path(path)

        synced_subs = pysrt.SubRipFile()
        item_counter = 1

        for group in groups:
            gtype = group["type"]
            src_idx = group["source_indices"]
            tgt_idx = group["target_indices"]

            if gtype == "keep":
                # Copy text from A, timing from B
                orig_text = clean_a[src_idx[0]]
                ref_sub = subs_b[tgt_idx[0]]
                synced_subs.append(pysrt.SubRipItem(
                    index=item_counter,
                    start=ref_sub.start,
                    end=ref_sub.end,
                    text=orig_text
                ))
                item_counter += 1

            elif gtype == "join":
                # Merge multiple A items into one B item time slot
                merged_text = " ".join(clean_a[i] for i in src_idx)
                # If many target slots, span start of first to end of last
                start_time = subs_b[tgt_idx[0]].start
                end_time = subs_b[tgt_idx[-1]].end
                synced_subs.append(pysrt.SubRipItem(
                    index=item_counter,
                    start=start_time,
                    end=end_time,
                    text=merged_text
                ))
                item_counter += 1

            elif gtype == "split":
                # Split one A item into multiple B item times
                original_text = clean_a[src_idx[0]]
                num_parts = len(tgt_idx)
                ref_texts = [clean_b[i] for i in tgt_idx]

                parts = []
                
                # 1. Semantic Dominant Match check: check if the original text matches one reference overwhelmingly
                if num_parts > 1:
                    try:
                        embs_ref = self.aligner.get_embeddings(ref_texts)
                        emb_orig = self.aligner.get_embeddings([original_text])[0]
                        
                        norm_orig = emb_orig / np.linalg.norm(emb_orig)
                        norm_refs = embs_ref / np.linalg.norm(embs_ref, axis=1, keepdims=True)
                        similarities = np.dot(norm_refs, norm_orig)
                        
                        sorted_indices = np.argsort(similarities)[::-1]
                        best_idx = sorted_indices[0]
                        second_idx = sorted_indices[1]
                        best_sim = similarities[best_idx]
                        second_sim = similarities[second_idx]
                        
                        if best_sim > 0.50 and (best_sim - second_sim) >= 0.20:
                            parts = [""] * num_parts
                            parts[best_idx] = original_text
                    except Exception as e:
                        print(f"Warning: Semantic check failed during split: {e}")

                # 2. If no dominant match, query the LLM Client to split
                if not parts and self.llm_client:
                    try:
                        parts = self.llm_client.split_line(original_text, num_parts, ref_texts)
                        # Validate and clean parts returned by the LLM (remove hallucinations/copies not in A)
                        parts = validate_and_clean_parts(parts, original_text)
                    except Exception as e:
                        print(f"Warning: LLM split failed: {e}. Falling back to even division.")
                        parts = []

                # 3. Fallback simple split if LLM/dominant match fails or is not provided
                if len(parts) != num_parts:
                    words = original_text.split()
                    chunk_size = max(1, len(words) // num_parts)
                    parts = [" ".join(words[i * chunk_size:(i + 1) * chunk_size]) for i in range(num_parts)]
                    # append remaining words to last chunk
                    if len(words) > chunk_size * num_parts:
                        parts[-1] += " " + " ".join(words[chunk_size * num_parts:])

                for idx, b_idx in enumerate(tgt_idx):
                    ref_sub = subs_b[b_idx]
                    synced_subs.append(pysrt.SubRipItem(
                        index=item_counter,
                        start=ref_sub.start,
                        end=ref_sub.end,
                        text=parts[idx]
                      ))
                    item_counter += 1

        synced_subs.save(output_path, encoding='utf-8')

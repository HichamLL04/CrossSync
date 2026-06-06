# 🎬 SubSync - Semantic Subtitle Synchronizer

SubSync is a tool designed to synchronize out-of-sync subtitles (e.g., in Spanish) using a correctly synchronized reference subtitle in another language (e.g., English). It utilizes multilingual sentence embeddings to calculate semantic alignment across different languages and optional local LLMs (via Ollama) to handle complex splits.

## 🚀 Features

* **Multilingual Semantic Alignment**: Uses `SentenceTransformers` (`paraphrase-multilingual-MiniLM-L12-v2`) to align subtitle text semantically, regardless of the language.
* **Dynamic Time Warping (DTW)**: Sequentially aligns the source and target subtitle blocks.
* **Semantic Dominant Match**: Automatically detects when a dialogue line matches a single target slot among a group containing unrelated elements (like on-screen text, signs, timestamps, or songs), leaving the extra elements empty.
* **LLM-assisted Splits**: Optionally utilizes local LLM models (e.g., `qwen2.5:3b` via Ollama) to semantically divide sentences when a single subtitle block must be split into multiple reference timestamps.
* **Vocabulary Validation**: Employs an accent-insensitive validation helper to guarantee that only words present in the original subtitle are included in the final output, preventing translation leakage or hallucinations.
* **Google Colab Notebook**: Includes an interactive notebook (`SubSync_Colab.ipynb`) with visual form fields and automated GPU-accelerated Ollama installation.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kaiser/SubSnyc.git
   cd SubSnyc
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Usage

### Basic Synchronization (Embeddings only)
To synchronize subtitles using only semantic embedding alignment (falls back to proportional split for multi-line divisions):
```bash
PYTHONPATH=. python sync.py \
  --unsynced "/path/to/unsynced.srt" \
  --synced "/path/to/reference.srt" \
  --output "/path/to/output.srt"
```

### Advanced Synchronization (With Ollama LLM)
Ensure you have [Ollama](https://ollama.com/) running and the chosen model pulled (e.g., `ollama pull qwen2.5:3b`):
```bash
PYTHONPATH=. python sync.py \
  --unsynced "/path/to/unsynced.srt" \
  --synced "/path/to/reference.srt" \
  --output "/path/to/output.srt" \
  --llm-provider ollama \
  --llm-model qwen2.5:3b
```

### Command Line Arguments
* `--unsynced`: Path to the out-of-sync subtitle file.
* `--synced`: Path to the reference subtitle file (correctly timed).
* `--output`: Path where the synchronized subtitle file will be saved.
* `--llm-provider`: LLM provider to use (`ollama` or `none`).
* `--llm-model`: The name of the model to use (default: `qwen2.5:3b`).
* `--ollama-url`: The Ollama API URL (default: `http://localhost:11434`).

## 📓 Google Colab
You can run SubSync in the cloud using the included notebook:
1. Open Google Colab.
2. Upload `SubSync_Colab.ipynb` to your Google Drive or open it directly.
3. Under *Runtime* > *Change runtime type*, select **T4 GPU** for faster processing.
4. Fill in the visual forms to run the synchronization.

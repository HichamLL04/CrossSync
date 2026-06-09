#!/usr/bin/env python3
import os
import sys
import argparse
import re
from src.aligner import SemanticAligner
from src.llm_client import LLMClient
from src.sync_pipeline import SubSyncPipeline

def parse_id(filename: str) -> str:
    base = os.path.basename(filename)
    
    # Remove all bracketed tags first! e.g., "[BD 1080p FLAC]", "[55CE8766]", "[TV-720P]"
    cleaned_base = re.sub(r"\[[^\]]+\]", "", base)
    
    # Also remove common video resolutions, codecs, bits: "1080p", "720p", "480p", "10bit", "8bit", "x264", "x265", "h264", "h265", "hevc"
    cleaned_base = re.sub(r"\b\d{3,4}p\b", "", cleaned_base, flags=re.IGNORECASE)
    cleaned_base = re.sub(r"\b\d+bit\b", "", cleaned_base, flags=re.IGNORECASE)
    cleaned_base = re.sub(r"\b(?:[xh]\.?26[45]|hevc|av1)\b", "", cleaned_base, flags=re.IGNORECASE)
    cleaned_base = re.sub(r"\b20\d{2}\b", "", cleaned_base) # Year
    
    # 1. Matches E01, EP01, EP_01, EP-01, Episode 01, Episode-01, Capitulo 01, etc.
    match_ep = re.search(r"\b(?:ep|e|episode|cap|capitulo|capítulo)\s*[_\-]?\s*(\d+)\b", cleaned_base, re.IGNORECASE)
    if match_ep:
        return f"{int(match_ep.group(1)):02d}"
        
    # 2. Search for the first isolated 2-digit or 3-digit number in the remaining text
    match_num = re.search(r"\b(\d{2,3})\b", cleaned_base)
    if match_num:
        return f"{int(match_num.group(1)):02d}"
        
    if '-' in base:
        return base.split('-', 1)[0].strip()
    return ""

def process_file(unsynced_path, synced_path, output_path, pipeline):
    print(f"Syncing: {os.path.basename(unsynced_path)} -> {os.path.basename(output_path)}")
    try:
        pipeline.sync(unsynced_path, synced_path, output_path)
        print("Success!")
    except Exception as e:
        print(f"Error syncing {unsynced_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="SubSync: Sincronizador de subtítulos con LLMs y Embeddings.")
    
    # Individual Mode Args
    parser.add_argument("--unsynced", help="Ruta al archivo SRT origen (sin sincronizar).")
    parser.add_argument("--synced", help="Ruta al archivo SRT de referencia (sincronizado).")
    parser.add_argument("--output", help="Ruta del archivo SRT final de salida.")

    # Batch Mode Args
    parser.add_argument("--unsynced-dir", help="Directorio con subtítulos origen.")
    parser.add_argument("--synced-dir", help="Directorio con subtítulos referencia.")
    parser.add_argument("--output-dir", help="Directorio para guardar subtítulos sincronizados.")

    # LLM Args
    parser.add_argument("--llm-provider", choices=["ollama", "gemini", "openai", "none"], default="none", help="Proveedor LLM.")
    parser.add_argument("--llm-model", default="qwen2.5:7b-instruct", help="Nombre del modelo LLM.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Endpoint de Ollama.")
    parser.add_argument("--api-key", help="Clave API (Gemini/OpenAI).")

    # Embedding Args
    parser.add_argument("--embedding-model", default="paraphrase-multilingual-MiniLM-L12-v2", help="Modelo de embeddings.")

    # GUI Mode Flag
    parser.add_argument("--gui", action="store_true", help="Forzar el inicio en modo interfaz gráfica (GUI).")

    args = parser.parse_args()

    # Determine if we should start the GUI.
    # We start GUI if --gui is passed, or if NO args are passed at all.
    has_cli_args = any([
        args.unsynced, args.synced, args.output,
        args.unsynced_dir, args.synced_dir, args.output_dir
    ])
    
    if args.gui or not has_cli_args:
        try:
            from src.gui import start_gui
            start_gui()
            return
        except ImportError as e:
            print(f"Error al iniciar la GUI: {e}")
            print("Asegúrate de tener PyQt6 instalado o ejecuta en modo CLI con los argumentos correspondientes.")
            parser.print_help()
            sys.exit(1)

    # Load API Key from environment if not provided
    api_key = args.api_key or os.getenv("LLM_API_KEY")

    # Initialize AI Components
    print("Loading embedding model...")
    aligner = SemanticAligner(model_name=args.embedding_model)
    
    llm_client = None
    if args.llm_provider and args.llm_provider != "none":
        llm_client = LLMClient(
            provider=args.llm_provider,
            model=args.llm_model,
            api_key=api_key,
            url=args.ollama_url
        )
        
    pipeline = SubSyncPipeline(aligner=aligner, llm_client=llm_client)

    # Batch mode
    if args.unsynced_dir and args.synced_dir and args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        unsynced_files = [os.path.join(args.unsynced_dir, f) for f in os.listdir(args.unsynced_dir) if f.endswith('.srt')]
        synced_files = [os.path.join(args.synced_dir, f) for f in os.listdir(args.synced_dir) if f.endswith('.srt')]

        # Index reference files by ID prefix
        synced_map = {}
        for sf in synced_files:
            fid = parse_id(sf)
            if fid:
                synced_map[fid] = sf

        # Process matched files
        for uf in unsynced_files:
            fid = parse_id(uf)
            if fid and fid in synced_map:
                out_name = os.path.basename(uf)
                out_path = os.path.join(args.output_dir, out_name)
                process_file(uf, synced_map[fid], out_path, pipeline)
            else:
                print(f"Warning: No match found for file {uf} using ID '{fid}'")

    # Individual mode
    elif args.unsynced and args.synced and args.output:
        process_file(args.unsynced, args.synced, args.output, pipeline)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

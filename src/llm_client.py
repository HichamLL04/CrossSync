import json
import re
import requests

class LLMClient:
    def __init__(self, provider: str, model: str, api_key: str = None, url: str = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.url = url or "http://localhost:11434"

    def _post_with_retry(self, url: str, json_data: dict, headers: dict) -> requests.Response:
        import time
        max_retries = 5
        for attempt in range(max_retries):
            try:
                res = requests.post(url, json=json_data, headers=headers)
                if res.status_code == 429 or res.status_code >= 500:
                    wait_time = (2 ** attempt) + 1
                    print(f"Warning: API returned status {res.status_code}. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                res.raise_for_status()
                return res
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = (2 ** attempt) + 1
                print(f"Warning: Connection error {e}. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)

    def split_line(self, text: str, num_parts: int, references: list[str]) -> list[str]:
        refs_formatted = "\n".join(f"- Parte {i+1} de referencia: \"{ref}\"" for i, ref in enumerate(references))
        
        prompt = f"""Eres un asistente experto en sincronización de subtítulos.
Tu tarea es dividir una línea de texto del subtítulo original (A) en exactamente {num_parts} partes secuenciales.
El texto original de A es:
"{text}"

Para guiarte sobre dónde realizar las divisiones semánticas, aquí tienes el texto de referencia de los subtítulos sincronizados (B) para cada una de las partes:
{refs_formatted}

Reglas estrictas:
1. NO inventes, traduzcas, agregues ni omitas palabras del texto original A. Cada palabra que uses en las partes resultantes debe pertenecer originalmente al texto de A. La unión de todas las partes no vacías en su orden original debe ser exactamente idéntica a "{text}".
2. Divide el texto ÚNICAMENTE en límites lógicos de frases u oraciones (ej. después de comas, preposiciones, pausas naturales). Jamás dividas a mitad de una palabra.
3. ASOCIACIÓN SEMÁNTICA: Compara detenidamente el significado de A con las referencias de B. Si una referencia de B no tiene correspondencia semántica con el diálogo de A (por ejemplo: si la referencia de B es un letrero en pantalla, cartel, hora, canción, créditos o línea adicional que no está en A), esa parte en tu respuesta DEBE ser obligatoriamente una cadena vacía (""). Coloca los fragmentos de A únicamente en las posiciones que tengan una correspondencia semántica real con las referencias de B.
4. Responde exclusivamente con un JSON que contenga un objeto con la clave "partes", cuyo valor sea una lista de cadenas de texto (strings) con exactamente {num_parts} elementos.

Aquí tienes ejemplos de cómo resolver esta tarea:

Ejemplo 1 (Referencias adicionales no presentes en A):
Texto original de A: "Con mi graduación escolar,"
Referencias de B:
- Parte 1 de referencia: "Entrance Ceremony"
- Parte 2 de referencia: "Entrance Ceremony"
- Parte 3 de referencia: "9:30 am"
- Parte 4 de referencia: "As I graduated from middle school,"
Respuesta:
{{
  "partes": [
    "",
    "",
    "",
    "Con mi graduación escolar,"
  ]
}}

Ejemplo 2 (División secuencial estándar):
Texto original de A: "Hola, me llamo Juan y vivo en Madrid."
Referencias de B:
- Parte 1 de referencia: "Hello, my name is John"
- Parte 2 de referencia: "and I live in Madrid."
Respuesta:
{{
  "partes": [
    "Hola, me llamo Juan",
    "y vivo en Madrid."
  ]
}}

Responde con el JSON correspondiente al texto original A y las referencias de B dadas al principio."""

        if self.provider == "ollama":
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0.0},
                "format": "json",
                "stream": False
            }
            headers = {"Content-Type": "application/json"}
            res = self._post_with_retry(f"{self.url}/api/chat", json_data=payload, headers=headers)
            content = res.json()["message"]["content"]
        
        elif self.provider == "gemini":
            headers = {"Content-Type": "application/json"}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json"
                }
            }
            res = self._post_with_retry(url, json_data=payload, headers=headers)
            content = res.json()["candidates"][0]["content"]["parts"][0]["text"]

        elif self.provider == "openai":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            res = self._post_with_retry("https://api.openai.com/v1/chat/completions", json_data=payload, headers=headers)
            content = res.json()["choices"][0]["message"]["content"]

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        # Parse output array
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return [str(s).strip() for s in data]
            elif isinstance(data, dict):
                # Check for list values in common keys
                for key in ["partes", "parts", "result", "list", "split"]:
                    if key in data and isinstance(data[key], list):
                        return [str(s).strip() for s in data[key]]
                # If it's a dict with keys like "parte 1", "parte 2" or "1", "2"
                # where all values are strings, extract the values in sorted key order
                if all(isinstance(v, str) for v in data.values()):
                    try:
                        sorted_keys = sorted(data.keys(), key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x)])
                    except Exception:
                        sorted_keys = sorted(data.keys())
                    return [str(data[k]).strip() for k in sorted_keys]
                raise ValueError("JSON response is a dictionary but could not extract parts list")
            else:
                raise ValueError("JSON response is not a list or dictionary")
        except Exception as e:
            # Fallback text parsing if JSON is malformed
            lines = [line.strip().strip('"') for line in content.replace('[', '').replace(']', '').split(',') if line.strip()]
            if len(lines) == num_parts:
                return lines
            raise ValueError(f"Failed to parse LLM content as JSON: {content}") from e

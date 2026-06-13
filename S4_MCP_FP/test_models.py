import os
from pathlib import Path

from google import genai

PROJECT_ID = "gcp-prj-dev-gis-dia-01"
LOCATIONS = ["global", "us-central1"]
ROOT_DIR = Path(__file__).resolve().parent

CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-image-preview",
]


def main() -> None:
    json_files = sorted(ROOT_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError("No JSON credentials file in root.")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(json_files[0])
    print(f"[info] Credentials: {json_files[0].name}")
    print(f"[info] Project: {PROJECT_ID}\n")

    results = []
    for location in LOCATIONS:
        print(f"\n--- Location: {location} ---")
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=location,
        )
        for model_id in CANDIDATE_MODELS:
            print(f"Testing {model_id} ...", end=" ", flush=True)
            try:
                resp = client.models.generate_content(
                    model=model_id,
                    contents="Reply with exactly one word: OK",
                )
                text = (resp.text or "").strip().replace("\n", " ")
                print(f"WORKING -> {text[:60]}")
                results.append((location, model_id, True, text[:80]))
            except Exception as e:
                msg = str(e).split("\n")[0][:120]
                print(f"FAILED  -> {msg}")
                results.append((location, model_id, False, msg))

    print("\n=== Summary ===")
    print(f"{'Status':<10} {'Location':<14} {'Model':<40} Detail")
    print("-" * 110)
    for location, model_id, ok, detail in results:
        status = "[WORKING]" if ok else "[FAILED]"
        print(f"{status:<10} {location:<14} {model_id:<40} {detail}")


if __name__ == "__main__":
    main()

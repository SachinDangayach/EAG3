import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]
MODEL_ID = os.environ["GCP_MODEL_ID"]

ROOT_DIR = Path(__file__).resolve().parent


def find_credentials_file(root: Path) -> Path:
    json_files = sorted(root.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No service account JSON file found in {root}. "
            "Place your GCP service account key JSON in the root folder."
        )
    if len(json_files) > 1:
        print(f"[info] Multiple JSON files found, using: {json_files[0].name}")
    return json_files[0]


def main(prompt: str = "who is sachin?") -> None:
    creds_path = find_credentials_file(ROOT_DIR)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
    print(f"[info] Using credentials: {creds_path}")
    print(f"[info] Project: {PROJECT_ID}, Location: {LOCATION}, Model: {MODEL_ID}")

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
    )

    print("\n=== Prompt ===")
    print(prompt)
    print("\n=== Response ===")
    print(response.text)


if __name__ == "__main__":
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "who is sachin?"
    main(user_prompt)

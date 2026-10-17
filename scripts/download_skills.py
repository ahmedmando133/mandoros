import os
import json
import hashlib
import urllib.request
from pathlib import Path
import concurrent.futures

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / "clinical_skills_library"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
LOCK_FILE = BASE_DIR / "skills-lock.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def download_file(raw_url, dest_path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(raw_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path

def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def install_skills_from_kdense():
    print("Fetching file tree for K-Dense-AI/scientific-agent-skills...")
    tree_data = fetch_json("https://api.github.com/repos/K-Dense-AI/scientific-agent-skills/git/trees/main?recursive=1")
    tree = tree_data.get("tree", [])

    target_skills = [
        "bgpt-paper-search",
        "clinical-decision-support",
        "statistical-analysis",
        "statsmodels",
        "clinical-reports",
        "exploratory-data-analysis",
        "peer-review",
    ]

    download_tasks = []
    for skill in target_skills:
        prefix = f"skills/{skill}/"
        skill_files = [x for x in tree if x["path"].startswith(prefix) and x["type"] == "blob"]
        print(f"Skill '{skill}': {len(skill_files)} files to download.")
        for item in skill_files:
            rel_path = item["path"][len(prefix):]
            dest = SKILLS_DIR / skill / rel_path
            raw_url = f"https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/{item['path']}"
            download_tasks.append((raw_url, dest))

    print(f"Total files to download from K-Dense-AI: {len(download_tasks)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_file, url, dst): dst for url, dst in download_tasks}
        for f in concurrent.futures.as_completed(futures):
            dst = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"Error downloading {dst}: {e}")

    # Return lock entries
    lock_entries = {}
    for skill in target_skills:
        skill_md = SKILLS_DIR / skill / "SKILL.md"
        if skill_md.exists():
            lock_entries[skill] = {
                "source": "K-Dense-AI/scientific-agent-skills",
                "sourceType": "github",
                "skillPath": f"skills/{skill}/SKILL.md",
                "computedHash": compute_sha256(skill_md),
            }
    return lock_entries

def install_clinicaltrials_database():
    print("Fetching file tree for google-deepmind/science-skills (clinical_trials_database)...")
    tree_data = fetch_json("https://api.github.com/repos/google-deepmind/science-skills/git/trees/main?recursive=1")
    tree = tree_data.get("tree", [])

    prefix = "skills/clinical_trials_database/"
    files = [x for x in tree if x["path"].startswith(prefix) and x["type"] == "blob"]
    print(f"clinicaltrials-database: {len(files)} files to download.")

    download_tasks = []
    # We install both as clinicaltrials-database and clinical_trials_database for complete compatibility
    for item in files:
        rel_path = item["path"][len(prefix):]
        raw_url = f"https://raw.githubusercontent.com/google-deepmind/science-skills/main/{item['path']}"
        download_tasks.append((raw_url, SKILLS_DIR / "clinicaltrials-database" / rel_path))
        download_tasks.append((raw_url, SKILLS_DIR / "clinical_trials_database" / rel_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_file, url, dst): dst for url, dst in download_tasks}
        for f in concurrent.futures.as_completed(futures):
            dst = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"Error downloading {dst}: {e}")

    lock_entries = {}
    skill_md = SKILLS_DIR / "clinicaltrials-database" / "SKILL.md"
    if skill_md.exists():
        lock_entries["clinicaltrials-database"] = {
            "source": "google-deepmind/science-skills",
            "sourceType": "github",
            "skillPath": "skills/clinical_trials_database/SKILL.md",
            "computedHash": compute_sha256(skill_md),
        }
    return lock_entries

def update_skills_lock(new_entries):
    lock_data = {"version": 1, "skills": {}}
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
        except Exception:
            pass
    if "skills" not in lock_data:
        lock_data["skills"] = {}

    for k, v in new_entries.items():
        lock_data["skills"][k] = v

    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)
    print("Updated skills-lock.json with all installed skills.")

if __name__ == "__main__":
    kdense_locks = install_skills_from_kdense()
    ct_locks = install_clinicaltrials_database()
    all_locks = {**kdense_locks, **ct_locks}
    update_skills_lock(all_locks)
    print("All skills downloaded and registered successfully!")

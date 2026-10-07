import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

API = "https://ods.od.nih.gov/api/index.aspx"

both_levels = [
    "VitaminA", "VitaminB6", "VitaminB12", "VitaminC", "VitaminD",
    "VitaminE", "VitaminK", "Folate", "Niacin", "Riboflavin", "Thiamin",
    "Choline", "Calcium", "Iron", "Magnesium", "Zinc", "Potassium",
    "Iodine", "Selenium", "Phosphorus", "Omega3FattyAcids", "Probiotics",
    "Biotin", "Copper", "Manganese", "Molybdenum", "PantothenicAcid",
    "Fluoride", "MVMS",
]
consumer_only = [
    "WYNTK", "ExerciseAndAthleticPerformance", "ImmuneFunction", "WeightLoss",
]

jobs = []
for t in both_levels:
    jobs.append((t, "Consumer", "Consumer"))
    jobs.append((t, "Health Professional", "HealthProfessional"))
for t in consumer_only:
    jobs.append((t, "Consumer", "Consumer"))

docs = Path("docs")
docs.mkdir(exist_ok=True)
for old in docs.glob("*.txt"):
    old.unlink()  # clear the old files so nothing is duplicated

for topic, level, slug in jobs:
    params = {"resourcename": topic, "readinglevel": level, "outputformat": "HTML"}
    r = requests.get(
        API,
        params=params,
        timeout=30,
        headers={"User-Agent": "nutrition-rag-portfolio-project"},
    )
    if r.status_code != 200:
        print("skipped", topic, level, r.status_code)
        continue
    text = BeautifulSoup(r.text, "html.parser").get_text("\n", strip=True)
    lines = [line for line in text.split("\n") if line]
    # drop the long reference list at the end of health-professional sheets
    if "References" in lines:
        idx = len(lines) - 1 - lines[::-1].index("References")
        if idx > len(lines) * 0.5:
            lines = lines[:idx]
    text = "\n".join(lines)
    if len(text) < 500:
        print("skipped (too short)", topic, level)
        continue
    (docs / f"{topic}-{slug}.txt").write_text(
        f"Source: NIH Office of Dietary Supplements, {topic} fact sheet ({level})\n\n{text}"
    )
    print("saved", topic, level, len(text))
    time.sleep(1)
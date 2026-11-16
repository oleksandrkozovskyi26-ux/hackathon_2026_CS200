import csv
import io
import requests
import json
from datetime import datetime, timedelta

url = "https://docs.google.com/spreadsheets/d/1xgWN3W8c6NUjePQub5r5-Ilfxfhsw9TzAqBh-WDuGtQ/export?format=csv&gid=0"
response = requests.get(url)
response.raise_for_status()
response.encoding = "utf-8"
reader = csv.reader(io.StringIO(response.text))

raw_dict = {}
for row in reader:
    if row[0] == "Прізвище":
        continue
    raw_dict[row[0]] = row[1:]

done_dict = {}
for key, value in raw_dict.items():
    for i in value:
        dates = [(datetime.strptime(i, "%d.%m.%Y").date() + timedelta(days=d)).strftime("%d.%m.%Y") for d in range(3)]
        done_dict.setdefault(key, []).extend(dates)

with open("api_to_json_cherguvania.json", "w", encoding="utf-8") as f:
    json.dump(done_dict, f, ensure_ascii=False, indent=2)
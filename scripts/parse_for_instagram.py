import json
from typing import List
from dto.Model import IgRecord as ImageRecord
from pathlib import Path
import os
from termcolor import colored
from tqdm import tqdm

base_dir = Path(__file__).resolve().parents[1]
file_path = base_dir / "downloads" / "json" / "data.json"
save_data_file = base_dir / "downloads" / "json" / "instagram.json"


def parse() -> List[ImageRecord]:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            records = []
            for record in tqdm(data, desc="Parsing Data"):
                _id = record.get('id')
                image_link = record.get('image_link')
                if _id and image_link:
                    records.append(ImageRecord(id=_id, image_link=image_link))
            return records
    except Exception as e:
        print(f"An error occurred while parsing the JSON file: {e}")
        return []


def filter_instagram_urls(data: List[ImageRecord]) -> List[ImageRecord]:
    return [record for record in tqdm(data, desc="Filtering Instagram URLs") if
            record.is_instagram_url(record.image_link)]


def write_to_file(data: List[ImageRecord]) -> bool:
    os.makedirs(os.path.dirname(save_data_file), exist_ok=True)
    with open(save_data_file, 'w') as f:
        json.dump([record.dict() for record in data], f, indent=4)

    return True

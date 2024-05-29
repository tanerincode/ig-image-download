import json
import os
from typing import List
from airtable import Airtable
from termcolor import colored
from dto.Model import IgRecord as ImageRecord


class ATDownloader:
    def __init__(self, api_key, base_id, table_name, file_path) -> None:
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name
        self.airtable = Airtable(self.base_id, api_key=self.api_key)
        self.file_path = file_path

    def connect_airtable(self):
        return self.airtable

    def fetch_airtable_data(self, table, filter_column, page_size, max_items) -> List[ImageRecord]:
        formula = f"NOT({{{filter_column}}} = '')" if filter_column else None
        fields = ["Id"]
        if filter_column and filter_column not in fields:
            fields.append(filter_column)

        records = []
        total_fetched = 0
        for record in self.airtable.iterate(table_name=table, batch_size=page_size, filter_by_formula=formula,
                                            fields=fields):
            records.append(record)
            total_fetched += 1
            if max_items != -1 and total_fetched >= max_items:
                break

        return [ImageRecord(id=record["id"], image_link=record["fields"].get(filter_column, "")) for record in records]

    def write_to_file(self, data: List[ImageRecord]):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if os.path.exists(self.file_path):
            confirmation = input(colored("File already exists. Do you want to overwrite it? (y/n): ", 'yellow'))
            if confirmation.lower() != 'y':
                return

        with open(self.file_path, 'w') as f:
            json.dump([record.dict() for record in data], f, indent=4)

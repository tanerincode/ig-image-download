import os
import time
import requests
import asyncio
import json
import logging
from termcolor import colored
import argparse
from transitions import Machine
from dotenv import load_dotenv
from pathlib import Path
from services.at_downloader import ATDownloader
from tqdm import tqdm
from scripts.parse_for_instagram import parse, filter_instagram_urls, write_to_file
from services.image_service import ImageService
from dto.Model import IgRecord

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='syncer.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')


class AutomatedSyncer:
    states = ['start', 'downloading_data', 'parsing_data', 'downloading_images', 'pushing_images', 'end']

    def __init__(self):
        self.downloaded_images = None
        self.filtered_records = None
        self.raw_data = {}
        self.machine = Machine(model=self, states=AutomatedSyncer.states, initial='start')
        self.machine.add_transition('start_sync', 'start', 'downloading_data', after='on_downloading_data')
        self.machine.add_transition('parse_data', 'downloading_data', 'parsing_data', after='on_parsing_data')
        self.machine.add_transition('download_images', 'parsing_data', 'downloading_images',
                                    after='on_downloading_images')
        self.machine.add_transition('push_images', 'downloading_images', 'pushing_images', after='on_pushing_images')
        self.machine.add_transition('finish', 'pushing_images', 'end', after='on_end')

    def start_sync(self):
        print(colored('Starting the automated syncer', 'green'))
        self.trigger('start_sync')

    def on_downloading_data(self):
        print(colored('Downloading data', 'green'))
        base_dir = Path(__file__).resolve().parents[1]
        file_path = base_dir / "downloads" / "json" / "data.json"
        api_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        table_name = os.getenv("AIRTABLE_TABLE_NAME")

        airtable_downloader = ATDownloader(
            api_key=api_key,
            base_id=base_id,
            table_name=table_name,
            file_path=file_path
        )

        # Fetch data with progress bar
        with tqdm(total=int(os.getenv("MAX_ITEMS", 20000)), desc="Fetching Data") as pbar:
            data = airtable_downloader.fetch_airtable_data(
                table=table_name,
                filter_column="Image Link",
                page_size=int(os.getenv("PAGE_SIZE", 100)),
                max_items=int(os.getenv("MAX_ITEMS", 20000))
            )
            pbar.update(len(data))

        airtable_downloader.write_to_file(data)
        self.trigger('parse_data')

    def on_parsing_data(self):
        print(colored('Parsing data', 'green'))
        records = parse()

        # Progress bar for filtering records
        with tqdm(total=len(records), desc="Filtering Instagram URLs") as pbar:
            filtered_records = []
            for record in records:
                if record.is_instagram_url(record.image_link):
                    filtered_records.append(record)
                pbar.update(1)

        write_to_file(filtered_records)
        self.filtered_records = filtered_records
        self.trigger('download_images')

    def on_downloading_images(self):
        image_service = ImageService(self.filtered_records)
        downloaded_images = image_service.process()
        self.downloaded_images = downloaded_images
        self.trigger('push_images')

    def on_pushing_images(self):
        print(colored('Pushing images to platform', 'green'))
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {os.getenv("AUTHORIZATION_TOKEN")}'
        }
        url = "https://api.dev.gastromind.co/api/v1/products/update_asset/"

        success = True

        with tqdm(total=len(self.downloaded_images), desc="Pushing Images", ncols=100,
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}') as pbar:
            for downloaded_image in self.downloaded_images:
                jsonData = json.dumps(downloaded_image, indent=4)
                response = requests.post(url=url, headers=header, data=jsonData)
                if response.status_code != 200:
                    logging.error(f"Error pushing data to platform: {downloaded_image}")
                    logging.error(response.text)
                    pbar.set_postfix(status='X')  # Show failure indicator
                    success = False
                else:
                    pbar.set_postfix(status='✓')  # Show success indicator
                pbar.update(1)

        if not success:
            print(colored('Some images failed to push.', 'red'))

        self.trigger('finish')

    def on_end(self):
        print(colored('Automated syncer has finished', 'green'))

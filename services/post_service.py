import shutil
import os
import zipfile
from datetime import datetime
import uuid
from pathlib import Path
from pkg.instaloader_4 import instaloader
import contextlib
from typing import List
from dto.Model import IgRecord
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

max_image_download_limit = os.getenv("DOWNLOAD_IMAGE_LIMIT", 50) or 50
server_host = os.getenv("SERVER_HOST", "localhost:8000") or "localhost:8000"


class PostService:
    def __init__(self, items: List[IgRecord]):
        self.items = items
        self.shortCodeList = {}
        self.base_dir = Path(__file__).resolve().parents[1]

    def process(self):
        for item in self.items:
            shortcode = item.image_link.split("/")[-2]
            self.shortCodeList[item.id] = shortcode
        return self.parse()

    def parse(self):
        if len(self.shortCodeList) > int(max_image_download_limit):
            raise ValueError(f"Exceeded the maximum limit of {max_image_download_limit} images")

        posts_dir_path = self.base_dir / "downloads" / "posts"
        posts_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate a unique zip filename using UUID
        zip_filename = f"{uuid.uuid4()}.zip"
        zip_path = posts_dir_path.parent / zip_filename

        # Check for existing post folders before downloading
        for recordID, shortcode in self.shortCodeList.items():
            shortcode_dir = posts_dir_path / shortcode
            if not shortcode_dir.exists():
                # If the shortcode directory doesn't exist, download the post
                self.download_post(shortcode, recordID)

        # Create the zip file containing the entire 'posts' folder
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for root, _, files in os.walk(posts_dir_path):
                for file in files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(posts_dir_path))

        return f"http://{server_host}/downloads/{zip_filename}"

    def download_post(self, shortcode: str, recordID: str):
        directory = self.base_dir / 'downloads' / 'posts' / recordID
        directory.mkdir(parents=True, exist_ok=True)

        try:
            # Temporarily remove the contextlib redirect to see the errors
            L = instaloader.Instaloader()

            # Load the post using the shortcode
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            # Download and save the post
            L.download_post(post, target=directory)

            return True
        except Exception as e:
            # Provide more detailed information on the error
            print(f"An error occurred while downloading post {recordID} with shortcode {shortcode}: {e}")
            return False

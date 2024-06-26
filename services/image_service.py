import logging
import os
from dto.Model import IgRecord
from typing import List
from urllib.parse import urlparse, parse_qs
from pkg.instaloader_4 import instaloader
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

max_image_download_limit = int(os.getenv("DOWNLOAD_IMAGE_LIMIT", 50))
server_host = os.getenv("SERVER_HOST", "localhost")

# Configure logging
logging.basicConfig(filename='syncer.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Configure logging
logging.basicConfig(filename='syncer.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')


class ImageService:
    def __init__(self, items: List[IgRecord]):
        self.items = items
        self.shortCodeList = {}
        self.base_dir = Path(__file__).resolve().parents[1]

    def process(self):
        for item in self.items:
            parsed_url = urlparse(item.image_link)
            query_params = parse_qs(parsed_url.query)
            img_index = query_params.get('img_index', [None])[0]
            shortcode = item.image_link.split("/")[-2]
            self.shortCodeList[item.id] = {'shortcode': shortcode, 'img_index': img_index}
        return self.parse()

    def parse(self):
        recordList = []
        with tqdm(total=len(self.shortCodeList), desc="Downloading Images") as pbar:
            for recordID, record in self.shortCodeList.items():
                shortcode = record['shortcode']
                img_index = record['img_index']
                recordList.append(self.download_image(shortcode, recordID, img_index))
                pbar.update(1)
        return recordList

    def download_image(self, shortcode: str, recordID: str, img_index: int = None):
        image_dir = self.base_dir / "downloads" / "images" / shortcode
        image_file = image_dir / f"{shortcode}.jpg"

        if image_file.exists():
            return {"asset_file_url": f"http://{server_host}/downloads/images/{shortcode}/{shortcode}.jpg",
                    "external_id": recordID}

        os.makedirs(image_dir, exist_ok=True)

        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        filename = f"{shortcode}"

        if img_index is not None and post.typename == "GraphSidecar":
            nodes = list(post.get_sidecar_nodes())
            img_index = int(img_index)
            if img_index <= len(nodes):
                node = nodes[img_index - 1]
                filename = f"{shortcode}_{img_index}"
                L.download_pic(filename=str(image_dir / filename), url=node.display_url, mtime=post.date_local)
            else:
                raise ValueError(f"Invalid img_index {img_index} for post with shortcode {shortcode}")
        else:
            L.download_pic(filename=str(image_dir / filename), url=post.url, mtime=post.date_local)

        imageURL = f"http://{server_host}/downloads/images/{shortcode}/{filename}"
        return {"asset_file_url": imageURL, "external_id": recordID}

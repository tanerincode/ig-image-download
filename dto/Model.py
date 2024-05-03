import re

import json
from typing import List
from pydantic import BaseModel


class IgRecord(BaseModel):
    id: str
    image_link: str

    def __repr__(self) -> str:
        return f"ImageRecord(id='{self.id}', image_link='{self.image_link}')"

    def is_instagram_story_url(self, url: str) -> bool:
        story_pattern = r'https?://(www\.)?instagram\.com/(stories|highlights)/.*'
        return bool(re.match(story_pattern, url))

    def is_instagram_url(self, url: str) -> bool:
        pattern = r'(https?:\/\/)?(www\.)?instagram\.com\/.*'
        if (not self.is_instagram_story_url(url)
                and bool(re.match(pattern, url)) and self.has_img_index_greater_than_one(url)):
            return True

    def has_img_index_greater_than_one(self, url: str) -> bool:
        match = re.search(r'img_index=(\d+)', url)
        if match:
            img_index_value = int(match.group(1))
            return img_index_value > 1
        return False

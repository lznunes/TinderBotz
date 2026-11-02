import string
import random
import os
import json
import time

import urllib.request
from PIL import Image
import hashlib
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse


class StorageHelper:

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    # Returns hash value of the image saved by the url given
    @staticmethod
    def store_image_as(url, directory, amount_of_attempts=1):
        destination = Path(directory)
        destination.mkdir(parents=True, exist_ok=True)
        extension = Path(urlparse(url).path).suffix.lower()
        if extension not in {".jpg", ".webp"}:
            print("URL DOES NOT CONTAIN .JPG OR .WEBP EXTENSION: {}".format(url))
            return None

        headers = {"User-Agent": "Mozilla/5.0", "Accept": "image/*"}
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(amount_of_attempts, 21):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = response.read()
                break
            except (OSError, URLError) as error:
                if attempt == 20:
                    print("Amount of attempts exceeded in storage_helper: {}".format(error))
                    return None
                sleepy_time = attempt * 30
                print("Attempt number {}: sleeping for {} seconds ...".format(attempt, sleepy_time))
                time.sleep(sleepy_time)
        else:
            return None

        # Decode in memory so downloads do not share temporary filenames.
        with Image.open(BytesIO(payload)) as source:
            if extension == ".webp":
                image = source.convert("RGB")
            else:
                image = source.copy()
        with image:
            hashvalue = hashlib.md5(image.tobytes()).hexdigest()
            filepath = destination / "{}.jpg".format(hashvalue)
            if not filepath.is_file():
                if extension == ".jpg":
                    filepath.write_bytes(payload)
                else:
                    image.save(filepath, "JPEG")

        print("Image saved as {}".format(filepath))
        return hashvalue

    @staticmethod
    def store_match(match, directory, filename):

        if not os.path.exists(directory):
            os.makedirs(directory)

        filepath = directory + "/{}.json".format(filename)

        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}

        data[match.get_id()] = match.get_dictionary()

        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file)

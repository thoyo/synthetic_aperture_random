import time
from datetime import datetime, timedelta
import urllib.request
import uuid
import os
import argparse
import logging

import schedule
import numpy as np
import ee
from twython import Twython
from dotenv import load_dotenv
import reverse_geocode

S1 = "COPERNICUS/S1_GRD"
INSTRUMENT_MODE = "IW"
RESOLUTION = 10
DAYS_INTERVAL = 2
IMAGE_MAX_PX = 1000
POST_TIME = "15:00"
DESTINATION_FOLDER = "images"

load_dotenv()
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")
OAUTH_TOKEN_SECRET = os.getenv("OAUTH_TOKEN_SECRET")

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")


def format_timestamp(datetime_object):
    return datetime_object.strftime("%Y-%m-%d")


def get_bands_info(image):
    copol_band = ""
    crosspol_band = ""
    bands = []
    for band in image.getInfo()["bands"]:
        id = band["id"]
        bands.append(id)
        if id in ["VV", "HH"]:
            copol_band = id
        elif id in ["VH", "HV"]:
            crosspol_band = id
    if copol_band == "" or crosspol_band == "":
        bands_str = ", ".join(bands)
        raise NameError(f"Bands in image [{bands_str}] not correct")
    return copol_band, crosspol_band


def generate_pseudocolor(image, copol_band, crosspol_band):
    # VV, 2VH, VV / VH / 100.0
    copol = image.select(copol_band)
    crosspol = image.select(crosspol_band)

    red = copol.rename("red")
    green = ee.Image(2).multiply(crosspol).rename("green")
    blue = copol.divide(crosspol).divide(ee.Image(100)).rename("blue")

    image_pseudocolor = red
    image_pseudocolor = image_pseudocolor.addBands(green)
    image_pseudocolor = image_pseudocolor.addBands(blue)

    return image_pseudocolor


def get_image_info(image, copol_band, crosspol_band):
    full_info = image.getInfo()
    epoch = int(full_info["properties"]["system:time_start"]) / 1e3
    timestamp = datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")

    coordinates = np.array(full_info["properties"]["system:footprint"]["coordinates"])
    mean_coordinates = [(np.mean(coordinates[:, 1]), np.mean(coordinates[:, 0]))]
    location = reverse_geocode.search(mean_coordinates)

    orbit_type = full_info["properties"]["orbitProperties_pass"]
    orbit_type = orbit_type[0] + orbit_type[1:].lower()

    # TODO: get info about location using google maps reverse api
    # TODO: get link to download original sar image
    # TODO: get info about weather conditions when image acquired (cloudy, suny, ...)
    # TODO: get info on if image was acquired at day or night

    info = f"{location[0]['country']}, {location[0]['city']} " \
           f"({mean_coordinates[0][1]:.6f}, {mean_coordinates[0][0]:.6f})\n" \
           f"{timestamp} UTC\n" \
           f"{orbit_type} orbit\n" \
           f"{copol_band}, {crosspol_band} polarizations"

    return info


def find_image(datetime_ini, datetime_fin):
    image_collection = ee.ImageCollection(S1)
    image_collection = image_collection.filter(ee.Filter.eq("instrumentMode", INSTRUMENT_MODE))
    image_collection = image_collection.filter(ee.Filter.eq("resolution_meters", RESOLUTION))
    image_collection = image_collection.filterDate(datetime_ini, datetime_fin)

    n_images = image_collection.size().getInfo()
    if n_images > 0:
        logging.info(f"{n_images} images found")
        image_list = image_collection.toList(n_images)
        idx = int(np.random.uniform(0, n_images - 1))
        logging.info(f"Image {idx} in the stack selected")
        image = ee.Image(image_list.get(idx))
        return image
    else:
        logging.error("Couldn't find image in interval [" + datetime_ini + ", " + datetime_fin + "]")
        return None


def db_to_i(image):
    # TODO: add test to check that mean value of input is mean value of output in dBs
    return ee.Image(10).pow(image.divide(ee.Image(10)))


def generate_url(image):
    return image.getThumbUrl(params={"bands": "red,green,blue", "dimensions": IMAGE_MAX_PX, "format": "jpg"})


def download_image(url, destination):
    urllib.request.urlretrieve(url, destination)


def post_image(image_file, info):
    photo = open(image_file, "rb")
    twitter = Twython(APP_KEY, APP_SECRET,
                      OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    response = twitter.upload_media(media=photo)
    twitter.update_status(status=info, media_ids=[response["media_id"]])


def job(test):
    logging.info("Starting job")
    now = datetime.now()
    before = now - timedelta(days=DAYS_INTERVAL)
    image = find_image(format_timestamp(before), format_timestamp(now))
    if image:
        copol_band, crosspol_band = get_bands_info(image)
        info = get_image_info(image, copol_band, crosspol_band)
        logging.info(f"Image info: \n{info}")
        image_i = db_to_i(image)
        image_pseudocolor = generate_pseudocolor(image_i, copol_band, crosspol_band)
        url = generate_url(image_pseudocolor)
        image_file = f"{DESTINATION_FOLDER}/{str(uuid.uuid4())}.jpg"
        logging.info(f"Downloading image to file {image_file}")
        download_image(url, image_file)
        logging.info(f"Image downloaded")
        if test:
            logging.info("This is a test, image won't be posted")
        else:
            logging.info("Posting image")
            post_image(image_file, info)
            logging.info("Image posted!")


if __name__ == "__main__":
    logging.info("Initializing GEE")
    ee.Initialize()
    logging.info("GEE initialized")

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", dest="manual", action="store_true")
    parser.add_argument("--automatic", dest="manual", action="store_false")
    parser.add_argument("--test", dest="test", action="store_true")
    parser.set_defaults(manual=True)
    parser.set_defaults(test=False)
    args = parser.parse_args()

    if not os.path.exists(DESTINATION_FOLDER):
        os.makedirs(DESTINATION_FOLDER)

    if args.manual:
        logging.info("Manual mode selected, an image will be posted now!")
        job(args.test)
    else:
        logging.info(f"Automatic mode selected, an image will be posted at {POST_TIME}")
        schedule.every().day.at(POST_TIME).do(job, args.test)
        while True:
            schedule.run_pending()
            time.sleep(60)  # wait one minute

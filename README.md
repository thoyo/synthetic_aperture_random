# Synthetic Aperture Random

This is the Python code behind the Twitter bot [@ApertureRandom](https://twitter.com/ApertureRandom), that posts every day a new Synthetic Aperture Radar image acquired with European Space Agencies's Sentinel-1 satellites. 

The images are obtained using [Google Earth Engine](https://earthengine.google.com/) (GEE).

## Requirements

* Access to GEE (can be requested [here](https://signup.earthengine.google.com))
* A Twitter developer account and the corresponding APP Key and APP Secret (apply [here](https://developer.twitter.com/en/apply))
* Python > 3.6 
* Virtualenv
* Pip

## Functioning
Using Python's [Schedule](https://pypi.org/project/schedule/) library, every day at a given time (default is 15:00) a new job 
is launched. This job retrieves all Ground Range Detected (GRD) images from GEE fulfilling the following criteria:
* Sensor: Sentinel-1
* Mode: Interferometric Wide Swath (the default mode for this satellite, for more info see the 
[User Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-1-sar/acquisition-modes/interferometric-wide-swath))
* Pixel resolution: 10x10m (the highest available)
* Acquisition time: not older than the last 2 days

Among the many retrieved images, the program picks one randomly. Its radiometric copol (either HH or VV) and crosspol 
(either HV or VH) bands are converted to RGB pseudo-colors using the following mapping:
* Red = Copol
* Green = 2 * Crosspol
* Blue = Copol / Crosspol / 100

The following information from the image is retrieved:
* Nearest city and country (using Python's [reverse_geocode](https://pypi.org/project/reverse_geocode/) library
* Coordinates
* Acquisition date and time
* Orbit type (ascending or descending)
* Polarizations

Then, the image is generated, downloaded and uploaded to Twitter.

## Usage
Generate a file called `.env` in the directory `synthetic_aperture_random/` with the following structure:
```
APP_KEY=<APP_KEY>
APP_SECRET=<APP_SECRET>
OAUTH_TOKEN=<OAUTH_TOKEN>
OAUTH_TOKEN_SECRET=<OAUTH_TOKEN_SECRET>
```
and replace the values in <> with your Twitter Developer's credentials. APP_KEY and APP_SECRET can be obtained from the web.
I generated the OAUTH tokens using the `scripts/twitter_auth.py` also provided in this repo, which requires the user to open 
a browser window in order to obtain an authentication pin.

You also need to authenticate your GEE account:
```
$ earthengine authenticate
```

### Using a Python virtual environment

Installation:
```
$ virtualenv -p python3.6 _env
$ source _env/bin/activate
(env_) $ pip install -r requirements/requirements.txt
```
Show the help:
```
(env_) $ python main.py -h
```
Running it manually (default):
```
(env_) $ python main.py --manual
```
Leaving it running in automatic mode in a server:
```
$ nohup python main.py --automatic &
```

### Using Docker

Build the image:
```
$ docker build -t thoyo/synthetic_aperture_random:1.0.0 .
```

Run it:
```
$ docker-compose -p twitter up -d
```
Check the logs:
```
docker logs -f twitter_synthetic_aperture_random_1
```

## TODO
* Add unit testing
* Allow user retrieving the full resolution image (upload it to drive and provide link in status?)

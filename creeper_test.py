import logging
import os
import random

from image_parser.image_parser import ImageParser
from laserdock.laserdock import LaserDock

logger = logging.getLogger(__name__)

random.seed('my_test!')
img = os.path.join('img', 'CreeperGrayscaleTest.png')


if __name__ == '__main__':
    parser = ImageParser(img_to_burn=img)

    dock = LaserDock()
    samples_for_burning = parser.make_samples()
    starting_sample = 0
    while True:
        dock.burn_samples(starting_sample, samples_for_burning)

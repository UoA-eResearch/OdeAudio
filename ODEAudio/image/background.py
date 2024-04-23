from os import path

from PIL import Image

from root import ROOT_DIR
from ODEAudio.utility.lerps import range_map


def get_image(aLim, bLim):
    """Loads background image, cropped and scaled to matche GUI"""
    image_aLim = (0., 2.)
    image_bLim = (0., 4.5)

    im_path = path.join(ROOT_DIR, 'data', 'ODEAudioBG.png')

    with Image.open(im_path) as im:
        w, h = im.size

        l, r = range_map(*image_aLim, 0, w, aLim)
        b, t = range_map(*image_bLim, h, 0, bLim)

        im_crop = im.crop((l, t, r, b))

        return im_crop

from PIL import Image, ImageDraw


def to_laserdock_coord(val1, val2=None):
    """
    Convert a value -1 to 1 to a LaserDock position value in range 0-4906
    Returns a single value if val2 is None, otherwise returns a tuple
    """
    if val2 is not None:
        return (int(4095 * (val1 + 1) / 2), int(4095 * (val2 + 1) / 2))
    return int(4095 * (val1 + 1) / 2)


def packet_to_image(filename, packet_samples):
    """
    Save a packet of samples to an image file
    """
    # if image exists, load it, otherwise create a new one
    try:
        im = Image.open(filename)
    except IOError:
        im = Image.new('RGB', (4096, 4096), 'white')

    # img = Image.new('RGB', (4096, 4096), 'white')
    draw = ImageDraw.Draw(im)
    # pixels = img.load()
    for sample in packet_samples:
        x = sample['x']
        y = sample['y']
        r = sample['r']
        g = sample['g']
        b = sample['b']
        print(x, y, r, g, b)
        # pixels[x, y] = (r, g, b)
        draw.ellipse((x - 50, y - 50, x + 50, y + 50), fill='red')
    im.save(filename)

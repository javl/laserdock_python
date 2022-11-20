def float_to_laserdock_xy(val):
    """
    Convert a float from -1 to 1 to a LaserDock XY value of 0 to 4906
    """
    return int(4095 * (val + 1) / 2)

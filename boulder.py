from numpy import zeros

def combine_plume_images(c1, c2, scale = 1):
    # Combines 2D plume concentrations c1 and c2
    # into RGB values using the Boulder approach.

    assert c1.shape == c2.shape, f"Shape mismatch: {c1.shape=} != {c2.shape}"
    assert len(c1.shape) == 2, f"Data must be 2D, but {c1.shape=}."

    c1[c1>1] = 1
    c1[c1<0] = 0
    c2[c2>1] = 1
    c2[c2<0] = 0

    c1 = c1 ** scale
    c2 = c2 ** scale

    nx, ny = c1.shape

    rgb = zeros((nx, ny, 3))

    rgb[:,:,0] = 1 - c2
    rgb[:,:,2] = 1 - c1
    rgb[:,:,1] = 1 - (c1 + c2)
    rgb[rgb>1] = 1
    rgb[rgb<0] = 0

    return rgb
    

""" Configuration data for sprites """
SPRITES_PATH = __file__[:__file__.rfind('/') + 1]
SPRITES_DATA = {
    'base_image'     : SPRITES_PATH + 'base.bmp',

    'eyes_image'     : SPRITES_PATH + 'eyes.bmp',

    'mouth_image'    : SPRITES_PATH + 'mouth.bmp',

    'exp_image'      : SPRITES_PATH + 'exp.bmp',

    'test_layer'     : SPRITES_PATH + 'test.bmp',

    'error_layer'    : SPRITES_PATH + 'dead.bmp',

    'transparent'    : (255, 0, 255), # Transparent color (decimal values) in above images

    'eyes'           : (0, 0),

    'mouth'          : (0, 0),

    'exp'            : (0, 32)
}

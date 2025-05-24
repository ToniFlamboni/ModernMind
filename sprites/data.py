""" Configuration data for sprites """
SPRITES_PATH = __file__[:__file__.rfind('/') + 1]
SPRITES_DATA = {
    'base_image'            : SPRITES_PATH + 'base.bmp',

    'eyes_neutral'          : SPRITES_PATH + 'facesets/eyes_neutral.bmp',

    'eyes_tired'            : SPRITES_PATH + 'facesets/eyes_tired.bmp',

    'eyes_indifferent'      : SPRITES_PATH + 'facesets/eyes_indifferent.bmp',

    'mouth_neutral'         : SPRITES_PATH + 'facesets/mouth_neutral.bmp',

    'mouth_tired'           : SPRITES_PATH + 'facesets/mouth_neutral.bmp',

    'mouth_indifferent'     : SPRITES_PATH + 'facesets/mouth_neutral.bmp',

    'exp_image'             : SPRITES_PATH + 'exp/exp.bmp',

    'text_exp_smug'         : SPRITES_PATH + 'text-exp/text-exp-smug.bmp',

    'text_exp_happy'        : SPRITES_PATH + 'text-exp/text-exp-happy.bmp',

    'text_exp_sad'          : SPRITES_PATH + 'text-exp/text-exp-sad.bmp',

    'text_exp_dead'         : SPRITES_PATH + 'text-exp/text-exp-smug.bmp',

    'boot_image'            : SPRITES_PATH + 'boot.bmp',

    'test_layer'            : SPRITES_PATH + 'exp/test.bmp',

    'error_layer'           : SPRITES_PATH + 'exp/dead.bmp',

    'exp_balatro'           : SPRITES_PATH + 'exp/balatro.bmp',

    'exp_p03'               : SPRITES_PATH + 'exp/p03_a.bmp',

    'exp_drone'             : SPRITES_PATH + 'exp/drone.bmp',

    'exp_lowpwr'            : SPRITES_PATH + 'exp/lowpower.bmp',

    'exp_sleepy'            : SPRITES_PATH + 'exp/sleepy.bmp',

    'transparent'    : (255, 0, 255), # Transparent color (decimal values) in above images

    'eyes'           : (0, 0),

    'mouth'          : (0, 0),

    'text-exp'       : (0, 0),

    'exp'            : (0, 32)
}

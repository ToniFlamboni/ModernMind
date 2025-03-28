import random
import time
from os import getenv
import board
import displayio
import adafruit_imageload
import busio
import adafruit_lis3dh
from analogio import AnalogIn
from adafruit_matrixportal.matrix import Matrix
from sprites.data import SPRITES_DATA

import wifi
import adafruit_connection_manager
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# UTILITY FUNCTIONS AND CLASSES --------------------------------------------

class Sprite(displayio.TileGrid):
    def __init__(self, filename, transparent=None):
        bitmap, palette = adafruit_imageload.load(
            filename, bitmap=displayio.Bitmap, palette=displayio.Palette)
        if isinstance(transparent, (tuple, list)):
            closest_distance = 0x1000000
            for color_index, color in enumerate(palette):
                delta = (transparent[0] - ((color >> 16) & 0xFF),
                         transparent[1] - ((color >> 8) & 0xFF),
                         transparent[2] - (color & 0xFF))
                rgb_distance = (delta[0] * delta[0] +
                                delta[1] * delta[1] +
                                delta[2] * delta[2])
                if rgb_distance < closest_distance:
                    closest_distance = rgb_distance
                    closest_index = color_index
            palette.make_transparent(closest_index)
        elif isinstance(transparent, int):
            palette.make_transparent(transparent)
        super(Sprite, self).__init__(bitmap, pixel_shader=palette)

def ioConnect(client):
    io.subscribe(feed_key = 'modernmind')
    # Used to connect/reconnect with AdafruitIO. Gets called initially, and called again if a disconnect happens.


def disconnect(client):
    # This is more for error checking. If the client disconnects, the face should change to reflect an error!
    pass

def ioMessageDecode(client, feed_id, payload):
    if payload == "ON":
        SPRITES.append(Sprite(SPRITES_DATA['test_layer']))
    if payload == "OFF":
        SPRITES.pop(-1)
    # I think this might contain all the logic for face changes and stuff. I think?


# SET UP
MATRIX = Matrix(bit_depth=6)
DISPLAY = MATRIX.display

# Order in which sprites are added determines the layer order
SPRITES = displayio.Group() ## The main canvas is a 'Group'. what tf is that?? Maybe not necessary to understand
SPRITES.append(Sprite(SPRITES_DATA['base_image'])) #Keep opaque
SPRITES.append(Sprite(SPRITES_DATA['eyes_image'], SPRITES_DATA['transparent']))
SPRITES.append(Sprite(SPRITES_DATA['mouth_image'], SPRITES_DATA['transparent']))
SPRITES.append(Sprite(SPRITES_DATA['exp_image'], SPRITES_DATA['transparent'])) #Keep opaque
# SPRITES.append(Sprite(SPRITES_DATA['test_layer'], SPRITES_DATA['transparent'])) #Keep opaque
# An additional layer would go here, presumably the text layer.
### Add more layers here, if desired. General setup here.

DISPLAY.show(SPRITES)

MOVE_STATE = False                                     # Initially stationary
MOVE_EVENT_DURATION = random.uniform(0.1, 3)           # Time to first move
BLINK_STATE = 2                                        # Start eyes closed
BLINK_EVENT_DURATION = random.uniform(0.25, 0.5)       # Time for eyes to open
EXP_EVENT_DURATION = 1                                 # Time for expression to last
TIME_OF_LAST_TAP_EVENT = TIME_OF_LAST_EXP_EVENT = TIME_OF_LAST_BLINK_EVENT = time.monotonic()

EXP_STATE = 0                                          # Expression neutral   ## NEUTRAL???
EXP_TYPE = 0                                           # Expression type

MOUTH_TYPE = 0  ## mouth type???

WIDTH = 64
HEIGHT = 32  ## Change depending on what LCD I get

FRAMES_HOLD = 9                                       # Animation frame speed

COUNTDOWN = FRAMES_HOLD

# Audio set up
sampleWindow = 0.033  # Sample window width (0.033 sec = 33 mS = ~30 Hz)
dc_offset = 0  # DC offset in mic signal - if unusure, leave 0
noise = 100  # Noise/hum/interference in mic signal

mic_pin = board.A1
mic = AnalogIn(mic_pin)  # Getting the audio value

# PyGamer OR MatrixPortal I2C Setup:
i2c = busio.I2C(board.SCL, board.SDA)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)

# Set range of accelerometer (can be RANGE_2_G, RANGE_4_G, RANGE_8_G or RANGE_16_G).
lis3dh.range = adafruit_lis3dh.RANGE_2_G

# WIFI SETUP

# Grab credentials from env
ssid = getenv('SSID')
wifi_password = getenv('PASSWORD')
username = getenv('USERNAME')
aioKey = getenv('AIO_KEY')

# Establish WiFi Connection
wifi.radio.connect(ssid, wifi_password)

# Websocket and ssl_context
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

# Creates a MQTT client
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=8883,
    username=username,
    password=wifi_password,
    socket_pool=pool,
    ssl_context=ssl_context,
    is_ssl=True,
)

# Creates a client with AdafruitIO, and connects it to their services
io = IO_MQTT(mqtt_client)
io.connect()

# Subscribes to the 'ModernMind' feed
io.subscribe(feed_key = 'modernmind')

io.on_message = ioMessageDecode

# MAIN LOOP ----------------------------------------------------------------

while True:
    # Maintains connection with IO MQTT client
    io.loop()

    NOW = time.monotonic()

    # Audio mouth syncing -------------------------------------------------------------

    # Listen to mic for short interval, recording min & max signal
    signalMin = 65535
    signalMax = 0
    while (time.monotonic() - NOW) < sampleWindow:
        signal = mic.value
        if signal < signalMin:
            signalMin = signal
        if signal > signalMax:
            signalMax = signal

    peakToPeak = signalMax - signalMin  # Audio amplitude
    MOUTH_TYPE = int(((peakToPeak - 250) * 2) / 16383)  # Remove low-level noise, boost
    if MOUTH_TYPE > 3:
        MOUTH_TYPE = 3

    # Blinking -------------------------------------------------------------
    
    if NOW - TIME_OF_LAST_BLINK_EVENT > BLINK_EVENT_DURATION:
        TIME_OF_LAST_BLINK_EVENT = NOW  # Start change in blink
        BLINK_STATE += 1                # Cycle paused/closing/opening
        if BLINK_STATE == 1:            # Starting a new blink (closing)
            BLINK_EVENT_DURATION = random.uniform(0.03, 0.07)
        elif BLINK_STATE == 2:          # Starting de-blink (opening)
            BLINK_EVENT_DURATION *= 2
        else:                           # Blink ended,
            BLINK_STATE = 0             # paused
            BLINK_EVENT_DURATION = random.uniform(BLINK_EVENT_DURATION * 3, 4)

    if BLINK_STATE:  # Currently in a blink?
        # Fraction of closing or opening elapsed (0.0 to 1.0)
        FRAME = 0  # Open eyes frame
        if BLINK_STATE == 1:
            FRAME = 3  # Closed eyes frame
        elif BLINK_STATE == 2:     # Opening
            FRAME = FRAME - 1
            if FRAME == -1:
                FRAME += 2

    else:           # Not blinking
        FRAME = 0

    # Expression Changing -------------------------------------------------------------

    # Read accelerometer values (in m / s ^ 2).  Returns a 3-tuple of x, y,
    # z axis values.  Divide them by 9.806 to convert to Gs.
    x, y, z = [
        value / adafruit_lis3dh.STANDARD_GRAVITY for value in lis3dh.acceleration
    ]

    # Expression change according to accelerometer values
    if x: ## If any X-movement at all...
        NUDGE = 0 ## nudge??
        if x > 0.4:
            TIME_OF_LAST_EXP_EVENT = NOW
            EXP_SWITCH = 1 ## A boolean noting an emotion change???
            NUDGE = 1
            EXP_STATE = 0
            COUNTDOWN = COUNTDOWN - 1
            if COUNTDOWN == FRAMES_HOLD/3*2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD/3:
                EXP_TYPE += 1
            elif COUNTDOWN == 0:
                EXP_TYPE = 3
            elif COUNTDOWN == -1:
                 COUNTDOWN += 1
        elif x < -0.4:
            TIME_OF_LAST_EXP_EVENT = NOW
            EXP_SWITCH = 1
            NUDGE = 1
            EXP_STATE = 1
            COUNTDOWN = COUNTDOWN - 1
            if COUNTDOWN == FRAMES_HOLD/3*2:
                EXP_TYPE += 1 ## The increase in EXP_TYPE are smear frames????
            elif COUNTDOWN == FRAMES_HOLD/3:
                EXP_TYPE += 1
            elif COUNTDOWN == 0:
                EXP_TYPE = 3
            elif COUNTDOWN == -1:
                 COUNTDOWN += 1
        else:
            NUDGE = NUDGE - 1
            if NUDGE == -1:
               NUDGE = 0
            if NOW - TIME_OF_LAST_EXP_EVENT > EXP_EVENT_DURATION:
                EXP_TYPE = EXP_TYPE - 1
                if EXP_TYPE == -1:
                    EXP_TYPE = 0
                    EXP_SWITCH = 0
                    COUNTDOWN = FRAMES_HOLD
    ## Seems like I can add extra emotions HERE.
    if z:
        if z > 0.4:
            TIME_OF_LAST_EXP_EVENT = NOW
            EXP_SWITCH = 1
            NUDGE = 1
            EXP_STATE = 3
            COUNTDOWN = COUNTDOWN - 1
            if COUNTDOWN == FRAMES_HOLD/3*2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD/3:
                EXP_TYPE += 1
            elif COUNTDOWN == 0:
                EXP_TYPE = 3
            elif COUNTDOWN == -1:
                 COUNTDOWN += 1
        elif z < -0.4:
            TIME_OF_LAST_EXP_EVENT = NOW
            EXP_SWITCH = 1
            NUDGE = 1
            EXP_STATE = 2
            COUNTDOWN = COUNTDOWN - 1
            if COUNTDOWN == FRAMES_HOLD/3*2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD/3:
                EXP_TYPE += 1
            elif COUNTDOWN == 0:
                EXP_TYPE = 3
            elif COUNTDOWN == -1:
                 COUNTDOWN += 1
        else:
            NUDGE = NUDGE - 1
            if NUDGE == -1:
               NUDGE = 0
            if NOW - TIME_OF_LAST_EXP_EVENT > EXP_EVENT_DURATION:
                EXP_TYPE = EXP_TYPE - 1
                if EXP_TYPE == -1:
                    EXP_TYPE = 0
                    EXP_SWITCH = 0
                    COUNTDOWN = FRAMES_HOLD

    # Then interpolate between closed position and open position
    EYES_POS = (SPRITES_DATA['eyes'][0],
                SPRITES_DATA['eyes'][1] - FRAME * HEIGHT)

    MOUTH_POS = (SPRITES_DATA['mouth'][0],
                 SPRITES_DATA['mouth'][1]- MOUTH_TYPE * HEIGHT)

    EXP_POS = (SPRITES_DATA['exp'][0] - EXP_STATE * WIDTH,
               SPRITES_DATA['exp'][1] - EXP_TYPE * HEIGHT)


    # Move sprites -----------------------------------------------------
    SPRITES[1].x, SPRITES[1].y = (int(EYES_POS[0]),
                                  int(EYES_POS[1]))
    SPRITES[2].x, SPRITES[2].y = (int(MOUTH_POS[0]),
                                  int(MOUTH_POS[1]))
    SPRITES[3].x, SPRITES[3].y = (int(EXP_POS[0]),
                                  int(EXP_POS[1]))



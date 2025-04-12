import random
import time
from os import getenv
import board
import displayio
from digitalio import DigitalInOut

import ssl
import socketpool

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
            filename, bitmap=displayio.Bitmap, palette=displayio.Palette
        )
        if isinstance(transparent, (tuple, list)):
            closest_distance = 0x1000000
            for color_index, color in enumerate(palette):
                delta = (
                    transparent[0] - ((color >> 16) & 0xFF),
                    transparent[1] - ((color >> 8) & 0xFF),
                    transparent[2] - (color & 0xFF),
                )
                rgb_distance = (
                    delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2]
                )
                if rgb_distance < closest_distance:
                    closest_distance = rgb_distance
                    closest_index = color_index
                    closest_index = color_index
                    closest_index = color_index
            palette.make_transparent(closest_index)
        elif isinstance(transparent, int):
            palette.make_transparent(transparent)
        super(Sprite, self).__init__(bitmap, pixel_shader=palette)


def ioConnect(client):
    # print("yiipeeee1!!!!!!!!!")
    io.subscribe(feed_key="modernmind")
    # Used to connect/reconnect with AdafruitIO. Gets called initially, and called again if a disconnect happens.


def disconnect(client):
    # This is more for error checking. If the client disconnects, the face should change to reflect an error!
    pass


def ioMessageDecode(client, feed_id, payload):
    if payload == "ON":
        SPRITES.append(Sprite(SPRITES_DATA["test_layer"], SPRITES_DATA["transparent"]))
        # print("Change detected! TEST SPRITE ENABLED!")
    if payload == "OFF":
        SPRITES.pop(-1)
        # print("Change detected! TEST SPRITE DISABLED.")
    # I think this might contain all the logic for face changes and stuff. I think?


# SET UP
MATRIX = Matrix(bit_depth=6)
DISPLAY = MATRIX.display

# Order in which sprites are added determines the layer order
SPRITES = displayio.Group()
SPRITES.append(Sprite(SPRITES_DATA["base_image"]))  # Keep opaque
SPRITES.append(Sprite(SPRITES_DATA["eyes_image"], SPRITES_DATA["transparent"]))
SPRITES.append(Sprite(SPRITES_DATA["mouth_image"], SPRITES_DATA["transparent"]))
SPRITES.append(
    Sprite(SPRITES_DATA["exp_image"], SPRITES_DATA["transparent"])
)  # Keep opaque
# SPRITES.append(Sprite(SPRITES_DATA['test_layer'], SPRITES_DATA['transparent'])) #Keep opaque
# An additional layer would go here, presumably the text layer.
### Add more layers here, if desired. General setup here.

DISPLAY.root_group = SPRITES

MOVE_STATE = False  # Initially stationary
MOVE_EVENT_DURATION = random.uniform(0.1, 3)  # Time to first move
BLINK_STATE = 2  # Start eyes closed
BLINK_EVENT_DURATION = random.uniform(0.25, 0.5)  # Time for eyes to open
EXP_EVENT_DURATION = 1  # Time for expression to last
TIME_OF_LAST_TAP_EVENT = (
    TIME_OF_LAST_EXP_EVENT
) = TIME_OF_LAST_BLINK_EVENT = time.monotonic()

EXP_STATE = 0  # Expression neutral   ## NEUTRAL???
EXP_TYPE = 0  # Expression type

MOUTH_TYPE = 0  ## mouth type???

WIDTH = 64
HEIGHT = 32  ## Change depending on what LCD I get

FRAMES_HOLD = 9  # Animation frame speed
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
ssid = getenv("CIRCUITPY_WIFI_SSID")
wifi_password = getenv("CIRCUITPY_WIFI_PASSWORD")
username = getenv("ADAFRUIT_AIO_USERNAME")
aioKey = getenv("ADAFRUIT_AIO_KEY")

pool = socketpool.SocketPool(wifi.radio)
socket = adafruit_connection_manager.get_radio_socketpool(wifi.radio)

# Websocket and ssl_context
context = ssl.create_default_context()


# Creates a MQTT client
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=username,
    password=aioKey,
    socket_pool=pool,
    ssl_context=context,
    is_ssl=True,
    socket_timeout = 0.2
)

# Creates a client with AdafruitIO, and connects it to their services
io = IO_MQTT(mqtt_client)
while True:
    try:
        io.connect()
    except:
        print("Connection failure!")
    else:
        break

# Subscribes to the 'ModernMind' feed
io.subscribe(feed_key="modernmind")

io.on_message = ioMessageDecode

# MAIN LOOP ----------------------------------------------------------------
loopCounter = 0

while True:

    if loopCounter == 25:
        # Maintains connection with IO MQTT client
        try:
            io.loop(timeout=0.21)
            loopCounter = 0
        except:
            print("Connection to AdafruitIO failed!")
            SPRITES.append(Sprite(SPRITES_DATA['error_layer']))
            io.connect()
            SPRITES.pop()

    loopCounter += 1
    print(loopCounter)

    # TODO: Create both an exception catcher, AND a way to reconnect without exploding!

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
        BLINK_STATE += 1  # Cycle paused/closing/opening
        if BLINK_STATE == 1:  # Starting a new blink (closing)
            BLINK_EVENT_DURATION = random.uniform(0.03, 0.07)
        elif BLINK_STATE == 2:  # Starting de-blink (opening)
            BLINK_EVENT_DURATION *= 2
        else:  # Blink ended,
            BLINK_STATE = 0  # paused
            BLINK_EVENT_DURATION = random.uniform(BLINK_EVENT_DURATION * 3, 4)

    if BLINK_STATE:  # Currently in a blink?
        # Fraction of closing or opening elapsed (0.0 to 1.0)
        FRAME = 0  # Open eyes frame
        if BLINK_STATE == 1:
            FRAME = 3  # Closed eyes frame
        elif BLINK_STATE == 2:  # Opening
            FRAME = FRAME - 1
            if FRAME == -1:
                FRAME += 2

    else:  # Not blinking
        FRAME = 0

    # Expression Changing -------------------------------------------------------------

    # Read accelerometer values (in m / s ^ 2).  Returns a 3-tuple of x, y,
    # z axis values.  Divide them by 9.806 to convert to Gs.
    x, y, z = [
        value / adafruit_lis3dh.STANDARD_GRAVITY for value in lis3dh.acceleration
    ]

    # Expression change according to accelerometer values
    if x:  ## If any X-movement at all...
        NUDGE = 0  ## nudge??
        if x > 0.4:
            TIME_OF_LAST_EXP_EVENT = NOW
            EXP_SWITCH = 1  ## A boolean noting an emotion change???
            NUDGE = 1
            EXP_STATE = 0
            COUNTDOWN = COUNTDOWN - 1
            if COUNTDOWN == FRAMES_HOLD / 3 * 2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD / 3:
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
            if COUNTDOWN == FRAMES_HOLD / 3 * 2:
                EXP_TYPE += 1  ## The increase in EXP_TYPE are smear frames????
            elif COUNTDOWN == FRAMES_HOLD / 3:
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
            if COUNTDOWN == FRAMES_HOLD / 3 * 2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD / 3:
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
            if COUNTDOWN == FRAMES_HOLD / 3 * 2:
                EXP_TYPE += 1
            elif COUNTDOWN == FRAMES_HOLD / 3:
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
    EYES_POS = (SPRITES_DATA["eyes"][0], SPRITES_DATA["eyes"][1] - FRAME * HEIGHT)

    MOUTH_POS = (
        SPRITES_DATA["mouth"][0],
        SPRITES_DATA["mouth"][1] - MOUTH_TYPE * HEIGHT,
    )

    EXP_POS = (
        SPRITES_DATA["exp"][0] - EXP_STATE * WIDTH,
        SPRITES_DATA["exp"][1] - EXP_TYPE * HEIGHT,
    )

    # Move sprites -----------------------------------------------------
    SPRITES[1].x, SPRITES[1].y = (int(EYES_POS[0]), int(EYES_POS[1]))
    SPRITES[2].x, SPRITES[2].y = (int(MOUTH_POS[0]), int(MOUTH_POS[1]))
    SPRITES[3].x, SPRITES[3].y = (int(EXP_POS[0]), int(EXP_POS[1]))

    ## Alright, here's the deal. This counter below MUST happen every loop. Only issue is, it takes a WHILE for this to process: exactly how long is seen
    ## in the timeout field. This unfortunately stalls the rest of the loop, leading to potentially janky transitions. What to do?
    ## Two options: give this a SECOND conditional on if my face is in its neutral state, or tie it to the accelerometer. I'm less privy to that approach though, given that it'd have to be a range and not just 0.
    ## The other option is to place it at the bottom of the loop. It remains to be seen if this'll work, though.


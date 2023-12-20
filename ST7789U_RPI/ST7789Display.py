import numbers
import time
import numpy

import spidev
import RPi.GPIO as GPIO

from .ST7789 import ST7789


def image_to_data(image, rotation=0):
    if not isinstance(image, numpy.ndarray):
        image = numpy.array(image.convert('RGB'))

    # Rotate the image
    pb = numpy.rot90(image, rotation // 90).astype('uint16')

    # Mask and shift the 888 RGB into 565 RGB
    red = (pb[..., [0]] & 0xf8) << 8
    green = (pb[..., [1]] & 0xfc) << 3
    blue = (pb[..., [2]] & 0xf8) >> 3

    # Stick 'em together
    result = red | green | blue

    # Output the raw bytes
    return result.byteswap().tobytes()


class ST7789Display:
    def __init__(
            self,
            port,
            dc,
            spi_mode=0,
            cs=None,
            backlight=None,
            rst=None,
            width=240,
            height=240,
            rotation=90,
            invert=True,
            spi_speed_hz=4000000,
            offset_left=0,
            offset_top=0
    ):
        """Create an instance of the display using SPI communication.

        Must provide the GPIO pin for the D/C pin and the SPI driver.

        Can optionally provide the GPIO pin for the reset pin as the rst parameter.

        :param port: SPI port number
        :param cs: SPI chip-select number (0 or 1) for BCM
        :param backlight: Pin for controlling backlight
        :param rst: Reset pin for ST7789
        :param spi_mode: Default is 0 for ST7789 that includes CS pin, use 3 for Non CS
        :param width: Width of display connected to ST7789
        :param height: Height of display connected to ST7789
        :param rotation: Rotation of display connected to ST7789
        :param invert: Invert display
        :param spi_speed_hz: SPI speed (in Hz)

        """
        if rotation not in [0, 90, 180, 270]:
            raise ValueError("Invalid rotation {}".format(rotation))

        if width != height and rotation in [90, 270]:
            raise ValueError("Invalid rotation {} for {}x{} resolution".format(rotation, width, height))

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self._spi = spidev.SpiDev(port, cs)
        self._spi.mode = spi_mode
        self._spi.lsbfirst = False
        self._spi.max_speed_hz = spi_speed_hz

        self._dc = dc
        self._rst = rst
        self._width = width
        self._height = height
        self._rotation = rotation
        self._invert = invert

        self._offset_left = offset_left
        self._offset_top = offset_top

        # Set DC as output.
        GPIO.setup(dc, GPIO.OUT)

        # Setup backlight as output (if provided).
        self._backlight = backlight
        if backlight is not None:
            GPIO.setup(backlight, GPIO.OUT)
            GPIO.output(backlight, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(backlight, GPIO.HIGH)

        # Setup reset as output (if provided).
        if rst is not None:
            GPIO.setup(self._rst, GPIO.OUT)
            self.reset()
        self._init()

    def send(self, data, is_data=True, chunk_size=4096):
        GPIO.output(self._dc, is_data)

        if isinstance(data, numbers.Number):
            data = [data & 0xFF]

        for start in range(0, len(data), chunk_size):
            end = min(start + chunk_size, len(data))
            self._spi.xfer(data[start:end])

    def set_backlight(self, value):
        """Set the backlight on/off."""
        if self._backlight is not None:
            GPIO.output(self._backlight, value)

    @property
    def width(self):
        return self._width if self._rotation == 0 or self._rotation == 180 else self._height

    @property
    def height(self):
        return self._height if self._rotation == 0 or self._rotation == 180 else self._width

    def command(self, data):
        self.send(data, False)

    def data(self, data):
        self.send(data, True)

    def reset(self):
        if self._rst is not None:
            GPIO.output(self._rst, 1)
            time.sleep(0.500)
            GPIO.output(self._rst, 0)
            time.sleep(0.500)
            GPIO.output(self._rst, 1)
            time.sleep(0.500)

    def _init(self):
        self.command(ST7789.SWRESET)  # Software reset
        time.sleep(0.150)  # delay 150 ms

        self.command(ST7789.MADCTL)
        self.data(0x70)

        self.command(ST7789.FRMCTR2)  # Frame rate ctrl - idle mode
        self.data(0x0C)
        self.data(0x0C)
        self.data(0x00)
        self.data(0x33)
        self.data(0x33)

        self.command(ST7789.COLMOD)
        self.data(0x05)

        self.command(ST7789.GCTRL)
        self.data(0x14)

        self.command(ST7789.VCOMS)
        self.data(0x37)

        self.command(ST7789.LCMCTRL)  # Power control
        self.data(0x2C)

        self.command(ST7789.VDVVRHEN)  # Power control
        self.data(0x01)

        self.command(ST7789.VRHS)  # Power control
        self.data(0x12)

        self.command(ST7789.VDVS)  # Power control
        self.data(0x20)

        self.command(0xD0)
        self.data(0xA4)
        self.data(0xA1)

        self.command(ST7789.FRCTRL2)
        self.data(0x0F)

        self.command(ST7789.GMCTRP1)  # Set Gamma
        self.data(0xD0)
        self.data(0x04)
        self.data(0x0D)
        self.data(0x11)
        self.data(0x13)
        self.data(0x2B)
        self.data(0x3F)
        self.data(0x54)
        self.data(0x4C)
        self.data(0x18)
        self.data(0x0D)
        self.data(0x0B)
        self.data(0x1F)
        self.data(0x23)

        self.command(ST7789.GMCTRN1)  # Set Gamma
        self.data(0xD0)
        self.data(0x04)
        self.data(0x0C)
        self.data(0x11)
        self.data(0x13)
        self.data(0x2C)
        self.data(0x3F)
        self.data(0x44)
        self.data(0x51)
        self.data(0x2F)
        self.data(0x1F)
        self.data(0x1F)
        self.data(0x20)
        self.data(0x23)

        if self._invert:
            self.command(ST7789.INVON)
        else:
            self.command(ST7789.INVOFF)

        self.command(ST7789.SLPOUT)

        self.command(ST7789.DISPON)
        time.sleep(0.100)

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        if x1 is None:
            x1 = self._width - 1

        if y1 is None:
            y1 = self._height - 1

        y0 += self._offset_top
        y1 += self._offset_top

        x0 += self._offset_left
        x1 += self._offset_left

        self.command(ST7789.CASET)
        self.data(x0 >> 8)
        self.data(x0 & 0xFF)
        self.data(x1 >> 8)
        self.data(x1 & 0xFF)
        self.command(ST7789.RASET)
        self.data(y0 >> 8)
        self.data(y0 & 0xFF)
        self.data(y1 >> 8)
        self.data(y1 & 0xFF)
        self.command(ST7789.RAMWR)

    def display(self, image):
        self.set_window()

        pixel_bytes = image_to_data(image, self._rotation)

        # Write data to hardware.
        for i in range(0, len(pixel_bytes), 4096):
            self.data(pixel_bytes[i:i + 4096])

import qrcode
import qrcode.image.svg
from lxml.etree import tostring


class QR:
    def __init__(self, text):
        f = qrcode.image.svg.SvgImage
        self.img = qrcode.make(text, image_factory=f)

    def get_svg(self):
        return tostring(self.img._img).decode("utf-8")
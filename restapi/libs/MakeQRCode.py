import qrcode, os
from qrcode.image.styledpil import StyledPilImage

base_dir = os.path.join(os.path.dirname(__file__),'../static/')

def generate_qr_code(data: str, filename: str) -> None:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)

    qrimg = qr.make_image(image_factory=StyledPilImage, embeded_image_path=os.path.join(base_dir,'logo_qrcode.jpg'))
    qrimg.save(os.path.join(base_dir,'qrcode',filename))

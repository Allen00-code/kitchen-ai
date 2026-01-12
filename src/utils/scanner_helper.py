from pyzbar.pyzbar import decode
from PIL import Image

def scan_barcode_from_image(image_path):
    try:
        # Abrimos la imagen
        img = Image.open(image_path)
        # Decodificamos
        decoded_objects = decode(img)
        
        if decoded_objects:
            # Retornamos el primer código que encontremos
            return decoded_objects[0].data.decode("utf-8")
        return None
    except Exception as e:
        print(f"Error leyendo imagen: {e}")
        return None
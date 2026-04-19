from pickletools import optimize

from PIL import Image

#utils class helps in assisting (no data storage, control flow or business rules)
def resize_image(image_path, max_size = (800,800)):
    """
   Resizes the image in-place if it exceeds max_size.
   thumbnail() preserves aspect ratio — no stretching or distortion.
   Saves back to the same path, replacing the original oversized file.
   """
    #opens the image
    img = Image.open(image_path)

    # convert RGBA/palette PNGs to RGB so JPEG saving never crashes
    if img.mode in ('RGBA','P'):
        img = img.convert('RGB')

    #check size height and width
    if img.height > max_size[0] or img.width > max_size[1]:
        img.thumbnail(max_size) # keeps aspect ratio
        img.save(image_path,optimize=True,quality=85)
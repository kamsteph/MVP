from PIL import image

#utils class helps in assisting (no data storage, control flow or business rules)
def resize_image(image_path, size = (800,800)):
    #opens the image
    img = Image.open(image_path)

    #check size height and width
    if img.height > size[0] or img.width > size[1]:
        img.thumbnail(size)
        img.save(image_path)
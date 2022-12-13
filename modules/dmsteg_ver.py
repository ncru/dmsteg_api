import fitz  # PyMuPDF
import io
from PIL import Image


def getfile(file):
    # open the file
    pdf_file = fitz.open(file)

    # iterate over PDF pages
    for page_index in range(len(pdf_file)):
        # get the page itself
        page = pdf_file[page_index]
        # get image list
        image_list = page.get_images()

        for image_index, img in enumerate(image_list, start=1):
            # get the XREF of the image
            xref = img[0]
            # extract the image bytes
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            # get the image extension
            image_ext = base_image["ext"]
            # load it to PIL
            image = Image.open(io.BytesIO(image_bytes))
            # save it to local disk
            image.save(open(f"image{page_index+1}_{image_index}.{image_ext}", "wb"))

    # return True, "hello"

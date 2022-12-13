from fitz import fitz, Rect


def getfile(file):
    # open pdf
    # w = 595
    # h = 842
    scale = 50

    # TO DO: Get pdf page dimensions, then calculate rx ry from there

    rx = 545  # left
    ry = 725  # down

    rect = Rect(
        rx, ry, rx + scale, ry + scale
    )  # x0, y0, x1, y1 | top left, bottom right | move image using x0y0, size image using x1y1
    # open the file
    pdf_file = fitz.open(file)

    for page in pdf_file:
        page.insert_image(rect, filename="datamatrix.png")

    pdf_file.saveIncr()

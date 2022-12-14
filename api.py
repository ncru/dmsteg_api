import os
import psycopg2
from dotenv import load_dotenv
from modules.threesys import *
from flask import Flask, render_template, request, send_file, url_for, flash, redirect
from werkzeug.utils import secure_filename
import json

INSERT_ORIGPDFS_RETURN_ID = (
    "INSERT INTO origpdfs (orig_pdf_data) VALUES (%s) RETURNING orig_id;"
)
INSERT_THREESYSPDF_RETURN_ROW = "INSERT INTO threesyspdfs (pdf_metadata, pdf_data, origpdfs_id) VALUES (%s,%s, %s) RETURNING *;"

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)
app.config["UPLOAD_FOLDER"] = "./uploads/"
# app.config["SECRET_KEY"] = "a1b6da6f44ab0e075f90f2f503fdc24b"  # dont touch
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def main():
    return render_template("index.html")


def check_files(req):
    file = req.files["file"]
    if (
        "file" not in request.files
        or request.files["file"] == ""
        or not allowed_file(file.filename)
    ):
        return False
    return True


@app.route("/generate", methods=["POST"])
def generate():
    if request.method == "POST":
        if not check_files(request):
            return {
                "message": "Invalid inputs",
            }, 406

        file = request.files["file"]
        # file_name = f'temp-{noext_file_name}-original.pdf'
        # file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        file_from_folder = f"./uploads/{file.filename}"
        document = fitz.open(file_from_folder)

        # rpdf_data = bytes(rpdf_data)
        # with open(
        #     os.path.join(app.config["UPLOAD_FOLDER"], f"temp-{rpdf_id}-modified.pdf"),
        #     "wb",
        # ) as _f:
        #     _f.write(rpdf_data)

        images = grab_first_page_images(document)
        img_paths = []
        for i, image in enumerate(images):
            img_name = f'tempimg-{i}-{file.filename[: file.filename.find(".pdf")]}.png'
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], img_name)
            img_paths.append(img_path)
            image.save(img_path)

        dm_paths = grab_all_dms(img_paths)
        # if dms in the pdf check if they are 3sys
        if len(dm_paths) > 0:
            valid_dm_path = check_dms_for_steganography(dm_paths)
            if valid_dm_path != False:
                reg_msg = read_dm(valid_dm_path)
                _image = Image.open(valid_dm_path)
                steg_msg = read_steganography(_image)
                return {
                    "message": "The document is already signed",
                }, 400
            else:
                return {
                    "message": "The document may not be valid",
                }, 400
        # if there are no dms then check if the margins are clear
        elif margins_passed(document):
            orig_pdf_data = bytes(document.tobytes())
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(INSERT_ORIGPDFS_RETURN_ID, (orig_pdf_data,))
                    steg_id = cursor.fetchone()[0]

            ord_dm = generate_dm(document)
            steg_dm = steganography(ord_dm, str(steg_id))
            modified_document = put_steg_dm_in_pdf(document, steg_dm)
            base_name = os.path.basename(modified_document.name)
            new_name = f'temp-{base_name[: base_name.find(".pdf")]}-modified.pdf'
            new_path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
            modified_document.save(new_path)
            metadata = json.dumps(modified_document.metadata)
            new_pdf_data = bytes(modified_document.tobytes())

            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        INSERT_THREESYSPDF_RETURN_ROW, (metadata, new_pdf_data, steg_id)
                    )
                    (
                        rpdf_id,
                        rpdf_metadata,
                        rpdf_data,
                        rorigpdfs_id,
                    ) = cursor.fetchall()[0]

            # os.remove(file_path)
            # os.remove(new_path)
            send_file(new_path, as_attachment=True)
            return {
                "message": "Verified pdf successfully created",
                "pdf_id": rorigpdfs_id,
                "metadata": rpdf_metadata,
            }, 201
        else:
            return {
                "message": "The document must have clear 1 inch margins",
            }, 400


@app.route("/verify", methods=["POST"])
def verify():
    if request.method == "POST":
        if not check_files(request):
            return {
                "message": "Invalid inputs",
            }, 406

        file = request.files["file"]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        file_from_folder = f"./uploads/{file.filename}"
        document = fitz.open(file_from_folder)

        images = grab_first_page_images(document)
        img_paths = []
        for i, image in enumerate(images):
            img_name = f'tempimg-{i}-{file.filename[: file.filename.find(".pdf")]}.png'
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], img_name)
            img_paths.append(img_path)
            image.save(img_path)

        dm_paths = grab_all_dms(img_paths)
        if len(dm_paths) > 0:
            valid_dm_path = check_dms_for_steganography(dm_paths)
            if valid_dm_path != False:
                reg_msg = read_dm(valid_dm_path)
                _image = Image.open(valid_dm_path)
                steg_msg = read_steganography(_image)
                return {
                    "message": "The document is signed and valid!",
                }, 200
            else:
                return {
                    "message": "The document is not valid",
                }, 406
        else:
            return {
                "message": "This document has not been validated",
            }, 300
    return


if __name__ == "__main__":
    app.run()

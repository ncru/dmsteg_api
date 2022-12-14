import os
import psycopg2
from dotenv import load_dotenv
from modules.threesys import *
from flask import Flask, render_template, request, send_file, url_for, flash, redirect
from werkzeug.utils import secure_filename
import json
import base64

INSERT_PDF_RETURN_ROW = (
    "INSERT INTO threesyspdfs (pdf_metadata, pdf_data) VALUES (%s, %s) RETURNING *;"
)

# load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)
app.config["UPLOAD_FOLDER"] = "uploads/"
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def main():
    # if request.method == "POST":
    #     # check if the post request has the file part
    #     if "file" not in request.files:
    #         flash("No file part")
    #         return redirect(request.url)
    #     file = request.files["file"]
    #     # If the user does not select a file, the browser submits an
    #     # empty file without a filename.
    #     if file.filename == "":
    #         flash("No selected file")
    #         return redirect(request.url)
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    #         return redirect(url_for("download_file", name=filename))
    return render_template("index.html")


# FileStorage format


@app.route("/generate", methods=["POST"])
def generate():
    if request.method == "POST":
        file = request.files["file"]
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
        file_from_folder = f"uploads/{file.filename}"
        document = create_fitz_file(file_from_folder)

        metadata = json.dumps(document.metadata)
        pdf_data = bytes(document.tobytes())

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(INSERT_PDF_RETURN_ROW, (metadata, pdf_data))
                (rpdf_id, rpdf_metadata, rpdf_data) = cursor.fetchall()[0]

        rpdf_data = bytes(rpdf_data)
        with open(
            os.path.join(app.config["UPLOAD_FOLDER"], f"temp-{rpdf_id}.pdf"), "wb"
        ) as _f:
            _f.write(rpdf_data)

        # return {
        #     "pdf_id": rpdf_id,
        #     "message": "VERIFIED PDF SUCCESSFULLY CREATED",
        #     "metadata": rpdf_metadata,
        # }, 201

        images = grab_first_page_images(document)
        dms = grab_all_dms(images)

        #  INSERT THERE MAY ONLY BE ONE 3SYS STEG

        # if dms in the pdf check if they are 3sys
        if len(dms) > 0:
            valid_dm = check_dms_for_steganography(dms)
            if valid_dm != False:
                reg_msg = read_dm(valid_dm)
                steg_msg = read_steganography(valid_dm)
                return "THE DOCUMENT IS ALREADY SIGNED", 400
                # print("MESSAGE:", reg_msg)
                # print("SECRET:", steg_msg)
            else:
                return "THE DOCUMENT MAY NOT BE VALID", 400
                # print("THE DOCUMENT MAY NOT BE VALID")
        # if there are no dms then check if the margins are clear
        elif margins_passed(document):
            ord_dm = generate_dm(document)
            steg_dm = steganography(ord_dm)
            # put dm in pdf
            modified_document = put_steg_dm_in_pdf(document, steg_dm)
            base_name = os.path.basename(modified_document.name)
            new_name = base_name[: base_name.find(".pdf")] + "-modified.pdf"
            modified_document.save(os.path.join(app.config["UPLOAD_FOLDER"], new_name))
            return "DM STEG ADDED TO DOCUMENT", 200
        else:
            return "THE DOCUMENT MUST HAVE CLEAR 1 INCH MARGINS", 400

    # if request.method == "POST":
    #     f = request.files["file"]
    #     f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))

    #     # get file, text to be hidden here for processing
    #     file = "buffer/%s" % (f.filename)
    #     text = request.form["text"]
    #     #
    #     # - external function for generating DM STEG here -
    #     #
    #     dmsteg_gen.getfile(file)  # external function for inserting DM STEG

    #     # return file
    #     return send_file(file, as_attachment=True)  # ENDPOINT RESPONSE
    #     # return render_template("success.html", name=text) # to test whether text is read from form


@app.route("/verify", methods=["POST"])
def verify():
    return
    # if request.method == "POST":
    #     # save file
    #     f = request.files["file"]
    #     f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))

    #     # get file to be processed to verify function
    #     file = "buffer/%s" % (f.filename)

    #     dmsteg_ver.getfile(file)
    #     # isAuthentic = dmsteg_ver.getfile(file)

    #     # get separated DM here
    #     # insert DM to DM Steg Reader function

    #     return render_template("success.html", name=True)  # return boolean
    #     # return send_file("gen/datamatrix.png", as_attachment=True)


if __name__ == "__main__":
    app.run()

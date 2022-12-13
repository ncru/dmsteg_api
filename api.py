import os, modules.dmsteg_gen as dmsteg_gen, modules.dmsteg_ver as dmsteg_ver
from flask import Flask, render_template, request, send_file, url_for, flash, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "buffer/"
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def main():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return redirect(url_for("download_file", name=filename))

    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if request.method == "POST":
        f = request.files["file"]
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))

        # get file, text to be hidden here for processing
        file = "buffer/%s" % (f.filename)
        text = request.form["text"]
        #
        # - external function for generating DM STEG here -
        #
        dmsteg_gen.getfile(file)  # external function for inserting DM STEG

        # return file
        return send_file(file, as_attachment=True)  # ENDPOINT RESPONSE
        # return render_template("success.html", name=text) # to test whether text is read from form


@app.route("/verify", methods=["POST"])
def verify():
    if request.method == "POST":
        # save file
        f = request.files["file"]
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))

        # get file to be processed to verify function
        file = "buffer/%s" % (f.filename)

        dmsteg_ver.getfile(file)
        # isAuthentic = dmsteg_ver.getfile(file)

        # get separated DM here
        # insert DM to DM Steg Reader function

        return render_template("success.html", name=True)  # return boolean
        # return send_file("gen/datamatrix.png", as_attachment=True)


if __name__ == "__main__":
    app.run(port=5000, debug=True)

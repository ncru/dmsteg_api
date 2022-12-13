import os, dmsteg_gen
from flask import Flask, render_template, request, send_file, url_for, flash, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "temp/"
ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def upload():
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
def success():
    if request.method == "POST":
        f = request.files["file"]
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))

        # get file here for processing
        file = "temp/%s" % (f.filename)
        # external function for generating DM STEG here
        # external function for inserting DM STEG below
        dmsteg_gen.getfile(file)

        # return file
        return send_file(file, as_attachment=True)
        # return render_template("success.html", name=f.filename)


if __name__ == "__main__":
    app.run(port=5000, debug=True)

from flask import Flask, request, jsonify, render_template
from scanner import scan_server

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Brak adresu URL"}), 400

    result = scan_server(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

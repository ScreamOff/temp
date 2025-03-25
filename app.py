from flask import Flask, request, jsonify, render_template
from scanner import scan_server

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    url = data.get("url")
    depth = data.get("depth", 3)  # Pobieramy głębokość, domyślnie ustawiamy 3, jeśli nie podano

    if not url:
        return jsonify({"error": "Brak adresu URL"}), 400

    # Przekazujemy url i depth do funkcji skanowania
    result = scan_server(url, depth)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

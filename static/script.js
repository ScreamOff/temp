function scanServer() {
    let url = document.getElementById("urlInput").value;

    fetch("/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
    })
    .then(response => response.json())
    .then(data => {
        let resultDiv = document.getElementById("result");
        if (data.error) {
            resultDiv.innerHTML = `<p style="color:red;">Błąd: ${data.error}</p>`;
        } else {
            resultDiv.innerHTML = `
                <h3>Wyniki dla: ${url}</h3>
                <p><b>Adres IP:</b> ${data.ip}</p>
                <h4>Otwarte porty:</h4>
                <ul>${Object.entries(data.open_ports).map(([port, status]) => `<li>${port}: ${status}</li>`).join("")}</ul>
                <h4>Fragment zawartości strony:</h4>
                <p>${data.content_snippet}</p>
            `;
        }
    })
    .catch(error => console.error("Błąd:", error));
}

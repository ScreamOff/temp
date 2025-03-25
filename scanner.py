import os
import socket
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import XMLParsedAsHTMLWarning
import warnings

# Funkcja skanowania portów
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def scan_ports(ip):
    """ Skanuje porty na danym IP za pomocą socket """
    ports = [
        20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 119, 123, 135, 137, 138, 139, 143,
        161, 162, 179, 194, 389, 443, 445, 465, 514, 515, 587, 636, 873, 989, 990,
        993, 995, 1080, 1194, 1433, 1434, 1521, 1723, 2049, 2082, 2083, 2181, 2483,
        2484, 3306, 3389, 3690, 4000, 4045, 4369, 5000, 5432, 5672, 5900, 5984, 6379,
        6667, 7001, 8080, 8443, 9000, 9090, 9200, 9300, 11211, 27017, 27018, 50000
    ]

    result = {}

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # Ustalamy limit czasu na 1 sekundy
        status = sock.connect_ex((ip, port))  # Próba połączenia się z portem
        result[port] = "open" if status == 0 else "closed"
        sock.close()

    return result

# Funkcja do pobierania strony głównej i zasobów
def fetch_all_content(url, visited_urls=None, depth=3, base_url=None):
    """ Pobiera wszystkie pliki z serwera (HTML, CSS, JS, obrazy) """
    if visited_urls is None:
        visited_urls = set()

    if depth == 0 or url in visited_urls:
        return {"images": [], "scripts": [], "styles": [], "others": []}  # Zwracamy pustą listę, jeśli przekroczono głębokość

    try:
        # Wysyłanie żądania HTTP
        response = requests.get(url, timeout=5)
        html_content = response.text

        # Parsowanie HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # Zbieranie linków do innych stron i zasobów
        resources = {
            "images": [],
            "scripts": [],
            "styles": [],
            "others": []
        }

        # Zbieramy wszystkie obrazy
        for img in soup.find_all("img"):
            img_url = img.get("src")
            if img_url:
                img_url = urljoin(url, img_url)  # Konwertuj na pełny URL
                resources["images"].append(img_url)

        # Zbieramy skrypty
        for script in soup.find_all("script"):
            script_url = script.get("src")
            if script_url:
                script_url = urljoin(url, script_url)
                resources["scripts"].append(script_url)

        # Zbieramy style
        for link in soup.find_all("link", rel="stylesheet"):
            style_url = link.get("href")
            if style_url:
                style_url = urljoin(url, style_url)
                resources["styles"].append(style_url)

        # Zbieramy inne pliki (np. PDF, pliki tekstowe)
        for a in soup.find_all("a"):
            href = a.get("href")
            if href:
                href = urljoin(url, href)
                resources["others"].append(href)

        # Dodajemy URL do odwiedzonych linków
        visited_urls.add(url)

        # Rekurencyjne pobieranie linków do innych stron
        for a in soup.find_all("a"):
            href = a.get("href")
            # Sprawdzamy, czy link jest częścią tej samej domeny i czy nie był wcześniej odwiedzony
            if href and href.startswith('http') and href not in visited_urls:
                # Jeśli jest częścią tej samej domeny
                if base_url and base_url in href:
                    visited_urls.add(href)
                    # Rekurencyjnie wywołujemy funkcję dla nowych linków
                    new_resources = fetch_all_content(href, visited_urls, depth - 1, base_url)
                    # Dodajemy znalezione zasoby z rekurencji
                    for key in resources:
                        resources[key].extend(new_resources[key])

        # Zapisz zawartość na serwerze
        save_to_server(url, html_content, resources)

        return resources

    except requests.RequestException as e:
        return {"error": str(e)}

# Funkcja zapisywania zawartości na serwerze
def save_to_server(url, content, resources):
    """ Zapisuje stronę i jej zawartość na serwerze """
    # Ustalamy ścieżkę dla pliku
    parsed_url = urlparse(url)
    safe_path = parsed_url.path.lstrip('/').replace('?', '_').replace('&', '_')  # Zamiana znaków na bezpieczne
    folder_path = Path(f"downloaded_files/{parsed_url.netloc}/{safe_path}")

    # Tworzymy strukturę katalogów, jeśli nie istnieje
    folder_path.parent.mkdir(parents=True, exist_ok=True)

    # Zapisz treść HTML
    html_file = folder_path.with_suffix('.html')
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(content)

    # Zapisz inne zasoby (obrazki, CSS, JS, itp.)
    save_resources(folder_path, "images", resources["images"])
    save_resources(folder_path, "scripts", resources["scripts"])
    save_resources(folder_path, "styles", resources["styles"])
    save_resources(folder_path, "others", resources["others"])

def save_resources(base_folder, folder_name, resource_urls):
    """ Funkcja do zapisywania zasobów (np. obrazy, skrypty) """
    # Tworzymy folder dla zasobów (np. obrazy, skrypty)
    resource_folder = base_folder / folder_name

    # Upewnijmy się, że folder istnieje
    resource_folder.mkdir(parents=True, exist_ok=True)

    for resource_url in resource_urls:
        try:
            # Pobieramy plik
            response = requests.get(resource_url, timeout=5)
            response.raise_for_status()  # Wyrzuci wyjątek dla błędów HTTP, np. 404

            # Sprawdzamy, czy URL kończy się na plik (np. .jpg, .css) i nie jest folderem
            resource_name = Path(urlparse(resource_url).path).name
            resource_path = resource_folder / resource_name

            # Sprawdzamy, czy ścieżka wskazuje na folder (aby uniknąć zapisu w folderze zamiast pliku)
            if not resource_path.suffix:
                resource_path = resource_path.with_suffix(".html")  # Zakładając, że to plik HTML, jeśli nie ma rozszerzenia

            # Zapisujemy plik
            with open(resource_path, 'wb') as file:
                file.write(response.content)

        except requests.RequestException as e:
            print(f"Błąd przy pobieraniu zasobu: {resource_url} - {e}")
        except PermissionError as e:
            print(f"Błąd przy zapisie pliku: {resource_url} - {e}")

def get_ip(domain):
    """ Pobiera adres IP dla podanej domeny """
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def scan_server(url, depth=3):
    """ Główna funkcja do skanowania """
    domain = url.replace("http://", "").replace("https://", "").split("/")[0]
    ip = get_ip(domain)

    if not ip:
        return {"error": "Nie można uzyskać IP"}

    # Skanowanie portów
    ports = scan_ports(ip)

    # Pobieranie zawartości strony i zasobów
    base_url = f"http://{domain}"
    resources = fetch_all_content(url, depth=depth, base_url=base_url)

    return {
        "ip": ip,
        "open_ports": ports,
        "resources": resources  # Zwracamy zasoby
    }

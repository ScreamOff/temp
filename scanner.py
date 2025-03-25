import socket
import requests
import nmap


def get_ip(domain):
    """ Pobiera adres IP dla podanej domeny """

    try:
        return socket.gethostbyname(domain.replace("http://", "").replace("https://", "").split("/")[0])
    except socket.gaierror:
        return None


def scan_ports(ip):
    """ Skanuje popularne porty na danym IP """
    scanner = nmap.PortScanner()
    ports = [21, 22, 25, 53, 80, 443, 3306, 8080]  # Najczęściej używane porty
    result = {}

    for port in ports:
        try:
            scanner.scan(ip, str(port))
            state = scanner[ip]['tcp'][port]['state']
            result[port] = state
        except:
            result[port] = "unknown"

    return result


def fetch_content(url):
    """ Pobiera zawartość strony """
    try:
        response = requests.get(url, timeout=5)
        return response.text[:500]  # Skrócona wersja treści
    except requests.RequestException:
        return "Brak dostępu"


def scan_server(url):
    """ Główna funkcja do skanowania """
    domain = url.replace("http://", "").replace("https://", "").split("/")[0]
    ip = get_ip(domain)

    if not ip:
        return {"error": "Nie można uzyskać IP"}

    ports = scan_ports(ip)
    content = fetch_content(url)

    return {
        "ip": ip,
        "open_ports": ports,
        "content_snippet": content
    }
if __name__ == "__main__":
    nm = nmap.PortScanner()
    print(nm.scan(get_ip("https://tu.kielce.pl")))
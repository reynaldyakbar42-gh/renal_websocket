import socket
import threading
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Konfigurasi
HOST = 'localhost'
PORT = 8081

def get_scraped_data():
    """Fungsi yang sudah diperbaiki untuk scraping web Informatika"""
    try:
        url = "https://informatika.umsida.ac.id/pembekalan-calon-asisten-laboratorium-teknik-informatika-umsida-perkuat-pemahaman-dasar-jaringan/"
        
        # PERBAIKAN: Tambahkan headers agar tidak diblokir
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # PERBAIKAN: Selektor yang lebih aman
        # Mengambil heading h3 (biasanya judul artikel terkait/sidebar)
        items = soup.find_all('h3')
        results = []
        for item in items[:10]:
            # Ambil teks langsung dari h3 atau link di dalamnya
            text = item.get_text(strip=True)
            if text:
                results.append(text)
        
        return results if results else ["Tidak ada data ditemukan."]
    except Exception as e:
        return [f"Gagal Scraping: {e}"]

def send_response(client_socket, status, content_type, content):
    """Helper untuk mengirim data melalui socket"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    response_header = f"HTTP/1.1 {status}\r\n"
    response_header += f"Content-Type: {content_type}\r\n"
    response_header += f"Content-Length: {len(content)}\r\n"
    response_header += "Connection: close\r\n\r\n"
    
    client_socket.sendall(response_header.encode('utf-8') + content)

def parse_request(request_data):
    """Parsing dasar untuk mendapatkan path"""
    try:
        lines = request_data.split('\r\n')
        if len(lines) > 0:
            first_line = lines[0].split(' ')
            if len(first_line) > 1:
                path = urlparse(first_line[1]).path
                return {'path': path}
    except:
        pass
    return {'path': '/'}

def handle_client(client_socket, client_address):
    try:
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        if not request_data:
            return
        
        parsed = parse_request(request_data)
        
        # ROUTING
        if parsed['path'] == '/' or parsed['path'] == '/index.html':
            html = """
            <html>
                <head><title>Home Server</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Server + Scraper Integration</h1>
                    <p>Berhasil menghubungkan Socket dengan BeautifulSoup</p>
                    <a href="/scraping" style="display:inline-block; padding:10px 20px; background:blue; color:white; text-decoration:none; border-radius:5px;">
                        Lihat Hasil Scraping Live
                    </a>
                </body>
            </html>
            """
            send_response(client_socket, "200 OK", "text/html", html)

        elif parsed['path'] == '/scraping':
            print(f"[*] Menjalankan scraping untuk {client_address}")
            data_list = get_scraped_data()
            
            items_html = "".join([f"<li style='margin-bottom:8px;'>{data}</li>" for data in data_list])
            response_html = f"""
            <html>
                <head><title>Hasil Scraping</title></head>
                <body style="font-family: sans-serif; padding: 30px;">
                    <h2>Daftar Judul dari Web Informatika</h2>
                    <hr>
                    <ul>{items_html}</ul>
                    <br>
                    <a href="/"> Kembali ke Utama</a>
                </body>
            </html>
            """
            send_response(client_socket, "200 OK", "text/html", response_html)
        else:
            send_response(client_socket, "404 Not Found", "text/html", "<h1>404 Not Found</h1>")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Server Aktif di http://{HOST}:{PORT}")
    
    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client, addr))
        thread.start()

if __name__ == "__main__":
    main()
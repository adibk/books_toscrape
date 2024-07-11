import requests
from bs4 import BeautifulSoup

# URL of the site to scrape

book_links = []

page_nb = 50
while True:
    base_url = 'https://books.toscrape.com/catalogue'
    page_url = f'{base_url}/page-{page_nb}.html'

    print(f'request page: {page_nb}, url: {page_url}')

    response = requests.get(page_url)
    if response.status_code != 200:
        break

    soup = BeautifulSoup(response.text, 'html.parser')
    books = soup.find_all('article', class_='product_pod')

    for book in books:
        link = book.h3.a['href']
        book_links.append(f'{base_url}/{link}')
    
    page_nb += 1
    
for book_link in book_links:
    print(book_link)


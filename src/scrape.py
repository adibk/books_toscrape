import requests
from bs4 import BeautifulSoup

# URL of the site to scrape

book_links = []

page_nb = 1
while True:
    url = f'https://books.toscrape.com/catalogue/page-{page_nb}.html'

    print(f'request page: {page_nb}, url: {url}')

    response = requests.get(url)
    if response.status_code != 200:
        break

    soup = BeautifulSoup(response.text, 'html.parser')
    books = soup.find_all('article', class_='product_pod')

    for book in books:
        link = book.h3.a['href']
        full_link = url + link
        book_links.append(full_link)
    
    page_nb += 1
    
for book_link in book_links:
    print(book_link)

# print(books)
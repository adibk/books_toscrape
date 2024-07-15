import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import spacy

verbose = True
verbose_content = False

url_base = 'https://books.toscrape.com'
url_catalogue = f'{url_base}/catalogue'

def get_page_links():
    book_links = []
    page_nb = 1
    while True:
        url_page = f'{url_catalogue}/page-{page_nb}.html'

        if verbose:
            print(f'request page: {page_nb}, url: {url_page}')

        response = requests.get(url_page)
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.find_all('article', class_='product_pod')

        for book in books:
            book_path = book.h3.a['href']
            book_links.append(f'{url_catalogue}/{book_path}')
        
        page_nb += 1
        
    return book_links
    
def get_books_content():
    books = []
    book_links = get_page_links()
    for book_link in book_links:
        response = requests.get(book_link)
        if response.status_code != 200 and verbose:
            print(f'request error, url: {book_link}')
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        product = {}
        
        # url
        product['url'] = book_link
        
        # book nb
        pattern = r"_(\d+)/index.html"
        match = re.search(pattern, product['url'])
        if match:
            product['book_nb'] = int(match.group(1))
        
        # title
        product['title'] = None
        h1_tag = soup.find('h1')
        if h1_tag:
            product['title'] = h1_tag.text.strip()
        
        # img
        product['url_image'] = None 
        image_container = soup.find('div', id='product_gallery')
        if image_container:
            img_tag = image_container.find('img')
            if img_tag and 'src' in img_tag.attrs:
                url_img = img_tag['src']
                product['url_image'] = urljoin(url_base, url_img)
            
        # category
        product['category'] = None  
        breadcrumb = soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            breadcrumb_items = breadcrumb.find_all('li')
            if len(breadcrumb_items) > 2:
                product['category'] = breadcrumb_items[2].text.strip()

        # rating
        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }
        product['rating'] = None
        rating_element = soup.find('p', class_='star-rating')
        if rating_element and len(rating_element['class']) > 1:
            product_rating_class = rating_element['class'][1]
            product['rating'] = rating_map.get(product_rating_class, None)    

        # description
        product['description'] = None
        description_section = soup.find('div', id='product_description')
        if description_section:
            next_sibling_p = description_section.find_next_sibling('p')
            if next_sibling_p:
                product['description'] = next_sibling_p.text.strip()
            
        # description ...more
        more = '...more'
        if product['description'] is not None and product['description'].endswith(more):
            product['description'] = product['description'][:-len(more)].strip()
            product['description_more'] = True
        else:
            product['description_more'] = False
        
        # product info    
        product['UPC'] = None
        product['type'] = None
        product['price_exclude_tax'] = None
        product['price_include_tax'] = None
        product['tax'] = None
        product['availability'] = None
        product['nb_reviews'] = None
        product['currency'] = None
        header_map = {
            'UPC': 'UPC',
            'Product Type': 'type',
            'Price (excl. tax)': 'price_exclude_tax',
            'Price (incl. tax)': 'price_include_tax',
            'Tax': 'tax',
            'Availability': 'availability',
            'Number of reviews': 'nb_reviews',
        }
        product_info_table = soup.find('table', class_='table table-striped')
        if product_info_table:
            for row in product_info_table.find_all('tr'):
                header = row.find('th').text.strip()
                value = row.find('td').text.strip()
                new_header = header_map.get(header, None)    
                if new_header:
                    product[new_header] = value    

        # currency
        currency_map = {
            '£': 'pound',
            '€': 'euro',
            '$': 'dollar',
            '¥': 'yen',
            '₹': 'rupee',
            '₽': 'ruble',
            '₩': 'won',
            '₺': 'lira'
        }
        pattern = r"([£€$¥₹₽₩₺])(\d+\.\d{2})"
        match = re.search(pattern, product['price_include_tax'])
        if match:
            product['currency'] = currency_map.get(match.group(1), None)

        # price
        pattern = r'[-+]?\d*\.\d+'
        if product['price_exclude_tax']:
            product['price_exclude_tax'] = float(re.search(pattern, product['price_exclude_tax']).group())
        else:
            product['price_exclude_tax'] = 0
        if product['price_include_tax']:
            product['price_include_tax'] = float(re.search(pattern, product['price_include_tax']).group())
        else:
            product['price_include_tax'] = 0
        if product['tax']:
            product['tax'] = float(re.search(pattern, product['tax']).group())
        else:
            product['tax'] = 0
            
        # Availability
        if product['availability']:
            pattern = r"In stock \((\d+) available\)"
            match = re.search(pattern, product['availability'])
            if match:
                product['availability'] = int(match.group(1))
            else:
                product['availability'] = 0
        
        # keywords
        product['keywords'] = None
        def extract_keywords_spacy(text, num_keywords=5):
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            # Extract keywords based on named entities and noun chunks, excluding stop words
            keywords = set()
            for token in doc:
                if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                    keywords.add(token.text)
            # Alternatively, using named entities and noun chunks
            for entity in doc.ents:
                if not entity.text.lower() in nlp.Defaults.stop_words:
                    keywords.add(entity.text)
            for chunk in doc.noun_chunks:
                if not chunk.text.lower() in nlp.Defaults.stop_words:
                    keywords.add(chunk.text)
            # Return the most relevant keywords
            return list(keywords)[:num_keywords]
        if product['description']:
            product['keywords'] = extract_keywords_spacy(product['description'])
        
        # if verbose_content:
        if verbose_content:
            print('\nProduct Information:\n')
            for key, value in product.items():
                print(f'{key}: {value}\n\n')
            print('-' * 100)
        elif verbose:
            print(f'book number {product["book_nb"]} done')
        
        books.append(product)
    
    return books

def main():
    get_books_content()

if __name__ == '__main__':
    main()
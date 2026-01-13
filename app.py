import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

st.title("Trustpilot Review Scraper")
st.write("Extract reviews from any Trustpilot page and receive them via email.")

# Input fields
url = st.text_input("Trustpilot URL", placeholder="https://www.trustpilot.com/review/example.com")
num_pages = st.number_input("Number of pages to scrape", min_value=1, max_value=100, value=5)
email = st.text_input("Your email", placeholder="you@example.com")

def scrape_trustpilot_reviews(url, num_pages, min_length=20):
    reviews = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'}
    
    progress = st.progress(0)
    status = st.empty()
    
    for page in range(1, num_pages + 1):
        status.text(f"Scraping page {page} of {num_pages}...")
        progress.progress(page / num_pages)
        
        paginated_url = f"{url}?page={page}"
        response = requests.get(paginated_url, headers=headers)
        
        if response.status_code != 200:
            continue
        
        # FIX 1: Decode raw bytes as UTF-8 to handle special characters
        html_content = response.content.decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        review_blocks = soup.find_all('article')
        
        for block in review_blocks:
            text_tag = block.find('p', {'data-service-review-text-typography': 'true'})
            date_tag = block.find('time')
            
            # FIX 3: Only match star rating images (alt text contains "Rated")
            rating_tag = block.find('img', alt=lambda x: x and 'Rated' in x)
            
            # FIX 2: Preserve spacing between paragraphs
            review_text = text_tag.get_text(separator=' ', strip=True) if text_tag else ''
            review_date = date_tag['datetime'] if date_tag and 'datetime' in date_tag.attrs else 'Unknown'
            star_rating = rating_tag['alt'] if rating_tag else 'Not found'
            
            if len(review_text) >= min_length:
                reviews.append({
                    'text': review_text,
                    'rating': star_rating,
                    'date': review_date
                })
    
    status.text(f"Done! Found {len(reviews)} reviews.")
    return reviews

def send_email_with_csv(to_email, csv_content, company_name, review_count):
    gmail_address = st.secrets["GMAIL_ADDRESS"]
    gmail_password = st.secrets["GMAIL_APP_PASSWORD"]
    
    analysis_prompt = f"""I have a CSV file with {review_count} Trustpilot reviews for {company_name}. The columns are: text, rating, date.

Please analyse these reviews and provide:

1. **Sentiment Overview** - Overall sentiment and percentage breakdown by star rating

2. **Key Themes (Top 5)** - What topics

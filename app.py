import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
import io

st.title("Trustpilot Review Scraper")
st.write("Extract reviews from any Trustpilot page and download as CSV.")

# Input fields
url = st.text_input("Trustpilot URL", placeholder="https://www.trustpilot.com/review/example.com")
num_pages = st.number_input("Number of pages to scrape", min_value=1, max_value=100, value=5)

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
        response.encoding = 'utf-8'  # FIX 1: Force UTF-8 encoding
        
        if response.status_code != 200:
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
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

# Scrape button
if st.button("Scrape Reviews"):
    if not url:
        st.error("Please enter a Trustpilot URL")
    elif "trustpilot.com/review/" not in url:
        st.error("Please enter a valid Trustpilot URL (e.g., https://www.trustpilot.com/review/example.com)")
    else:
        reviews = scrape_trustpilot_reviews(url, num_pages)
        
        if reviews:
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['text', 'rating', 'date'])
            writer.writeheader()
            writer.writerows(reviews)
            
            # Download button
            st.download_button(
                label="📥 Download CSV",
                data=output.getvalue(),
                file_name="trustpilot_reviews.csv",
                mime="text/csv"
            )
            
            # Preview
            st.subheader("Preview (first 5 reviews)")
            for review in reviews[:5]:
                st.write(f"**{review['rating']}** — {review['date']}")
                st.write(review['text'])
                st.divider()
        else:
            st.warning("No reviews found. Check the URL and try again.")

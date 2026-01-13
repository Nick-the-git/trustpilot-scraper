import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
import io
import resend

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
        
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        review_blocks = soup.find_all('article')
        
        for block in review_blocks:
            text_tag = block.find('p', {'data-service-review-text-typography': 'true'})
            date_tag = block.find('time')
            rating_tag = block.find('img', alt=lambda x: x and 'Rated' in x)
            
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
    resend.api_key = st.secrets["RESEND_API_KEY"]
    
    analysis_prompt = f"""I have a CSV file with {review_count} Trustpilot reviews for {company_name}. The columns are: text, rating, date.

Please analyse these reviews and provide:

1. **Sentiment Overview** - Overall sentiment and percentage breakdown by star rating

2. **Key Themes (Top 5)** - What topics come up most frequently?

3. **Strengths** - What do customers consistently praise? Include 2-3 example quotes.

4. **Areas for Improvement** - What complaints appear repeatedly? Include 2-3 example quotes.

5. **Notable Reviews** - Highlight 3-5 particularly insightful or actionable reviews.

6. **Recommendations** - Based on this feedback, what are the top 5 actions the business should take?

Format as a clear executive summary."""

    html_content = f"""
    <h2>Your Trustpilot Reviews Export</h2>
    <p>Your requested export for <strong>{company_name}</strong> is attached.</p>
    <p><strong>Total reviews:</strong> {review_count}</p>
    
    <h3>AI Analysis Prompt</h3>
    <p>Upload the attached CSV to Claude or ChatGPT along with this prompt:</p>
    <pre style="background: #f5f5f5; padding: 15px; border-radius: 8px; white-space: pre-wrap;">{analysis_prompt}</pre>
    """
    
    resend.Emails.send({
        "from": "Trustpilot Scraper <onboarding@resend.dev>",
        "to": to_email,
        "subject": f"Your Trustpilot Reviews - {company_name}",
        "html": html_content,
        "attachments": [
            {
                "filename": f"trustpilot_reviews_{company_name}.csv",
                "content": list(csv_content.encode('utf-8'))
            }
        ]
    })

# Scrape button
if st.button("Scrape and Email Reviews"):
    if not url:
        st.error("Please enter a Trustpilot URL")
    elif "trustpilot.com/review/" not in url:
        st.error("Please enter a valid Trustpilot URL")
    elif not email:
        st.error("Please enter your email address")
    else:
        reviews = scrape_trustpilot_reviews(url, num_pages)
        
        if reviews:
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['text', 'rating', 'date'])
            writer.writeheader()
            writer.writerows(reviews)
            csv_content = output.getvalue()
            
            # Extract company name from URL
            company_name = url.replace("https://www.trustpilot.com/review/", "").split("?")[0]
            
            # Send email
            try:
                send_email_with_csv(email, csv_content, company_name, len(reviews))
                st.success(f"✅ Done! {len(reviews)} reviews sent to {email}")
            except Exception as e:
                st.error(f"Failed to send email: {type(e).__name__}: {e}")
                import traceback
                st.code(traceback.format_exc())
            
            # Also offer download
            st.download_button(
                label="📥 Download CSV",
                data=csv_content,
                file_name="trustpilot_reviews.csv",
                mime="text/csv"
            )
        else:
            st.warning("No reviews found. Check the URL and try again.")

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_ebay(search_term, num_pages):
   results = []
   
   for page in range(1, num_pages + 1):
      url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_pgn={page}"
      headers = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }
      response = requests.get(url, headers=headers)
      soup = BeautifulSoup(response.text, 'html.parser')
   
      items = soup.select("li.s-item")

      for item in items:
         title_tag = item.select_one(".s-item__title")
         price_tag = item.select_one(".s-item__price")
         shipping_tag = item.select_one(".s-item__shipping")
         link_tag = item.select_one(".s-item__link")

         title = title_tag.text if title_tag else None
         price = price_tag.text if price_tag else None
         shipping = shipping_tag.text if shipping_tag else None
         link = link_tag['href'] if link_tag else None

         if title and price:
            results.append({
               "Title": title,
               "Price": price,
               "Shipping": shipping,
               "Link": link
            })
         
      print(f"Page {page} scraped successfully.")
      time.sleep(4)

   return pd.DataFrame(results)

def save_to_csv(df,filename="data/ebay_results.csv"):
   df.to_csv(filename, index=False)
   print(f"Data saved to {filename}")

if __name__ == "__main__":
   
   print("\nWelcome to the eBay Scraper! This is a simple web scraper that collects data from eBay listings which I made for educational purposes\n")
   search = input("\nEnter the search term: ").strip()
   pages = int(input("\nEnter the number of pages to scrape: ").strip())
   print(f"\nSearching for: {search} on eBay")
   print(f"\nNumber of pages to scrape: {pages}")
   print("-----------------------------\n")
   df = scrape_ebay(search, pages)
   print("Scraping completed.")
   save_to_csv(df)

   df = pd.read_csv("data/ebay_results.csv")
          
   print(df.head())
   print(df.columns)
   
   

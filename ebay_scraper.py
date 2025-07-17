import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

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
         location_tag = item.select_one(".s-item__location")
         link_tag = item.select_one(".s-item__link")
         

         title = title_tag.text if title_tag else None
         price = price_tag.text if price_tag else None
         shipping = shipping_tag.text if shipping_tag else None
         location = location_tag if location_tag else None
         link = link_tag['href'] if link_tag else None

         if title and price:
            results.append({
               "Title": title,
               "Price": price,
               "Shipping": shipping,
               "Location": location.text if location else None,
               "Link": link
            })
         
      print(f"Page {page} scraped successfully.")
      time.sleep(4)

   return pd.DataFrame(results)

def save_to_csv(df,filename="data/ebay_results.csv"):
   df.to_csv(filename, index=False)
   print(f"Data saved to {filename}")

def clean_price(price):
   if not isinstance(price,str):
      return None
   match = re.search(r"\$([\d,.]+)",price)
   if match:
      return float(match.group(1).replace(',', ''))
   return None

def clean_location(location):
   if not isinstance(location, str):
      return None
   match = re.search(r"\bLocated in \b",location)
   if match:
      return location.replace(match.group(0), '').strip()
   return None

def clean_shipping(shipping):
   if not isinstance(shipping, str):
      return None
   match = re.search(r"\+\$(\d+(?:\.\d{1,2})?)\s*delivery", shipping, flags=re.IGNORECASE)
   if match:
      return float(match.group(1))
   return None

if __name__ == "__main__":
   
   print("\nWelcome to the eBay Scraper! This is a simple web scraper that collects data from eBay listings which I made for educational purposes\n")
   
   ans = input("Do you want to scrape eBay? (yes/no): ").strip().lower()
   if ans == 'yes':
      print("\nGreat! Let's get started.\n")
      search = input("Enter the search term: ").strip()
      pages = int(input("\nEnter the number of pages to scrape: ").strip())
      print(f"\nSearching for: {search} on eBay")
      print(f"\nNumber of pages to scrape: {pages}")
      print("-----------------------------\n")
      df = scrape_ebay(search, pages)
      print("Scraping completed.")
      save_to_csv(df)

   df = pd.read_csv("data/ebay_results.csv")
          
   #Exploratory data analysis in python
   print("\nPrinting 5 entries: \n",df.head())
   print("\nNaming columns: \n",df.columns)
   print("\nChecking entries for price\n",df["Price"].unique()[:10]) #This is to check the unique values in the price column

   #Removing characters for the columns
   df["Clean_Price"] = df["Price"].apply(clean_price)
   
   df["Clean_Location"] = df["Location"].apply(clean_location)
  
   df["Clean_Shipping"] = df["Shipping"].apply(clean_shipping)
   print("\nPrinting 5 entries with the location cleaned: \n",df.head())

   print("Printing all null values in the columns:")
   print("Title: ", df["Title"].isnull().sum())
   print("Shipping: ", df["Shipping"].isnull().sum())
   print("Price: ", df["Clean_Price"].isnull().sum())
   print("Location", df["Clean_Location"].isnull().sum())
   print("Link: ", df["Link"].isnull().sum())
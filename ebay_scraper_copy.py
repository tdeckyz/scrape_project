import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import matplotlib.pyplot as plt
import seaborn as sns

def scrape_ebay(search_term, num_pages):
   results = []
   
   for page in range(1, num_pages + 1):
      url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_pgn={page}"
      headers = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }
      try:
         response = requests.get(url, headers=headers)
         soup = BeautifulSoup(response.text, 'html.parser')
      except requests.exceptions.RequestException as e:
         print(f"Failed to retrieve page {page}: {e}")
         continue
      
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
   match = re.search(r"\$([\d,.]+)",price) #regular expression to find entries with dollar sign and numbers followed by a comma or period
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
   
   #Replacing "Free International Shipping with FIS"
   if "Free" in shipping:
      return 0.0
   match = re.search(r"\+\$(\d+(?:\.\d{1,2})?)\s*delivery", shipping, flags=re.IGNORECASE)
   if match:
      return float(match.group(1))
   return None
def clean_data(df):
   #deleting rows with the title "Shop on eBay"
   df = df[~df["Title"].str.strip().str.lower().eq("shop on ebay")]
   #Removing characters for the columns
   df = df.copy()
   df.loc[:,"Clean_Price"] = df["Price"].apply(clean_price)
   df.loc[:,"Clean_Location"] = df["Location"].apply(clean_location)
   df.loc[:,"Clean_Shipping"] = df["Shipping"].apply(clean_shipping)

   print("Printing all null values in the columns:")
   print("Title: ", df["Title"].isnull().sum())
   print("Shipping: ", df["Shipping"].isnull().sum())
   print("Price: ", df["Clean_Price"].isnull().sum())
   print("Location", df["Clean_Location"].isnull().sum())
   print("Link: ", df["Link"].isnull().sum())

   cleaned_df = df[["Title", "Clean_Price", "Clean_Location", "Clean_Shipping", "Link"]].copy()
   
   #Renaming the columns
   cleaned_df.rename(columns={
       "Clean_Price": "Price",
       "Clean_Location": "Location",
       "Clean_Shipping": "Shipping"
   }, inplace=True)
   return cleaned_df

def visualize_data(df):
   sns.histplot(df['Price'])


if __name__ == "__main__":
   print("\nWelcome to the eBay Scraper! This is a simple web scraper that collects data from eBay listings which I made for educational purposes")
   print("Great! Let's get started.\n")
   search = input("Enter the search term: ").strip()
   pages = int(input("Enter the number of pages to scrape: ").strip())
   print(f"Searching for: {search} on eBay")
   print(f"Number of pages to scrape: {pages}")
   print("-----------------------------\n")
   df = scrape_ebay(search, pages)
   print("Scraping completed.")
   print("\nCleaning the data...\n")
   cleaned_df = clean_data(df)
   save_to_csv(cleaned_df)
   
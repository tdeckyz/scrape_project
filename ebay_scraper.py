import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

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


st.title('eBay Scraper And Analytics Dashboard')
st.write("Collect, clean, visualize, and analyze eBay listing for educational insights.")

#Inputs
search_term = st.text_input("Enter the search item: ")
num_pages = st.number_input("Number of pages to scrape: ", min_value = 1, max_value = 20, value =1)

#Scraping
if st.button("Scrape eBay"):
   if not search_term:
      st.warning("Please enter the search term.")
   else:
      with st.spinner("Scrapping eBay ..."):
         df = scrape_ebay(search_term, num_pages)
         cleaned_df = clean_data(df)

      st.success(f"Scraping completed! Found {len(cleaned_df)} items.")
      st.subheader("Data Table")
      st.dataframe(cleaned_df)

      st.subheader("Visualizations")
      st.subheader("Overall Insights: ")
      st.markdown("These visualizations allow quick analysis of price trends, shipping patterns, regional differences, and product features, providing actionable insights for market analysis, pricing strategy, and product research.")

      if not cleaned_df.empty:
         #Price distribution
         st.markdown("Price distribution")
         fig, ax  = plt.subplots()
         sns.histplot(cleaned_df['Price'], kde=True, ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_ylabel("Count")
         ax.set_title("Distribution of item prices")
         st.pyplot(fig)
         st.markdown("The histogram shows how item prices are spread. Most items are clustered in the lower price range, indicating a competitive" \
         " market for affordable products. Outliers on the higher end suggest premium or rare items")

         #Shipping cost distribution
         st.markdown("Shipping cost distribution")
         fig, ax = plt.subplots()
         sns.histplot(cleaned_df["Shipping"].dropna(),bins=20, kde=False, ax=ax)
         ax.set_xlabel("Shipping Cost (USD)")
         ax.set_ylabel("Count")
         ax.set_title("Distribution of shipping costs")
         st.pyplot(fig)
         st.markdown("Reveals that many items offer free shipping (0 USD), while some charge delivery fees. Highlights seller strategies and buyer preferences. " \
         "Free shipping is common, but some sellers charge for delivery, indicating a mix of pricing strategies in the eBay marketplace.")

         #Average price by location
         avg_price_by_location = (
            cleaned_df.dropna(subset=["Location","Price"])
            .groupby("Location")["Price"].mean()
            .sort_values(ascending= False)
            .head(10)   #keeps the top 10 locations.
            )
         fig, ax = plt.subplots(figsize=(8, 5))
         sns.barplot(x=avg_price_by_location.values, y=avg_price_by_location.index, ax=ax)
         ax.set_xlabel("Average Price (USD)")
         ax.set_ylabel("Location")
         ax.set_title("Top 10 Locations by Average Price")
         st.pyplot(fig)
         st.markdown("This bar chart shows the top 10 locations with the highest average item prices. It highlights regional price variations, " \
                     "indicating where buyers might find more expensive items.")

         # --- Scatter Plot: Price vs Shipping ---
         st.markdown("### Price vs Shipping Cost")
         fig, ax = plt.subplots()
         sns.scatterplot(data=cleaned_df.dropna(subset=["Price", "Shipping"]), x="Price", y="Shipping", ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_ylabel("Shipping Cost (USD)")
         ax.set_title("Price vs Shipping Cost")
         st.pyplot(fig)
         st.markdown("This scatter plot illustrates the relationship between item prices and shipping costs on eBay. It helps identify trends, " \
         "such as whether higher-priced items tend to have higher shipping costs.")

          # --- Boxplot of Prices ---
         st.markdown("### Boxplot of Prices")
         fig, ax = plt.subplots()
         sns.boxplot(x=cleaned_df["Price"].dropna(), ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_title("Boxplot of Item Prices")
         st.pyplot(fig)
         st.markdown("The boxplot provides a summary of item prices, showing the median, quartiles, and potential outliers. It helps identify " \
                     "the overall price distribution and any extreme values that may warrant further investigation.")

         # --- Wordcloud of Item Titles ---
         st.markdown("### Wordcloud of Item Titles")
         titles_text = " ".join(cleaned_df["Title"].dropna())
         wordcloud = WordCloud(width=800, height=400, background_color="white").generate(titles_text)
         fig, ax = plt.subplots(figsize=(10,5))
         ax.imshow(wordcloud, interpolation='bilinear')
         ax.axis("off")
         st.pyplot(fig)
         st.markdown("The wordcloud visualizes the most common words in item titles, highlighting key trends and popular categories in the eBay marketplace.")

      st.subheader("Download CSV")
      csv = cleaned_df.to_csv(index=False)
      st.download_button(
         label = "Download data as CSV",
         data = csv, 
         file_name = f"ebay_{search_term}.csv",
         mime = 'text/csv'
      )


import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sqlalchemy import create_engine

# Custom styling
st.markdown(
    """
    <style>
    /* Titles */
    h1 {
        text-align: center;
        color: #4CAF50;
        font-family: 'Arial Black', sans-serif;
    }
    h2, h3 {
        color: #333333;
        font-family: 'Arial', sans-serif;
    }

    /* Round DataFrames */
    .stDataFrame {
        border-radius: 10px;
        border: 1px solid #ddd;
    }

    /* Buttons */
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #45a049;
        color: white;
    }

    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

engine = create_engine('sqlite:///ebay_data.db')      #create SQLite DB file

def save_to_db(df,table_name="ebay_results"):
   df.to_sql(table_name, con=engine, if_exists = 'replace', index=False)
   st.success(f"Data saved to SQL table '{table_name}'")

def load_from_db(table_name = "ebay_results"):
   df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
   return df

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

   cleaned_df = df[["Title", "Clean_Price", "Clean_Location", "Clean_Shipping", "Link"]].copy()
   
   #Renaming the columns
   cleaned_df.rename(columns={
       "Clean_Price": "Price",
       "Clean_Location": "Location",
       "Clean_Shipping": "Shipping"
   }, inplace=True)
   return cleaned_df

st.sidebar.title("eBay Scraper")
st.title('eBay Scraper And Analytics Dashboard')
st.write("Collect, clean, visualize, and analyze eBay listing for educational insights.")

#Inputs
search_term = st.sidebar.text_input("Enter the search item: ")
num_pages = st.sidebar.number_input("Number of pages to scrape: ", min_value = 1, max_value = 20, value =1)

data_to_use = None

if st.sidebar.checkbox("Load data from database"):
   try:
      db_df = load_from_db()
      if db_df.empty:
         st.warning("No data to display.")
      else:
         #st.subheader("Data from Database")
         #st.dataframe(db_df)
         data_to_use = db_df #for visualizations
   except Exception as e:
      st.error(f"Failed to load data from database: {e}")


if st.button("Scrape eBay"):
   if not search_term:
      st.warning("Please enter the search term.")
   else:
      with st.spinner("Scrapping eBay ..."):
         df = scrape_ebay(search_term, num_pages)
         cleaned_df = clean_data(df)
         save_to_db(cleaned_df)

      with st.spinner("🔄 Scraping data... please wait"):
         time.sleep(2)  # Replace with your scraping function
      st.success(f"✅ Done! Scraping completed. Found {len(cleaned_df)} items.")
      #st.dataframe(cleaned_df)
      data_to_use = cleaned_df  #for visualizations

if data_to_use is not None and not data_to_use.empty:      
   st.subheader("Data Table")
   st.dataframe(data_to_use)

   #st.subheader("Visualizations")
   st.subheader("Overall Insights: ")
   st.markdown("These visualizations allow quick analysis of price trends, shipping patterns, regional differences, and product features, providing actionable insights for market analysis, pricing strategy, and product research.")

   if not data_to_use.empty:

      tab1, tab2, tab3 = st.tabs(["Price Distribution","Shipping Cost Distribution","Average Price by Location"])

      with tab1:
         #Price distribution
         fig, ax  = plt.subplots()
         sns.histplot(data_to_use['Price'], kde=True, ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_ylabel("Count")
         ax.set_title("Distribution of item prices")
         st.pyplot(fig)
         st.markdown("The histogram shows how item prices are spread. Most items are clustered in the lower price range, indicating a competitive" \
         " market for affordable products. Outliers on the higher end suggest premium or rare items")

      with tab2:
         #Shipping cost distribution
         fig, ax = plt.subplots()
         sns.histplot(data_to_use["Shipping"].dropna(),bins=20, kde=False, ax=ax)
         ax.set_xlabel("Shipping Cost (USD)")
         ax.set_ylabel("Count")
         ax.set_title("Distribution of shipping costs")
         st.pyplot(fig)
         st.markdown("Reveals that many items offer free shipping (0 USD), while some charge delivery fees. Highlights seller strategies and buyer preferences. " \
         "Free shipping is common, but some sellers charge for delivery, indicating a mix of pricing strategies in the eBay marketplace.")

      with tab3:
         #Average price by location
         avg_price_by_location = (
            data_to_use.dropna(subset=["Location","Price"])
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

      tab4, tab5, tab6 = st.tabs(["Price vs Shipping","Boxplot of Prices","Wordcloud of Titles"])

      with tab4:
         # --- Scatter Plot: Price vs Shipping ---
         fig, ax = plt.subplots()
         sns.scatterplot(data=data_to_use.dropna(subset=["Price", "Shipping"]), x="Price", y="Shipping", ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_ylabel("Shipping Cost (USD)")
         ax.set_title("Price vs Shipping Cost")
         st.pyplot(fig)
         st.markdown("This scatter plot illustrates the relationship between item prices and shipping costs on eBay. It helps identify trends, " \
         "such as whether higher-priced items tend to have higher shipping costs.")

      with tab5:
         # --- Boxplot of Prices ---
         fig, ax = plt.subplots()
         sns.boxplot(x=data_to_use["Price"].dropna(), ax=ax)
         ax.set_xlabel("Price (USD)")
         ax.set_title("Boxplot of Item Prices")
         st.pyplot(fig)
         st.markdown("The boxplot provides a summary of item prices, showing the median, quartiles, and potential outliers. It helps identify " \
                     "the overall price distribution and any extreme values that may warrant further investigation.")

      with tab6:
         # --- Wordcloud of Item Titles ---
         titles_text = " ".join(data_to_use["Title"].dropna())
         wordcloud = WordCloud(width=800, height=400, background_color="white").generate(titles_text)
         fig, ax = plt.subplots(figsize=(10,5))
         ax.imshow(wordcloud, interpolation='bilinear')
         ax.axis("off")
         st.pyplot(fig)
         st.markdown("The wordcloud visualizes the most common words in item titles, highlighting key trends and popular categories in the eBay marketplace.")

      
      save_to_db(data_to_use)
      csv = data_to_use.to_csv(index=False)
      st.sidebar.download_button(
         label = "Download data as CSV",
         data = csv, 
         file_name = f"ebay_{search_term}.csv",
         mime = 'text/csv'
      )


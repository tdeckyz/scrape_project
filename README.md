# eBay Web Scraper
A Python script that scrapes product listings from eBay using a search keyword and stores the data in a CSV file and provides analytics with visualization. Please note that this is solely made for education purpose. 

## Features

- Scrapes product title, price, shipping charge, location and link
- Cleans and structures data
- Saves results in CSV format
- Performs EDA using Python in Jupyter Notebook
- Provides insights:
    - Price distribution
    - Shipping analysis
    - Location-based pricing
    - Word cloud of product titles
- Download results as CSV

## Tech Stack

- Python 3
- Requests
- BeautifulSoup
- Pandas
- Streamlit
- matplotlib
- seaborn
- wordcloud
- sqlalchemy 


## Installation

```bash
git clone https://github.com/tdeckyz/scrap_project.git
pip install -r requirements.txt

## Run
run streamlit run app.py

## Demo
https://scrapeproject.streamlit.app/
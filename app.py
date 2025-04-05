import yfinance as yf
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def create_database():
    db = mysql.connector.connect(host="localhost", user="root", password="**your sql password**")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS project")
    db.close()

def create_tables():
    db = mysql.connector.connect(host="localhost", user="root", password="**your sql password**", database="project")
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(10) UNIQUE NOT NULL,
            name VARCHAR(100)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stock_id INT,
            date DATE,
            open_price FLOAT,
            close_price FLOAT,
            volume INT,
            FOREIGN KEY (stock_id) REFERENCES stocks(id)
        )
    """)
    db.commit()
    db.close()

def fetch_stock_data(symbol, period="1mo"):
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    data.reset_index(inplace=True)
    return data

def insert_stock_data(symbol, name, data):
    db = mysql.connector.connect(host="localhost", user="root", password="**your sql password**", database="project")
    cursor = db.cursor()
    cursor.execute("INSERT INTO stocks (symbol, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=name", (symbol, name))
    db.commit()
    cursor.execute("SELECT id FROM stocks WHERE symbol=%s", (symbol,))
    stock_id = cursor.fetchone()[0]
    
    for _, row in data.iterrows():
        cursor.execute("""
            INSERT INTO stock_prices (stock_id, date, open_price, close_price, volume)
            VALUES (%s, %s, %s, %s, %s)
        """, (stock_id, row["Date"].date(), row["Open"], row["Close"], row["Volume"]))
    
    db.commit()
    cursor.close()
    db.close()

def fetch_from_mysql(symbol):
    db = mysql.connector.connect(host="localhost", user="root", password="**your sql password**", database="project")
    cursor = db.cursor()
    cursor.execute("SELECT id FROM stocks WHERE symbol=%s", (symbol,))
    stock_id = cursor.fetchone()[0]
    cursor.execute("SELECT date, close_price FROM stock_prices WHERE stock_id=%s", (stock_id,))
    data = cursor.fetchall()
    db.close()
    return pd.DataFrame(data, columns=["Date", "Close Price"])

def plot_stock_data(df):
    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"], df["Close Price"], label="Closing Price")
    plt.xlabel("Date")
    plt.ylabel("Stock Price")
    plt.title("Stock Price Trend")
    plt.legend()
    plt.show()

def stock_dashboard():
    st.set_page_config(page_title="Stock Market Analysis", layout="wide")
    st.title("📈 Stock Market Analysis Dashboard")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        stock_symbol = st.text_input("🔍 Enter Stock Symbol (e.g., AAPL):", "AAPL")
        period = st.selectbox("⏳ Select Time Period:", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=0)
        
        if st.button("Fetch Data"):
            stock_data = fetch_stock_data(stock_symbol, period)
            insert_stock_data(stock_symbol, stock_symbol, stock_data)
            st.success("✅ Data Fetched and Stored Successfully!")
    
    with col2:
        if stock_symbol:
            df = fetch_from_mysql(stock_symbol)
            df["Date"] = pd.to_datetime(df["Date"])
            
            if not df.empty:
                st.subheader(f"📊 Stock Price Trend for {stock_symbol}")
                st.line_chart(df.set_index("Date")["Close Price"])
                
                st.subheader("📜 Data Table")
                st.dataframe(df.sort_values(by="Date", ascending=False))
                
                st.subheader("📌 Key Statistics")
                col3, col4, col5 = st.columns(3)
                col3.metric("📌 Latest Close Price", f"${df['Close Price'].iloc[-1]:.2f}")
                col4.metric("📊 Highest Close Price", f"${df['Close Price'].max():.2f}")
                col5.metric("📉 Lowest Close Price", f"${df['Close Price'].min():.2f}")
            else:
                st.warning("⚠ No data found for the selected stock.")

if __name__ == "__main__":
    create_database()
    create_tables()
    stock_dashboard()

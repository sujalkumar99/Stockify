from flask import Flask, render_template, request, redirect
import feedparser
import sqlite3
from flask import Flask, render_template, request
import yfinance as yf
import plotly.graph_objects as go
from ta.momentum import RSIIndicator

app = Flask(__name__)

app.secret_key = "stockify123"

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        if user:
            return redirect("/")
        else:
            return "Invalid Username or Password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            return "Registration Successful!"

        except:
            return "Username already exists!"

    return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
def home():

    stock = ""
    price = ""
    graph = ""
    rsi_value = ""
    company_name = ""
    sector = ""
    country = ""
    signal = ""
    news = []
    market_cap = ""
    pe_ratio = ""

    if request.method == "POST":

        stock = request.form["stock"].upper()

        # Indian stocks shortcut
        indian_stocks = [
            "IRB",
            "TCS",
            "INFY",
            "SBIN",
            "RELIANCE"
        ]

        if stock in indian_stocks:
            stock = stock + ".NS"

        # News
        feed = feedparser.parse(
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock}&region=US&lang=en-US"
        )

        for item in feed.entries[:5]:
            news.append(item.title)

        data = yf.Ticker(stock)
        info = data.info

        company_name = info.get("longName", "N/A")
        sector = info.get("sector", "N/A")
        country = info.get("country", "N/A")

        market_cap = round(
            info.get("marketCap", 0) / 10000000,
            2
        )

        pe_ratio = round(info.get("trailingPE", 0), 2)

        history_1d = data.history(period="1d")

        if not history_1d.empty:
            price = round(
                history_1d["Close"].iloc[-1],
                2
            )

        history = data.history(period="1mo")

        if not history.empty:

            rsi = RSIIndicator(
                history["Close"]
            ).rsi()

            rsi_value = round(
                rsi.iloc[-1],
                2
            )

            if rsi_value > 70:
                signal = "SELL 🔴"
            elif rsi_value < 30:
                signal = "BUY 🟢"
            else:
                signal = "HOLD 🟡"

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=history.index,
                        open=history["Open"],
                        high=history["High"],
                        low=history["Low"],
                        close=history["Close"]
                    )
                ]
            )

            fig.update_layout(
                title=stock,
                template="plotly_dark",
                autosize=True
            )

            graph = fig.to_html(
                full_html=False,
                config={"responsive": True}
            )

    return render_template(
        "index.html",
        stock=stock,
        price=price,
        rsi=rsi_value,
        signal=signal,
        company_name=company_name,
        sector=sector,
        country=country,
        market_cap=market_cap,
        pe_ratio=pe_ratio,
        graph=graph,
        news=news
    )

if __name__ == "__main__":
    app.run(debug=True)
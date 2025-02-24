import streamlit as st
import requests
import pandas as pd
import tweepy
import re

# FastAPI Backend URLs
FASTAPI_AUTH_URL = "http://127.0.0.1:8000"
FASTAPI_SENTIMENT_URL = "http://127.0.0.1:8001/predict/"

# Twitter API Credentials (Replace with your actual credentials)
TWITTER_BEARER_TOKEN = ""
client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

#  Streamlit Page Config
st.set_page_config(page_title="Sentiment Analysis", page_icon="💡", layout="wide")

#  Authentication State
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # Default Page is Login

# **Custom Styling (Modern UI)**
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            color: black;
        }
        .login-box {
            background-color: #e3f2fd; /* Light Blue */
            padding: 30px;
            border-radius: 12px;
            box-shadow: 2px 2px 15px rgba(0, 0, 0, 0.1);
            width: 40%;
            margin: auto;
            text-align: center;
        }
        .stTextInput>div>div>input, .stPassword>div>div>input {
            border-radius: 10px;
            padding: 12px;
            border: 1px solid #ddd;
        }
        .stButton>button {
            background-color: #007BFF !important;
            color: white !important;
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #0056b3 !important;
        }
        .stRadio>div {
            display: flex;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)

# **Login Page**
def login_page():
    # Clear any previous login input by explicitly setting default values.
    st.markdown("<h2 class='title'>🔐 Login</h2>", unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    # Using keys ensures these values are always reset.
    username = st.text_input("Username", key="login_username", value="")
    password = st.text_input("Password", type="password", key="login_password", value="")

    if st.button("Login"):
        response = requests.post(
            f"{FASTAPI_AUTH_URL}/login/", 
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            st.session_state.auth_token = response.json()["access_token"]
            st.success("✅ Login Successful!")
            st.session_state.page = "analysis"
            st.rerun()
        else:
            st.error("❌ Invalid Credentials")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Create an Account"):
        st.session_state.page = "register"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

#  **Register Page**
def register_page():
    st.markdown("<h2 class='title'>📝 Register</h2>", unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    new_username = st.text_input("New Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")

    if st.button("Register"):
        response = requests.post(
            f"{FASTAPI_AUTH_URL}/register/",
            json={"username": new_username, "email": new_email, "password": new_password}
        )
        if response.status_code == 200:
            st.success("✅ Registration Successful! Redirecting to Login...")
            st.session_state.page = "login"
            st.rerun()
        else:
            error_detail = response.json().get("detail", "")
            if isinstance(error_detail, list):
                message_displayed = False
                for err in error_detail:
                    loc = err.get("loc", [])
                    msg = err.get("msg", "").lower()
                    if "email" in loc:
                        st.error("❌ Error: Email format is not valid")
                        message_displayed = True
                        break
                    elif "username" in loc:
                        if "already exists" in msg:
                            st.error("❌ Error: Username already exists")
                        else:
                            st.error("❌ Error: Username is not valid")
                        message_displayed = True
                        break
                    elif "password" in loc:
                        if "at least 8 characters" in msg:
                            st.error("❌ Error: Password must be at least 8 characters")
                        else:
                            st.error("❌ Error: Password is not valid")
                        message_displayed = True
                        break
                if not message_displayed:
                    st.error(f"❌ Error: {error_detail}")
            else:
                st.error(f"❌ Error: {error_detail}")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 📌 **Main Sentiment Analysis Page**
def sentiment_analysis_page():
    st.title("💡 Sentiment Analysis")

    # Sidebar Navigation
    with st.sidebar:
        tab = st.radio("Navigation", ["Single Text Analysis", "Bulk CSV Analysis", "Twitter Sentiment Analysis"])

        #  Logout Button in Sidebar (Left Side at Bottom)
        if st.button("🚪 Logout", key="logout_button", help="Click to logout"):
            st.session_state.auth_token = None
            st.session_state.page = "login"
            st.rerun()

    # **🔍 SINGLE SENTENCE SENTIMENT ANALYSIS**
    if tab == "Single Text Analysis":
        st.subheader("🔍 Enter a Sentence to Analyze:")
        user_input = st.text_area("Enter your sentence here:", height=100)

        if st.button("🚀 Analyze Sentiment"):
            if user_input.strip():
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                response = requests.post(FASTAPI_SENTIMENT_URL, json={"text": user_input}, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    sentiment_label = result["sentiment"]
                    confidence = result["confidence"]
                    st.write(f"📊 **Sentiment:** {sentiment_label}")
                    st.write(f"💡 **Confidence Score:** {confidence:.2f}")
                else:
                    st.error("❌ API Error: Backend not responding.")

    # ** BULK CSV SENTIMENT ANALYSIS**
    if tab == "Bulk CSV Analysis":
        st.subheader("📂 Upload a CSV File")
        uploaded_file = st.file_uploader("Upload a CSV file with a 'text' column", type=['csv'])

        if uploaded_file:
            data = pd.read_csv(uploaded_file)
            if 'text' not in data.columns:
                st.error("🚫 The uploaded file must contain a 'text' column.")
            else:
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                predictions = [requests.post(FASTAPI_SENTIMENT_URL, json={"text": text}, headers=headers).json() for text in data['text']]
                data["Sentiment"] = [p["sentiment"] for p in predictions]
                data["Confidence"] = [p["confidence"] for p in predictions]
                
                st.dataframe(data)
                
                # Provide option to download the CSV file
                csv = data.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name='sentiment_analysis.csv', mime='text/csv')

    # ** REAL-TIME TWITTER SENTIMENT ANALYSIS**
    if tab == "Twitter Sentiment Analysis":
        st.subheader("🐦 Enter a Twitter Username:")
        twitter_username = st.text_input("Enter Twitter username (without @)")

        if st.button("🔍 Fetch & Analyze Tweets"):
            if twitter_username.strip():
                with st.spinner("Fetching latest tweets..."):
                    try:
                        user = client.get_user(username=twitter_username)
                        tweets = client.get_users_tweets(id=user.data.id, max_results=10, tweet_fields=["text"])

                        if tweets.data:
                            tweet_texts = [tweet.text for tweet in tweets.data]
                            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                            predictions = [requests.post(FASTAPI_SENTIMENT_URL, json={"text": text}, headers=headers).json() for text in tweet_texts]
                            
                            sentiment_data = pd.DataFrame({
                                "Tweet": tweet_texts,
                                "Sentiment": [p["sentiment"] for p in predictions],
                                "Confidence": [p["confidence"] for p in predictions]
                            })

                            st.write("### 📊 Sentiment Analysis of Tweets")
                            st.dataframe(sentiment_data)
                        else:
                            st.warning(f"⚠️ No tweets found for @{twitter_username}")

                    except Exception as e:
                        st.error(f"❌ Error fetching tweets: {e}")

#  **Page Routing**
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "register":
    register_page()
else:
    sentiment_analysis_page()

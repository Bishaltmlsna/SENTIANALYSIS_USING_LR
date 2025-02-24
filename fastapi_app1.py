from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import joblib
from sqlalchemy.orm import Session
import database
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Load Sentiment Model & Vectorizer
model = joblib.load("sentiment_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# 🔐 JWT Authentication
SECRET_KEY = "493869e1fabb5f07a2bcba608030c78b2eccd81cfaa5ebe8c97c81c5db584618"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

#  Token Verification
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")  # Return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

#  Sentiment Analysis Model Input
class TextInput(BaseModel):
    text: str

#  Sentiment Prediction API
@app.post("/predict/")
async def predict_sentiment(data: TextInput, user: str = Depends(verify_token), db: Session = Depends(database.get_db)):
    input_tfidf = vectorizer.transform([data.text])
    prediction = model.predict(input_tfidf)[0]
    confidence = model.predict_proba(input_tfidf)[0].max()
    sentiment_label = "Positive 😀" if prediction == 1 else "Negative 😔"
 #  Get the user object from the database
    db_user = db.query(database.User).filter(database.User.username == user).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store the result in the database
    new_entry = database.SentimentAnalysis(
        user_id=db_user.id,
        text=data.text,
        sentiment=sentiment_label
    )
    
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    return {"sentiment": sentiment_label, "confidence": round(float(confidence), 2)}

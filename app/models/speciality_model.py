import re
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
import joblib

nltk.download("stopwords", quiet=True)
arabic_stopwords = set(stopwords.words("arabic"))


def get_ml_model():
    try:
        model_path = "/home/sara/FastAPI/linear_svm_model.pkl"
        checkpoint = joblib.load(model_path)
        print("ML Model loaded successfully")  
        return checkpoint["model"], checkpoint["label_encoder"]
    except Exception as e:
        print(f"ML Model loading failed: {e}")
        return None, None


def get_embedding_model():
    return SentenceTransformer("intfloat/multilingual-e5-large")


def preprocess_question(question: str) -> str:
    ques = re.sub(r"[\u200e\u200f\u202a-\u202e؟]", " ", question)
    ques = re.sub(r"[^\u0600-\u06FFa-zA-Z\s-]", " ", ques)
    ques = re.sub(r"\s+", " ", ques).strip()
    ques = re.sub(r"[إأآا]", "ا", ques)
    ques = re.sub(r"ى", "ي", ques)
    ques = re.sub(r"ة", "ه", ques)
    ques = re.sub(r"ؤ", "و", ques)
    ques = re.sub(r"ئ", "ي", ques)
    ques = re.sub(r"ـ", "", ques)
    pattern = r"(?<!-)\b([a-zA-Z]+(?:\s+[a-zA-Z]+)+)\b"
    ques = re.sub(pattern, lambda m: m.group(1).replace(" ", "-"), ques)
    tokens = ques.split()
    tokens = [t for t in tokens if t not in arabic_stopwords]
    return " ".join(tokens)


def embed_texts(text_list, embedding_model):
    prefixed_texts = ["query: " + t for t in text_list]
    embeddings = embedding_model.encode(
        prefixed_texts,
        batch_size=16,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings


def predict_speciality(question: str, app_state=None) -> str:
    if not question.strip():
        return "General"

    try:
        if app_state is None:
            return "General"

        linear_svm = app_state.linear_svm
        le = app_state.label_encoder
        e5_model = app_state.embedding_model

        if linear_svm is None or le is None or e5_model is None:
            return "General"

        processed = preprocess_question(question)
        emb = embed_texts([processed], e5_model)
        pred_idx = linear_svm.predict(emb)[0]
        specialty = le.inverse_transform([pred_idx])[0]

        return specialty
    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return "General"
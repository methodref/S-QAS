from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba

vectorizer = None

def load_model():
    global vectorizer
    if vectorizer is None:
        vectorizer = TfidfVectorizer(tokenizer=jieba.lcut, analyzer='word')
    return vectorizer

def encode_texts(texts):
    load_model()
    if not texts:
        return []
    return vectorizer.fit_transform(texts)

def find_best_match(query, questions, top_k=1, threshold=0.3):
    if not questions:
        return None, 0

    question_texts = [q['question'] for q in questions]
    all_texts = question_texts + [query]

    tfidf_matrix = encode_texts(all_texts)
    
    query_vector = tfidf_matrix[-1]
    question_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(query_vector, question_vectors)[0]

    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])

    if best_score < threshold:
        return None, 0

    return questions[best_idx], best_score
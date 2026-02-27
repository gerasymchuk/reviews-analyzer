import html
import unicodedata
import re
from app.models.review import Review

def unescape_html(text: str) -> str:
    return html.unescape(text)  # "&amp;" → "&", "&#39;" → "'"

def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)

def remove_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text)

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def strip_control_chars(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

def moderate_repeats(text: str) -> str:
    return re.sub(r"(.)\1{3,}", r"\1\1\1", text)  # "!!!!!!!!" → "!!!" (max 3)

def is_too_short(text: str, min_len: int = 3) -> bool:
    return len(text) <= min_len


def remove_duplicates(reviews: list[Review]) -> list[Review]:
    unique_reviews = []
    seen_keys = set()
    for r in reviews:
        if (r.title, r.content) not in seen_keys:
            seen_keys.add((r.title, r.content))
            unique_reviews.append(r)
    return unique_reviews

def clean_text(text: str) -> str:
    text = unescape_html(text)
    text = normalize_unicode(text)
    text = remove_urls(text)
    text = strip_control_chars(text)
    text = normalize_whitespace(text)
    text = moderate_repeats(text)
    return text

def preprocess_review(review: Review) -> Review | None:
    title = clean_text(review.title)
    content = clean_text(review.content)

    if is_too_short(content):
        return None
    return Review(title=title, content=content, rating=review.rating)

def preprocess_reviews(reviews: list[Review]) -> list[Review]:
    cleaned = [preprocess_review(r) for r in reviews]
    cleaned = [r for r in cleaned if r is not None]
    return remove_duplicates(cleaned)
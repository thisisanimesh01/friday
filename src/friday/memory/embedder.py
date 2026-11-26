import os
import sys
import io
import logging
import warnings

# Mute noisy huggingface / transformers warning banners
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

# Suppress at Python stream level ONLY — do NOT use os.dup2 which corrupts PTY FDs
_null = io.StringIO()
_saved_stdout = sys.stdout
_saved_stderr = sys.stderr
sys.stdout = _null
sys.stderr = _null
try:
    from sentence_transformers import SentenceTransformer
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        # If model cannot be loaded (no internet or HF issues), fall back to a lightweight deterministic embedder
        model = None
        fallback_msg = f"SentenceTransformer unavailable: {e}"
        logging.getLogger("embedder").warning(fallback_msg)
except ImportError:
    model = None
finally:
    sys.stdout = _saved_stdout
    sys.stderr = _saved_stderr


def embed(text: str) -> list[float]:
    """Generate normalized vector embedding for text.

    Uses SentenceTransformer if available; otherwise uses a deterministic word-frequency
    and character-ngram feature hashing vector that preserves lexical similarity.
    """
    if model:
        try:
            return model.encode(text, show_progress_bar=False).tolist()
        except Exception:
            pass

    # Deterministic lexical-semantic feature hashing vector (dimension 128)
    # Maps overlapping word tokens and character 3-grams to index bins
    import re
    import hashlib

    dim = 128
    vec = [0.0] * dim

    clean_text = text.lower().strip()
    words = re.findall(r"\b\w+\b", clean_text)
    if not words and clean_text:
        words = [clean_text]

    # 1. Word unigram features
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += 2.0 * sign

    # 2. Character 3-gram features
    padded = f" {clean_text} "
    for i in range(len(padded) - 2):
        ngram = padded[i:i+3]
        h = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += 0.5 * sign

    # L2 normalize
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]

    return vec

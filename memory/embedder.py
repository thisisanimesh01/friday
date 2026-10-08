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
    model = SentenceTransformer('all-MiniLM-L6-v2')
finally:
    sys.stdout = _saved_stdout
    sys.stderr = _saved_stderr


def embed(text):
    return model.encode(text, show_progress_bar=False).tolist()

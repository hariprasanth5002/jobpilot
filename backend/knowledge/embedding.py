from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

# Lightweight local embedding model for the MVP (384-dimensional vectors)
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Singleton-style service to manage sentence-transformers model loading and encoding.
    Ensures the model is loaded only once in memory.
    """

    _instance: Optional["EmbeddingService"] = None

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name: str = model_name
        self._model: Optional[SentenceTransformer] = None

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def get_dimension(self) -> int:
        """
        Returns the embedding dimension of the loaded model.
        """
        if hasattr(self.model, "get_embedding_dimension"):
            dim = self.model.get_embedding_dimension()
        else:
            dim = self.model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384

    def encode(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Accepts a list of chunk texts and returns their embeddings as a NumPy array.
        When normalize=True, vectors are normalized to unit L2 norm.
        """
        if not texts:
            dim = self.get_dimension()
            return np.empty((0, dim), dtype=np.float32)

        # Generate embeddings using sentence-transformers
        raw_embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        embeddings = np.asarray(raw_embeddings, dtype=np.float32)

        if normalize:
            embeddings = normalize_embeddings(embeddings)

        return embeddings


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    Normalize every embedding vector to unit L2 norm:
    normalized_vector = vector / ||vector||2
    """
    if embeddings.size == 0:
        return embeddings

    # Compute L2 norm across axis 1
    norms = np.linalg.norm(embeddings, ord=2, axis=1, keepdims=True)

    # Avoid division by zero with small epsilon
    norms = np.where(norms == 0, 1e-12, norms)

    normalized = embeddings / norms
    return normalized.astype(np.float32)


def generate_embeddings(
    texts: List[str],
    model_name: str = DEFAULT_MODEL_NAME,
    normalize: bool = True,
) -> np.ndarray:
    """
    Convenience function to generate embeddings for a list of texts
    using the cached embedding service.
    """
    service = EmbeddingService.get_instance(model_name=model_name)
    return service.encode(texts, normalize=normalize)

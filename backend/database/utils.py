import hashlib
import uuid


def document_id_from_seed(seed: str) -> str:
    """Generate a deterministic UUID from a seed string to avoid duplicates"""
    seed_hash = hashlib.sha256(seed.encode('utf-8')).digest()
    generated_uuid = uuid.UUID(bytes=seed_hash[:16], version=4)
    return str(generated_uuid)

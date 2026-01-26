# services/hash_chain.py
"""
TrackRecord Hash Chain - Immutable Prediction Verification

This module implements a hash chain for predictions, ensuring:
1. Each prediction's content is hashed (content_hash)
2. Each prediction links to the previous one (chain_hash)
3. Any tampering breaks the chain and is detectable

Hash Structure:
- content_hash = SHA256(claim + quote + source_url + captured_at)
- chain_hash = SHA256(content_hash + prev_chain_hash + chain_index)

The chain is append-only and tamper-evident.
"""

import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


# Genesis hash - the first prediction links to this
GENESIS_HASH = "0" * 64  # 64 zeros represents the genesis block


@dataclass
class HashChainResult:
    """Result of hash chain computation"""
    content_hash: str
    chain_hash: str
    chain_index: int
    prev_chain_hash: str
    is_valid: bool = True


def compute_content_hash(
    claim: str,
    quote: str,
    source_url: str,
    captured_at: datetime
) -> str:
    """
    Compute the content hash for a prediction.
    This hash represents the immutable content of the prediction.
    """
    # Normalize the timestamp to ISO format
    timestamp_str = captured_at.isoformat() if isinstance(captured_at, datetime) else str(captured_at)
    
    # Combine all content
    content = f"{claim}|{quote}|{source_url}|{timestamp_str}"
    
    # SHA-256 hash
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_chain_hash(
    content_hash: str,
    prev_chain_hash: str,
    chain_index: int
) -> str:
    """
    Compute the chain hash that links this prediction to the previous one.
    This creates the tamper-evident chain.
    """
    # Combine content hash with previous chain hash and index
    chain_content = f"{content_hash}|{prev_chain_hash}|{chain_index}"
    
    # SHA-256 hash
    return hashlib.sha256(chain_content.encode('utf-8')).hexdigest()


def create_chain_entry(
    claim: str,
    quote: str,
    source_url: str,
    captured_at: datetime,
    prev_chain_hash: Optional[str] = None,
    chain_index: Optional[int] = None
) -> HashChainResult:
    """
    Create a new hash chain entry for a prediction.
    
    Args:
        claim: The prediction claim
        quote: Original quote
        source_url: Source URL
        captured_at: When the prediction was captured
        prev_chain_hash: Hash of the previous prediction (None for first)
        chain_index: Position in chain (None to auto-compute as 1)
    
    Returns:
        HashChainResult with all computed hashes
    """
    # Compute content hash
    content_hash = compute_content_hash(claim, quote, source_url, captured_at)
    
    # Use genesis hash if no previous
    if prev_chain_hash is None:
        prev_chain_hash = GENESIS_HASH
    
    # Default chain index
    if chain_index is None:
        chain_index = 1
    
    # Compute chain hash
    chain_hash = compute_chain_hash(content_hash, prev_chain_hash, chain_index)
    
    return HashChainResult(
        content_hash=content_hash,
        chain_hash=chain_hash,
        chain_index=chain_index,
        prev_chain_hash=prev_chain_hash,
        is_valid=True
    )


def verify_chain_entry(
    claim: str,
    quote: str,
    source_url: str,
    captured_at: datetime,
    stored_content_hash: str,
    stored_chain_hash: str,
    stored_prev_hash: str,
    stored_chain_index: int
) -> Dict[str, Any]:
    """
    Verify that a prediction's hashes are valid and haven't been tampered with.
    
    Returns:
        Dict with verification results
    """
    # Recompute content hash
    computed_content_hash = compute_content_hash(claim, quote, source_url, captured_at)
    content_valid = computed_content_hash == stored_content_hash
    
    # Recompute chain hash
    computed_chain_hash = compute_chain_hash(
        stored_content_hash,  # Use stored to check chain integrity separately
        stored_prev_hash,
        stored_chain_index
    )
    chain_valid = computed_chain_hash == stored_chain_hash
    
    return {
        "is_valid": content_valid and chain_valid,
        "content_valid": content_valid,
        "chain_valid": chain_valid,
        "stored_content_hash": stored_content_hash,
        "computed_content_hash": computed_content_hash,
        "stored_chain_hash": stored_chain_hash,
        "computed_chain_hash": computed_chain_hash,
        "chain_index": stored_chain_index,
        "prev_hash": stored_prev_hash
    }


def verify_chain_link(
    current_chain_hash: str,
    current_prev_hash: str,
    previous_chain_hash: str
) -> bool:
    """
    Verify that two consecutive predictions are properly linked.
    
    Args:
        current_chain_hash: Chain hash of current prediction
        current_prev_hash: The prev_chain_hash stored in current prediction
        previous_chain_hash: The chain_hash of the previous prediction
    
    Returns:
        True if the link is valid
    """
    return current_prev_hash == previous_chain_hash


def format_hash_display(hash_str: str, length: int = 8) -> str:
    """
    Format a hash for display (truncated with ellipsis).
    
    Args:
        hash_str: Full 64-character hash
        length: Number of characters to show (default 8)
    
    Returns:
        Formatted string like "a1b2c3d4..."
    """
    if not hash_str:
        return "N/A"
    return f"{hash_str[:length]}..."


def get_verification_url(chain_hash: str, base_url: str = "https://trackrecord.life") -> str:
    """
    Generate a verification URL for a prediction.
    """
    return f"{base_url}/verify/{chain_hash}"

"""
Core LLM extraction module for matrimonial biodata.
Handles LLM API calls and orchestrates the extraction pipeline.
"""

from typing import Optional, List, Dict, Any
import os
import time
import re

from .config import LLM_CONFIG, EXTRACTION_SCHEMA
from .prompt_template import get_extraction_prompt, get_system_prompt
from .validators import safe_parse_response


# ============================================================
# Record splitting helpers
# ============================================================

def split_records(text: str) -> List[str]:
    """
    Split text into individual records using the '=============NEW DATA' delimiter.
    This handles files with multiple matrimonial records separated by delimiters.
    
    Returns:
        List of individual record texts
    """
    # Pattern: =============NEW DATA : XX=============
    pattern = r'=============NEW DATA\s*:\s*\d+\s*=+\s*\n'
    records = re.split(pattern, text)
    
    # Filter out empty records and strip whitespace
    records = [r.strip() for r in records if r.strip()]
    
    return records if records else [text]


# ============================================================
# Chunking helpers
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = 3000,
    overlap: int = 300
) -> List[str]:
    """
    Split large text into overlapping chunks for LLM processing.
    """
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def merge_profiles(profiles: List[Dict]) -> Dict:
    """
    Merge multiple extracted profile dicts.
    Select the single most-complete profile instead of merging across chunks.
    This avoids mixing fields from different persons when a document contains
    multiple biodata entries or when chunked extraction yields inconsistent
    results. The profile with the highest count of non-empty fields is chosen.
    """
    if not profiles:
        return dict(EXTRACTION_SCHEMA)

    def completeness_score(p: Dict) -> int:
        return sum(1 for v in p.values() if v not in (None, "", [], {}))

    # Pick the single profile with the highest completeness
    best = max(profiles, key=completeness_score)

    merged = dict(EXTRACTION_SCHEMA)
    for k, v in best.items():
        merged[k] = v

    return merged


# ============================================================
# LLM Extractor class
# ============================================================

class LLMExtractor:
    """
    LLM-based extractor for matrimonial biodata.
    Supports multiple SDK shapes (OpenAI, Google Generative SDK, or other SDKs
    that expose simple generate(...) methods). The code tries to be tolerant
    of different client APIs.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Prefer OpenAI API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided. Set OPENAI_API_KEY or LLM_API_KEY "
                "environment variable or pass api_key parameter."
            )

        # Default to configured model unless overridden in config or params
        self.model = model or LLM_CONFIG.get("model", "gpt-4o")
        self.config = LLM_CONFIG.copy()
        self.config["model"] = self.model
        self._client = None

    @property
    def client(self) -> Any:
        """Lazy-load LLM client. Try OpenAI SDK first."""
        if self._client is None:
            last_exc = None
            # Try OpenAI SDK first (if available)
            try:
                import openai  # type: ignore
                # new-ish OpenAI package exposes OpenAI client class
                if hasattr(openai, "OpenAI"):
                    try:
                        self._client = openai.OpenAI(api_key=self.api_key)
                    except Exception:
                        # fall back to module-level api_key
                        try:
                            openai.api_key = self.api_key
                        except Exception:
                            pass
                        self._client = openai
                else:
                    # legacy openai module
                    try:
                        openai.api_key = self.api_key
                    except Exception:
                        pass
                    self._client = openai
                return self._client
            except Exception as e:
                last_exc = e

            # As a last resort, raise a clear ImportError
            raise ImportError(
                "OpenAI SDK not found. Install it with: pip install openai"
            ) from last_exc

        return self._client

    def _list_available_models(self) -> List[str]:
        """
        Try several client APIs to list available models; return list of names or empty list.
        """
        try:
            client = self.client
            # Google-style
            if hasattr(client, "list_models"):
                res = client.list_models()
                if isinstance(res, dict) and "models" in res:
                    return [m.get("name") if isinstance(m, dict) else str(m) for m in res["models"]]
                try:
                    return [getattr(m, "name", str(m)) for m in res]
                except Exception:
                    return []
            # Google newer style: client.models.list()
            if hasattr(client, "models") and hasattr(client.models, "list"):
                res = client.models.list()
                models = getattr(res, "models", []) or []
                return [getattr(m, "name", str(m)) for m in models]
            # Some SDKs might expose .models or .available_models
            if hasattr(client, "models"):
                try:
                    models_attr = getattr(client, "models")
                    if callable(models_attr):
                        res = models_attr()
                        return [getattr(m, "name", str(m)) for m in res] if res else []
                    # if it's iterable
                    return [str(m) for m in models_attr]
                except Exception:
                    return []
            if hasattr(client, "available_models"):
                try:
                    return [str(m) for m in client.available_models()]
                except Exception:
                    return []
        except Exception:
            return []
        return []

    def _choose_fallback_model(self, available: List[str]) -> Optional[str]:
        """
        Pick a sensible fallback model from a list of available models.
        Preference is given to known OpenAI models that are likely supported.
        """
        if not available:
            return None
        preferred = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo",
        ]
        for p in preferred:
            for m in available:
                if p in m:
                    return m
        # fallback to first available
        return available[0]

    def _generate_with_client(self, client: Any, prompt: str) -> str:
        """
        Generic wrapper to call the client's generation API.
        Tries multiple call shapes and returns text output.
        """
        gen_kwargs = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.config.get("temperature", 0.1),
            "max_tokens": self.config.get("max_tokens", 1024),
            "top_p": self.config.get("top_p", 0.9),
        }

            # OpenAI-style SDK: client.chat.completions.create()
        try:
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=gen_kwargs["temperature"],
                    max_tokens=gen_kwargs["max_tokens"],
                    top_p=gen_kwargs["top_p"],
                )
                # OpenAI response typically has .choices[0].message.content
                if hasattr(resp, "choices") and resp.choices:
                    choice = resp.choices[0]
                    if hasattr(choice, "message") and hasattr(choice.message, "content"):
                        return choice.message.content
        except Exception:
            pass

        # Google-style GenerativeModel instance
        try:
            if hasattr(client, "GenerativeModel"):
                model = client.GenerativeModel(
                    model_name=self.model,
                    generation_config={
                        "temperature": gen_kwargs["temperature"],
                        "max_output_tokens": gen_kwargs["max_tokens"],
                        "top_p": gen_kwargs["top_p"],
                    },
                )
                resp = model.generate_content(prompt)
                # google responses often have .text
                if hasattr(resp, "text"):
                    return resp.text
                # sometimes response is dict-like
                if isinstance(resp, dict):
                    return resp.get("text") or str(resp)
        except Exception:
            pass

        # Other SDKs: try common method names
        call_order = ["generate", "generate_text", "completion", "create_completion"]
        for name in call_order:
            try:
                if hasattr(client, name):
                    fn = getattr(client, name)
                    # try calling with keyword args
                    try:
                        resp = fn(**gen_kwargs)
                    except TypeError:
                        # try alternative arg shapes
                        try:
                            resp = fn(prompt, self.model)
                        except Exception:
                            resp = fn(prompt)
                    # extract text from possible response shapes
                    if isinstance(resp, str):
                        return resp
                    if hasattr(resp, "text"):
                        return resp.text
                    if isinstance(resp, dict):
                        # check common keys
                        for k in ("text", "content", "output", "generated_text"):
                            if k in resp:
                                return resp[k]
                        # sometimes resp contains choices
                        if "choices" in resp and resp["choices"]:
                            c = resp["choices"][0]
                            if isinstance(c, dict) and ("text" in c or "message" in c):
                                return c.get("text") or c.get("message") or str(c)
                        return str(resp)
            except Exception:
                continue

        raise RuntimeError("Unable to call generation API with the discovered client.")

    def _extract_single_chunk(self, text: str) -> Dict:
        """
        Extract profile fields from a single text chunk using LLM.
        """
        user_prompt = get_extraction_prompt(text)
        system_prompt = get_system_prompt()

        try:
            # Build messages list for OpenAI API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response_text = self._openai_generate(messages)
        except Exception as e:
            msg = str(e)
            if "not found" in msg.lower() or "404" in msg:
                available = self._list_available_models()
                raise RuntimeError(
                    f"Model '{self.model}' not available for this API/version. "
                    f"Error: {msg}. Available models: {available}"
                ) from e
            raise

        return safe_parse_response(response_text, EXTRACTION_SCHEMA)

    def _openai_generate(self, messages: List[Dict]) -> str:
        """
        Call OpenAI-compatible chat API for chat completions.
        Handles both the modern `openai.OpenAI` client and the legacy `openai` module.
        """
        # Try once, and if we get a model-not-found/404 error, attempt a single
        # fallback to an available model and retry.
        last_exc = None
        for attempt in (1, 2):
            try:
                client = self.client
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.config.get("temperature", 0.1),
                    max_tokens=self.config.get("max_tokens", 1024),
                    top_p=self.config.get("top_p", 0.9),
                )
                # typical OpenAI response: .choices[0].message.content
                if hasattr(resp, "choices") and resp.choices:
                    choice = resp.choices[0]
                    if hasattr(choice, "message") and hasattr(choice.message, "content"):
                        return choice.message.content
                    # fallback for dict-like choices
                    if isinstance(choice, dict):
                        msg = choice.get("message") or choice
                        if isinstance(msg, dict):
                            return msg.get("content") or msg.get("text") or str(resp)
                # fallback when resp is dict-like
                if isinstance(resp, dict):
                    # try common keys
                    for k in ("text", "content", "output"):
                        if k in resp:
                            return resp[k]
                raise RuntimeError("Unexpected response format from OpenAI API")
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                # If this looks like a model-not-found / 404 error and this is
                # the first attempt, try to pick a fallback model and retry once.
                if attempt == 1 and ("not found" in msg or "does not exist" in msg or "model_not_found" in msg or "404" in msg or ("model" in msg and "not" in msg)):
                    try:
                        available = self._list_available_models()
                        fallback = self._choose_fallback_model(available)
                        if fallback and fallback != self.model:
                            print(f"Info: model '{self.model}' unavailable; retrying with fallback '{fallback}'")
                            self.model = fallback
                            self.config["model"] = fallback
                            continue
                    except Exception:
                        pass
                # otherwise raise a wrapped runtime error
                raise RuntimeError(f"OpenAI API error: {e}") from e
        # If we get here, raise the last exception
        raise RuntimeError(f"OpenAI API error: {last_exc}") from last_exc

    def extract(self, text: str) -> List[Dict]:
        """
        Extract matrimonial profile information from text.
        Handles multiple records separated by '=============NEW DATA' delimiters.
        For single records, uses chunked LLM calls.
        
        Returns:
            List[Dict]: List of extracted profiles. For files with multiple records, returns all of them.
                       For single records, returns list with one profile.
        """
        if not text or not text.strip():
            return [dict(EXTRACTION_SCHEMA)]

        # Split into individual records if multiple exist
        records = split_records(text)
        
        extracted_profiles = []
        
        for idx, record in enumerate(records):
            try:
                profile = self._extract_single_record(record)
                has_values = any(profile.values()) if isinstance(profile, dict) else False
                print(f"[DEBUG] Record {idx+1}: has_values={has_values}, dict={isinstance(profile, dict)}")
                if isinstance(profile, dict) and any(profile.values()):
                    # Apply final sanitization to remove any invalid data
                    print(f"[DEBUG] Before sanitization: state={profile.get('state')}")
                    profile = self._sanitize_final_profile(profile)
                    print(f"[DEBUG] After sanitization: state={profile.get('state')}")
                    extracted_profiles.append(profile)
                    if len(records) > 1:
                        print(f"Extracted record {idx + 1}/{len(records)}")
                else:
                    print(f"[DEBUG] Record {idx+1}: Skipped due to no values or not dict")
            except Exception as e:
                print(f"LLM extraction failed for record {idx + 1}: {e}")
                continue
            
            # Rate-limit protection
            time.sleep(0.5)
        
        return extracted_profiles if extracted_profiles else [dict(EXTRACTION_SCHEMA)]

    def _sanitize_final_profile(self, profile: Dict) -> Dict:
        """Apply field validation to remove mismatched data."""
        original_state = profile.get('state')
        try:
            from .field_validators import FieldValidator
            is_valid, errors = FieldValidator.validate_profile(profile)
            if errors:
                for field_name in errors:
                    print(f"Warning: Removing invalid data from '{field_name}'")
                    profile[field_name] = None
            # DEBUG: Always log state sanitization
            if original_state and profile.get('state') != original_state:
                print(f"DEBUG: State field changed from '{original_state}' to '{profile.get('state')}'")
        except Exception as e:
            print(f"Warning: Field validation failed: {e}")
        return profile

    def _extract_single_record(self, text: str) -> Dict:
        """
        Extract a single matrimonial record (may be chunked if large).
        """
        chunks = chunk_text(text)
        partial_profiles = []

        for idx, chunk in enumerate(chunks):
            try:
                profile = self._extract_single_chunk(chunk)
                if isinstance(profile, dict):
                    partial_profiles.append(profile)
            except Exception as e:
                print(f"LLM extraction failed for chunk {idx}: {e}")
                continue

            # Rate-limit protection (important for some LLM providers)
            time.sleep(0.5)

        if not partial_profiles:
            return dict(EXTRACTION_SCHEMA)

        return merge_profiles(partial_profiles)


# ============================================================
# Public functional API (used by pipeline)
# ============================================================

def extract_profile(
    text: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict]:
    """
    Public API for LLM extraction.
    
    Returns a list of profiles (one per record in the document).
    For documents with multiple matrimonial records, returns all of them.
    For single-record documents, returns a list with one profile.

    Used by Pipeline layer.
    """
    try:
        extractor = LLMExtractor(api_key=api_key, model=model)
        profiles = extractor.extract(text)
        # Ensure we always return a list
        if isinstance(profiles, list):
            return profiles
        else:
            return [profiles] if profiles else [dict(EXTRACTION_SCHEMA)]
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return [dict(EXTRACTION_SCHEMA)]

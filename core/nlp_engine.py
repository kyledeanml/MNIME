import os
import sys
import threading
import atexit
import signal
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QSettings

class NLPEngine:
    _instance = None
    
    def __init__(self):
        self.settings = QSettings("MNIME", "MNIMEApp")
        # Check for bundled model
        bundled_model = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "MNIME-Core-1.5B-Q4_K_M.gguf")
        default_path = bundled_model if os.path.exists(bundled_model) else ""
        
        saved_path = self.settings.value("gguf_model_path", "")
        if not saved_path or not os.path.exists(saved_path):
            self.model_path = default_path
            if default_path:
                self.settings.setValue("gguf_model_path", default_path)
        else:
            self.model_path = saved_path
        self.llm = None
        self.is_loaded = False
        self.is_loading = False
        self.error = None
        self._lock = threading.Lock()
        
        # Register cleanup for normal exit
        atexit.register(self.unload_model)
        
        # Register cleanup for crashes
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._crash_handler
        
        # Attempt to register signal handlers for termination
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception:
            pass

    def _crash_handler(self, exc_type, exc_value, exc_traceback):
        self.unload_model()
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _signal_handler(self, signum, frame):
        self.unload_model()
        sys.exit(0)

    def unload_model(self):
        with self._lock:
            if self.llm is not None:
                try:
                    self.llm.close()
                except AttributeError:
                    pass
                del self.llm
                self.llm = None
            self.is_loaded = False
            self.is_loading = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = NLPEngine()
        return cls._instance

    def set_model_path(self, path: str):
        self.model_path = path
        self.settings.setValue("gguf_model_path", path)
        self.reload_model()

    def reload_model(self):
        """Reload the model synchronously. Call _reload_model_async() to run on a background thread."""
        self.unload_model()
        self.error = None
        self.is_loading = True
        if not self.model_path or not os.path.exists(self.model_path):
            self.error = "Model path not set or file does not exist."
            self.is_loading = False
            return False

        try:
            from llama_cpp import Llama
            
            kwargs = {
                "model_path": self.model_path,
                "n_ctx": 4096,
                "n_threads": 8,
                "n_gpu_layers": -1,
                "main_gpu": 0,
                "use_mlock": False,
            }
            
            # Conditionally inject new features that might fail on older builds
            try:
                # Add flash attention if supported
                kwargs["flash_attn"] = True
                self.llm = Llama(**kwargs)
            except TypeError:
                # Fallback if specific flags like flash_attn or type_k are unsupported by this older llama-cpp-python version
                kwargs.pop("flash_attn", None)
                self.llm = Llama(**kwargs)
                
            self.is_loaded = True
            self.is_loading = False
            return True
        except Exception as e:
            self.error = str(e)
            self.is_loading = False
            return False

    def reload_model_async(self):
        """Reload the model on a background thread so the UI stays responsive."""
        t = threading.Thread(target=self.reload_model, daemon=True)
        t.start()

    def check_model(self):
        enabled = str(self.settings.value("nlp_enabled", "true")).lower() == "true"
        if not enabled:
            self.unload_model()
            self.error = "NLP is globally disabled via Tabs Bar toggle."
            return
        
        if not self.is_loaded:
            self.error = "Model not loaded. Click the reload button to start NLP."
            return

    def generate_response(self, prompt: str, context_docs: List[Dict[str, Any]]) -> str:
        self.check_model()
        if not self.is_loaded:
            return f"Error: {self.error}"

        context_text = "\n\n".join([f"Document ({doc.get('source', 'Unknown')}):\n{doc.get('content', '')}" for doc in context_docs])
        
        system_prompt = (
            "You are an advanced local NLP assistant for MNIME. "
            "Use the provided document context to answer the user's query accurately. "
            "If the answer is not in the context, state that clearly."
        )
        
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\nCONTEXT:\n{context_text}\n\nQUERY: {prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        
        try:
            response = self.llm(
                full_prompt,
                max_tokens=1024,
                stop=["<|im_end|>", "<|im_start|>"],
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error generating response: {e}"

    def synthesize_reference(self, source_text: str, context_docs: List[Dict[str, Any]]) -> str:
        self.check_model()
        if not self.is_loaded:
            return f"Error: {self.error}"

        context_text = "\n\n".join([f"Document ({doc.get('source', 'Unknown')}):\n{doc.get('content', '')}" for doc in context_docs])
        
        system_prompt = (
            "You are an advanced legal and document analysis NLP. "
            "The user has highlighted a specific section from one document. "
            "You are provided with semantic search results from other open documents in their workspace. "
            "Synthesize a comparative brief: analyze how the highlighted text relates, conflicts, or aligns with the other documents."
        )
        
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\nOTHER DOCUMENTS CONTEXT:\n{context_text}\n\nHIGHLIGHTED SOURCE TEXT:\n{source_text}<|im_end|>\n"
            f"<|im_start|>assistant\nCOMPARATIVE BRIEF:\n"
        )
        
        try:
            response = self.llm(
                full_prompt,
                max_tokens=1024,
                stop=["<|im_end|>", "<|im_start|>"],
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error generating synthesis: {e}"

    def generate_verbose_bookmark(self, heading_candidate: str, page_text: str) -> str:
        self.check_model()
        if not self.is_loaded:
            return heading_candidate

        # Create a fast, constrained prompt for a concise sub-60-char title
        system_prompt = (
            "You are an expert document summarizer. "
            "Based on the following page text, generate a single, highly concise bookmark title (under 60 characters) that summarizes the core topic. "
            "Do not include introductory text, quotes, or markdown. Just return the bookmark text."
        )
        
        # Limit page text to 1500 chars to speed up inference and avoid huge context
        safe_text = page_text[:1500].strip()
        
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\nHEADING CANDIDATE: {heading_candidate}\n\nPAGE TEXT:\n{safe_text}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        
        try:
            # Low max_tokens to force short generation
            response = self.llm(
                full_prompt,
                max_tokens=25,
                stop=["<|im_end|>", "<|im_start|>", "\n"],
                echo=False
            )
            title = response['choices'][0]['text'].strip()
            # Clean up potential leading/trailing quotes or punctuation if needed
            title = title.strip('\'"*- ')
            return title if title else heading_candidate
        except Exception:
            return heading_candidate

    def generate_smart_filename(self, page_text: str, fallback_name: str) -> str:
        self.check_model()
        if not self.is_loaded or not page_text.strip():
            return fallback_name

        system_prompt = (
            "You are an expert document archiver. "
            "Based on the following document text, generate a highly concise filename (under 40 characters) that summarizes the core topic. "
            "Use underscores instead of spaces. Do not include file extensions. "
            "If the text is empty or meaningless, just reply UNKNOWN."
        )

        safe_text = page_text[:1000].strip()
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\nDOCUMENT TEXT:\n{safe_text}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        # Use thread lock to prevent parallel crashing in Split PDF
        with self._lock:
            try:
                response = self.llm(
                    full_prompt,
                    max_tokens=20,
                    stop=["<|im_end|>", "<|im_start|>", "\n", "."],
                    echo=False
                )
                raw_name = response['choices'][0]['text'].strip()
                if "UNKNOWN" in raw_name.upper() or not raw_name:
                    return fallback_name

                # Sanitize filename
                import re
                clean_name = re.sub(r'[<>:"/\\|?*]', '', raw_name)
                clean_name = clean_name.replace(' ', '_')
                clean_name = clean_name.strip('\'"_-')
                return clean_name if clean_name else fallback_name
            except Exception:
                return fallback_name

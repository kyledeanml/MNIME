"""
Semantic Search Engine for OmniMesh.
Adapts the "CodeEyes" codebase semantic search concept for offline document/codebase querying.
"""

import os
import zipfile
import shutil
import time
import stat
import re
from collections import Counter
from typing import List, Callable, Optional, Dict, Any

from .file_item import FileItem


class SearchEngine:
    """Core backend engine for semantic search over codebases and text documents."""

    @staticmethod
    def _safe_remove_directory(directory_path: str):
        if not os.path.exists(directory_path):
            return
        def remove_readonly(func, p, _):
            os.chmod(p, stat.S_IWRITE)
            func(p)
        try:
            shutil.rmtree(directory_path, onexc=remove_readonly)
        except OSError:
            time.sleep(0.1)
            try:
                shutil.rmtree(directory_path, onexc=remove_readonly)
            except OSError:
                try:
                    trash_path = f"{directory_path}_trash_{int(time.time())}"
                    os.rename(directory_path, trash_path)
                except OSError:
                    pass

    @staticmethod
    def extract_probe_terms(contents: List[str], top_k: int = 20) -> List[str]:
        tokens = []
        for content in contents:
            tokens += re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", content)
        common = Counter(tokens).most_common(top_k)
        return [term for term, _ in common]

    @staticmethod
    def load_files(root_dir: str) -> List[Dict[str, Any]]:
        data_list = []
        ignore_dirs = {'.venv', 'venv', 'env', '.git', 'node_modules', '__pycache__', '.idea', '.vscode'}
        
        for root, dirs, files in os.walk(root_dir):
            # Skip ignored directories to avoid hanging on dependencies
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in (".py", ".txt", ".md", ".json", ".csv", ".js", ".ts", ".html", ".css", ".cpp", ".c", ".h", ".java"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f_reader:
                            content_str = f_reader.read()
                        data_list.append({
                            "path": fpath,
                            "content": content_str,
                            "lines": len(content_str.splitlines())
                        })
                    except (UnicodeDecodeError, PermissionError):
                        continue
        return data_list

    @staticmethod
    def build_index(
        file_item: FileItem,
        use_smart_sampling: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Any:
        """
        Extracts the given file (if zip), loads texts, and builds a FAISS vector index.
        Returns the FAISS vectorstore.
        """
        import pandas as pd
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        extract_dir = os.path.join(os.path.dirname(file_item.file_path), f"extracted_{int(time.time())}")
        
        if progress_callback:
            progress_callback(10, "Preparing files...")

        data_list = []
        if file_item.extension == ".zip":
            os.makedirs(extract_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(file_item.file_path, 'r') as z_ref:
                    z_ref.extractall(extract_dir)
                data_list = SearchEngine.load_files(extract_dir)
            except Exception as e:
                SearchEngine._safe_remove_directory(extract_dir)
                raise RuntimeError(f"Failed to extract or read ZIP: {e}")
            finally:
                SearchEngine._safe_remove_directory(extract_dir)
        else:
            if file_item.extension in (".py", ".txt", ".md", ".json", ".csv", ".js", ".ts", ".html", ".css", ".cpp", ".c", ".h", ".java"):
                try:
                    with open(file_item.file_path, 'r', encoding='utf-8') as f_reader:
                        content_str = f_reader.read()
                    data_list.append({
                        "path": file_item.file_path,
                        "content": content_str,
                        "lines": len(content_str.splitlines())
                    })
                except Exception:
                    pass

        if not data_list:
            raise ValueError("No valid text files found to index.")

        df = pd.DataFrame(data_list)

        if progress_callback:
            progress_callback(40, "Initializing Embedding Model...")

        emb = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        split = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

        if use_smart_sampling and len(df) > 0:
            if progress_callback:
                progress_callback(50, "Smart Indexing (Extracting Probe Terms)...")

            frac = min(0.1, 1.0) if len(df) > 10 else 1.0
            sample = df['content'].sample(frac=frac, random_state=42).tolist()
            p_terms = SearchEngine.extract_probe_terms(sample)

            final_docs = []
            for i, (_, row) in enumerate(df.iterrows()):
                chunks = split.split_text(row['content'])
                for chk in chunks:
                    if any(term in chk for term in p_terms):
                        final_docs.append(Document(page_content=chk, metadata={"source": row['path']}))
                
                if progress_callback:
                    pct = 50 + int((i / len(df)) * 40)
                    progress_callback(pct, f"Smart Indexing ({i+1}/{len(df)})...")
            
            if not final_docs:
                if progress_callback:
                    progress_callback(90, "Fallback: Full Indexing...")
                for _, row in df.iterrows():
                    final_docs.extend([Document(page_content=c, metadata={"source": row['path']}) for c in split.split_text(row['content'])])

            vstore = FAISS.from_documents(final_docs, emb)
            
        else:
            if progress_callback:
                progress_callback(50, "Full Indexing...")
                
            all_docs = []
            for i, (_, row) in enumerate(df.iterrows()):
                all_docs.extend([Document(page_content=c, metadata={"source": row['path']}) for c in split.split_text(row['content'])])
                if progress_callback:
                    pct = 50 + int((i / len(df)) * 40)
                    progress_callback(pct, f"Full Indexing ({i+1}/{len(df)})...")
            
            vstore = FAISS.from_documents(all_docs, emb)

        if progress_callback:
            progress_callback(100, "Index Ready!")

        return vstore

    @staticmethod
    def search(vectorstore: Any, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the built FAISS index.
        Returns a list of dicts with 'content' and 'source'.
        """
        if not vectorstore:
            return []
            
        hits = vectorstore.similarity_search(query, k=k)
        results = []
        for hit in hits:
            results.append({
                "content": hit.page_content,
                "source": hit.metadata.get("source", "Unknown")
            })
        return results

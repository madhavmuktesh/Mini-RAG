import re
import time
from openai import OpenAI, RateLimitError, APIConnectionError, OpenAIError

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.vectorstore import search


def extract_keywords(text: str):
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stopwords = {
        "what", "which", "when", "where", "who", "why", "how",
        "the", "and", "for", "are", "with", "this", "that",
        "from", "into", "based", "does", "have", "has", "had",
        "main", "project", "system"
    }
    return [w for w in words if w not in stopwords]


def build_fallback_answer(question: str, results):
    if not results:
        return "I could not find relevant information in the uploaded documents."

    top_text = results[0][0]["text"].strip()
    sentences = re.split(r'(?<=[.!?])\s+', top_text)
    question_keywords = extract_keywords(question)

    ranked = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = sum(1 for kw in question_keywords if kw in sentence_lower)
        ranked.append((score, sentence.strip()))

    ranked.sort(key=lambda x: x[0], reverse=True)
    best_sentences = [sentence for score, sentence in ranked if sentence][:2]

    if not best_sentences:
        best_sentences = sentences[:2]

    answer = " ".join(best_sentences).strip()
    if not answer:
        return "Relevant content was found, but a concise answer could not be extracted."

    return answer


def generate_answer(question: str, document_ids=None, top_k: int = 4):
    started = time.perf_counter()
    results = search(question, top_k=top_k, document_ids=document_ids)

    if not results:
        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "answer": "I could not find relevant information in the uploaded documents.",
            "sources": [],
            "latency_ms": round(latency_ms, 2),
            "top_score": None,
        }

    context_blocks = []
    for i, (record, score) in enumerate(results, start=1):
        context_blocks.append(
            f"[{i}] {record['filename']} | score={score:.4f}\n{record['text']}"
        )
    context = "\n\n".join(context_blocks)

    answer = None

    if GROQ_API_KEY:
        try:
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY,
            )

            prompt = f"""
You are a RAG question-answering assistant.
Answer the question using only the provided context.
Give a short, direct answer first.
If needed, add 1-2 supporting sentences.
If the context does not contain the answer, say so clearly.

Question:
{question}

Context:
{context}
""".strip()

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "Answer only from retrieved document context. Do not hallucinate.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            answer = response.choices[0].message.content.strip()

        except RateLimitError as e:
            print(f"Groq rate limit error: {e}")
        except APIConnectionError as e:
            print(f"Groq connection error: {e}")
        except OpenAIError as e:
            print(f"Groq/OpenAI-compatible API error: {e}")
        except Exception as e:
            print(f"Unexpected LLM error: {e}")

    if not answer:
        answer = build_fallback_answer(question, results)

    latency_ms = (time.perf_counter() - started) * 1000

    sources = [
        {
            "document_id": record["document_id"],
            "chunk_id": record["chunk_id"],
            "filename": record["filename"],
            "score": round(score, 4),
            "text": record["text"][:400],
        }
        for record, score in results
    ]

    return {
        "answer": answer,
        "sources": sources,
        "latency_ms": round(latency_ms, 2),
        "top_score": round(results[0][1], 4),
    }
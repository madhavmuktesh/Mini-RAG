# Mandatory Explanations

## Why This Chunk Size Was Chosen

This project uses **500-word chunks with 75-word overlap** as a practical baseline chunking strategy for document retrieval [1]. The chunk size was chosen to balance two competing goals: preserving enough context inside each chunk so the meaning of a section is not lost, while also keeping chunks small enough for effective similarity search and answer generation [1][2][3].

If chunks are too small, important context can be split across multiple chunks, which may hurt answer quality because retrieval might return only part of the needed information [2][3]. If chunks are too large, each chunk becomes semantically broad, which can reduce retrieval precision for narrow factual questions because unrelated nearby text is embedded together [4][5].

The 75-word overlap was added to reduce boundary loss between neighboring chunks and improve continuity when a concept spans the end of one chunk and the beginning of the next [2][3]. This strategy was selected because it is lightweight, easy to implement in a custom FastAPI pipeline, and strong enough for a small academic RAG system without depending on heavy frameworks [1].

## One Retrieval Failure Case Observed

One retrieval failure case observed in this project happens when the correct answer is spread across **two adjacent chunks**, but only one of those chunks is returned in the top-k similarity search results [1]. In that situation, the system may generate a partial answer even though the full answer exists in the source document, because the answer-generation stage can only use the context it receives [2][4].

Another related issue appears when a **broad chunk** is retrieved for a very specific question, such as a narrow factual query about the technical stack or one mandatory requirement [4][5]. In those cases, the returned chunk may contain the answer, but it also contains surrounding unrelated sections, which lowers precision and may make the response less focused [3][4].

This failure case shows that retrieval quality depends strongly on chunk size, overlap, and ranking strategy, which is why chunking was treated as a deliberate design decision in this system [2][4].

## One Metric Tracked

The main metric tracked in this project is **query latency in milliseconds (`latency_ms`)**, which measures the total time taken from receiving a user question to returning the final response [1]. This metric is useful because it reflects the responsiveness of the complete pipeline, including retrieval and answer generation, and helps compare performance before and after design changes such as LLM integration or retrieval improvements [1].

A secondary signal observed during testing is the **top similarity score (`top_score`)** of the highest-ranked retrieved chunk, which provides a rough indication of how strongly the query matched the indexed document content [1][6]. While similarity score alone is not enough to fully evaluate answer quality, it is still a useful debugging signal when checking whether a weak answer came from poor retrieval or from answer generation behavior [6][7].

Together, these metrics helped evaluate both system responsiveness and retrieval confidence, which aligns with the task requirement to demonstrate metrics awareness in the final submission [1].
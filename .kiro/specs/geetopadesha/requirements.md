# Requirements Document

## Introduction

Geetopadesha is an AI-powered spiritual guidance application that answers user queries grounded exclusively in the 700 verses of the Bhagavad Gita. The system uses a Retrieval-Augmented Generation (RAG) architecture: user queries are semantically embedded, matched against pre-indexed verse embeddings, and a constrained LLM synthesizes plain-language answers citing the relevant verses. Responses include the full Sanskrit text, transliteration, and English translation of every cited verse. The system supports English, Hindi, and Sanskrit response languages, gracefully refuses out-of-scope queries, and enforces rate limiting and prompt injection protection.

## Glossary

- **System**: The Geetopadesha application as a whole.
- **Query_Handler**: The API layer component that receives user queries and orchestrates the RAG pipeline.
- **Embedder**: The component that converts text into dense vector representations.
- **Vector_Store**: The component that persists verse embeddings and performs similarity search.
- **Retriever**: The logic that fetches the top-k semantically relevant verses from the Vector_Store.
- **Prompt_Builder**: The component that assembles the augmented LLM prompt from the query and retrieved verses.
- **Answer_Generator**: The LLM component that produces a natural language answer.
- **Response_Formatter**: The component that structures the raw LLM output into a GeetaResponse.
- **Indexer**: The offline component that embeds all 700 Gita verses and stores them in the Vector_Store.
- **QueryRequest**: The input data structure containing the user query, language preference, topK, and session ID.
- **GeetaResponse**: The output data structure containing the answer, cited verses, language, queryId, and confidence score.
- **VerseChunk**: A single Bhagavad Gita verse with its metadata (Sanskrit, transliteration, translation, commentary, similarity score).
- **CitedVerse**: A verse included in a GeetaResponse, containing verseId, Sanskrit text, transliteration, and translation.
- **Corpus**: The complete dataset of all 700 Bhagavad Gita verses with Sanskrit, transliteration, English translation, and commentary.
- **Similarity_Score**: A cosine similarity value in the range [0.0, 1.0] indicating relevance of a verse to a query.
- **Out-of-scope query**: A user query whose subject matter falls outside the teachings of the Bhagavad Gita.


## Requirements

### Requirement 1: Query Input Validation

**User Story:** As a user, I want my query to be validated before processing, so that I receive clear feedback when my input is malformed or out of bounds.

#### Acceptance Criteria

1. WHEN a QueryRequest is received with an empty or whitespace-only query, THEN THE Query_Handler SHALL reject the request with an HTTP 400 response and a descriptive validation error message.
2. WHEN a QueryRequest is received with a query exceeding 1000 characters, THEN THE Query_Handler SHALL reject the request with an HTTP 400 response and a descriptive validation error message.
3. WHEN a QueryRequest is received with a language value not in ["en", "hi", "sa"], THEN THE Query_Handler SHALL reject the request with an HTTP 400 response and a descriptive validation error message.
4. WHEN a QueryRequest is received with a topK value less than 1 or greater than 10, THEN THE Query_Handler SHALL reject the request with an HTTP 400 response and a descriptive validation error message.
5. THE Query_Handler SHALL NOT mutate the QueryRequest during validation.


### Requirement 2: Query Embedding

**User Story:** As a developer, I want user queries to be converted into vector representations, so that semantic similarity search over the verse corpus can be performed.

#### Acceptance Criteria

1. WHEN a non-empty text string is provided, THE Embedder SHALL return a fixed-dimension float vector.
2. THE Embedder SHALL return an L2-normalized vector (magnitude ≈ 1.0) suitable for cosine similarity comparison.
3. WHEN the same text is embedded multiple times, THE Embedder SHALL return the same vector (deterministic output).
4. IF the Embedder fails to produce a vector, THEN THE Query_Handler SHALL retry the embedding once before returning an HTTP 500 error response.


### Requirement 3: Offline Verse Indexing

**User Story:** As a system operator, I want all 700 Bhagavad Gita verses to be indexed into the vector store, so that semantic retrieval is available at query time.

#### Acceptance Criteria

1. WHEN the Indexer processes the Corpus, THE Indexer SHALL embed and store exactly 700 verse records in the Vector_Store.
2. WHEN a verse is indexed, THE Indexer SHALL store the verse's Sanskrit text, transliteration, English translation, commentary, chapter number, and verse number as metadata alongside the embedding.
3. WHEN the Indexer completes, THE Vector_Store SHALL contain an entry for every verse in chapters 1 through 18.
4. IF the Corpus file is missing or unparseable, THEN THE Indexer SHALL halt and report a descriptive error without partially updating the Vector_Store.


### Requirement 4: Verse Retrieval

**User Story:** As a user, I want the system to find the most relevant Bhagavad Gita verses for my question, so that the answer I receive is grounded in the most pertinent teachings.

#### Acceptance Criteria

1. WHEN a valid query vector and a topK value are provided, THE Vector_Store SHALL return at most topK VerseChunk results sorted by Similarity_Score in descending order.
2. THE Vector_Store SHALL return only VerseChunk results whose Similarity_Score is in the range [0.0, 1.0].
3. WHEN the Vector_Store contains fewer indexed verses than topK, THE Vector_Store SHALL return all available verses rather than failing.
4. WHEN all retrieved verses have a Similarity_Score below 0.3, THE Query_Handler SHALL treat the query as potentially out-of-scope and proceed to graceful refusal handling.


### Requirement 5: Prompt Construction

**User Story:** As a developer, I want the LLM prompt to be assembled from the user query and retrieved verses within the token budget, so that the LLM receives complete, well-structured context without exceeding its context window.

#### Acceptance Criteria

1. WHEN a query and a list of VerseChunks are provided, THE Prompt_Builder SHALL produce a Prompt whose fullText includes a system instruction, the verse context, and the user query.
2. THE Prompt_Builder SHALL always include the system instruction constraining the Answer_Generator to Bhagavad Gita teachings only.
3. WHILE assembling verse context, THE Prompt_Builder SHALL ensure the assembled fullText does not exceed MAX_CONTEXT_TOKENS.
4. WHEN the combined verse context would exceed MAX_VERSE_CONTEXT_TOKENS, THE Prompt_Builder SHALL include verses in descending Similarity_Score order and truncate lower-ranked verses to stay within the token budget.
5. THE Prompt_Builder SHALL include at least one VerseChunk in the prompt context when the input list is non-empty.


### Requirement 6: Answer Generation

**User Story:** As a user, I want the system to generate a natural language answer grounded in the Bhagavad Gita, so that I receive meaningful spiritual guidance relevant to my question.

#### Acceptance Criteria

1. WHEN a valid Prompt is provided, THE Answer_Generator SHALL return a non-empty natural language answer.
2. THE Answer_Generator SHALL use only the verse context provided in the Prompt to formulate the answer and SHALL NOT introduce teachings from outside the Bhagavad Gita.
3. WHEN the response language is "en", THE Answer_Generator SHALL produce an answer in simple, everyday English that avoids unexplained Sanskrit terms and abstract philosophical jargon.
4. WHEN the response language is "hi", THE Answer_Generator SHALL produce an answer in Hindi.
5. WHEN the response language is "sa", THE Answer_Generator SHALL produce an answer in Sanskrit.
6. IF the Answer_Generator service returns a 5xx error or times out, THEN THE Query_Handler SHALL retry up to 3 times with exponential backoff before returning an HTTP 503 error response.


### Requirement 7: Response Formatting

**User Story:** As a user, I want every response to include the full verse details for every cited verse, so that I can read the original Sanskrit, transliteration, and translation alongside the answer.

#### Acceptance Criteria

1. WHEN a raw answer and a list of VerseChunks are provided, THE Response_Formatter SHALL produce a GeetaResponse containing a non-empty answer and at least one CitedVerse.
2. THE Response_Formatter SHALL include the Sanskrit text (Devanagari script), Roman transliteration, and English translation for every CitedVerse in the GeetaResponse.
3. THE Response_Formatter SHALL include a unique queryId in every GeetaResponse for traceability.
4. THE Response_Formatter SHALL include a confidence score in the GeetaResponse equal to the average Similarity_Score of the cited verses.
5. IF the raw answer contains a verse reference that does not correspond to a valid Bhagavad Gita chapter and verse number, THEN THE Response_Formatter SHALL remove that reference from the citedVerses list.


### Requirement 8: Out-of-Scope Query Handling

**User Story:** As a user, I want the system to gracefully decline questions unrelated to the Bhagavad Gita, so that I understand the system's scope without receiving a confusing or misleading answer.

#### Acceptance Criteria

1. WHEN a query's retrieved verses all have a Similarity_Score below 0.3, THE Query_Handler SHALL return a GeetaResponse whose answer contains a polite, informative refusal message indicating the query is outside the scope of the Bhagavad Gita.
2. WHEN an out-of-scope refusal is returned, THE Response_Formatter SHALL include the closest matching verse found as a CitedVerse so the user has some context.
3. THE Answer_Generator SHALL include scope-refusal language in its answer when the system prompt instructs it that no sufficiently relevant verses were found.


### Requirement 9: Security and Rate Limiting

**User Story:** As a system operator, I want the API to be protected against abuse and prompt injection, so that the service remains available and the LLM cannot be manipulated into producing off-scope content.

#### Acceptance Criteria

1. THE Query_Handler SHALL sanitize every incoming query by stripping control characters and special tokens before processing.
2. THE Query_Handler SHALL enforce a rate limit per session or IP address and return an HTTP 429 response when the limit is exceeded.
3. THE System SHALL store all LLM and embedding service API keys in environment variables and SHALL NOT include them in source code or response payloads.
4. THE Prompt_Builder SHALL include a system instruction in every prompt that constrains the Answer_Generator to Bhagavad Gita teachings, reducing the prompt injection attack surface.


### Requirement 10: Health and Observability

**User Story:** As a system operator, I want a health check endpoint and unique query IDs, so that I can monitor system availability and trace individual queries through the pipeline.

#### Acceptance Criteria

1. THE Query_Handler SHALL expose a health check endpoint that returns a HealthStatus indicating whether the Vector_Store, Embedder, and Answer_Generator are reachable.
2. THE System SHALL assign a unique queryId to every processed QueryRequest and include it in the GeetaResponse.
3. WHEN an error occurs at any pipeline stage, THE Query_Handler SHALL log the queryId, the stage name, and the error detail.


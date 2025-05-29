# Documentation

Quipubase is a database that comes to bridge the gap between traditional NoSQL Document Databases and dedicated Vector Stores with real-time support for cutting-edge user experiences. I've aimed to provide a comprehensive experience towards:

*	Having a robust mechanism for metadata management such as `collections` API.
*	A simple interface for document management through `events` API with RPC style and real time state changes with subscriptions.
*	An already known way to create, store and query embeddings through the `vector` API with lightweight models for embeddings generation.
*	A simple way to extract text content in both presentation (`html`) format and llm-ready (`text`) format from most file document types (`docx`,`pptx`,`pdf`,`xlsx` and more.).
*	An storage mechanism to save objects with proper security measures.
*	Authentication mechanism via OpenID connect with `google` and `github`.

Let's explore each API one by one.
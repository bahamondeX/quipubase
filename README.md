# Quipubase: Real-time Document Database for AI-Native Applications

**Quipubase** is a cutting-edge **real-time document database** engineered specifically for the demands of **AI-native applications**. Built on the robust foundation of `RocksDB`, it offers unparalleled performance and flexibility. Quipubase empowers developers to model their data dynamically through **schema-driven collections** utilizing `jsonschema`, ensuring adaptable document structures.

At its core, Quipubase provides **native support for vector similarity search**, enabling intelligent and scalable querying capabilities essential for AI workloads. Furthermore, its integrated `pub/sub` architecture allows for **real-time subscriptions to document-level events**, making it an ideal backend for responsive, live AI systems.

---

## Features

* **Real-time Document Database:** Fast, persistent storage for dynamic data.
* **AI-Native Design:** Optimized for the unique requirements of AI applications, including vector search.
* **RocksDB Core:** Leverages the high performance and reliability of RocksDB.
* **Schema-Driven Collections:** Define flexible document structures using JSON Schema.
* **Vector Similarity Search:** Efficiently query and retrieve semantically similar content.
* **Real-time Pub/Sub:** Subscribe to document-level events for reactive application development.

---

## API Reference

Quipubase exposes a comprehensive RESTful API for managing collections, documents, vector embeddings, and real-time events.

### Collections

Manage your schema-driven document collections.

| Endpoint                  | Method | Description                                  |
| :------------------------ | :----- | :------------------------------------------- |
| `/v1/collections`         | `GET`  | List all available collections.              |
| `/v1/collections`         | `POST` | Create a new collection with a defined schema. |
| `/v1/collections/{id}`    | `GET`  | Retrieve metadata for a specific collection. |
| `/v1/collections/{id}`    | `DELETE` | Delete an entire collection and its data.    |

### Events

Interact with Quipubase's real-time pub/sub system.

| Endpoint                  | Method | Description                                      |
| :------------------------ | :----- | :----------------------------------------------- |
| `/v1/events/{collection_id}` | `POST` | Publish an event to a specific collection.        |
| `/v1/events/{collection_id}` | `GET`  | Subscribe to real-time events for a collection. (This endpoint typically supports server-sent events or websockets for continuous streaming). |

### Vector Operations

Perform vector embedding management and similarity searches.

| Endpoint              | Method   | Description                                            |
| :-------------------- | :------- | :----------------------------------------------------- |
| `/v1/vector/upsert`   | `POST`   | Upsert (update or insert) texts into the vector store. |
| `/v1/vector/query`    | `POST`   | Query the vector store for similar texts.              |
| `/v1/vector/delete`   | `DELETE` | Delete embeddings from the vector store.               |
| `/v1/vector/embed`    | `POST`   | Embed raw text content using a specified model.        |

### File Processing

Convert file content into chunked text for processing.

| Endpoint    | Method | Description                                         |
| :---------- | :----- | :-------------------------------------------------- |
| `/v1/files` | `POST` | Upload a file and receive its chunked content (HTML or text format). |

### Authentication

Handle user authentication with OAuth providers.

| Endpoint                | Method | Description                                        |
| :---------------------- | :----- | :------------------------------------------------- |
| `/v1/auth/{provider}` | `GET`  | Initiate OAuth login flow (e.g., GitHub, Google). |

---

## Data Models (Schemas)

Quipubase uses JSON Schema for defining collection structures and various other data transfer objects.

* **`CollectionMetadataType`**: Basic metadata for a collection (id, name).
* **`CollectionType`**: Full details of a collection, including its JSON Schema.
* **`JsonSchema`**: Represents a standard JSON Schema definition.
* **`JsonSchemaModel`**: A more specific JSON Schema model used for creating collections, including example properties.
* **`HTTPValidationError`**: Standard error response for validation issues.
* **`DeleteCollectionReturnType`**: Response for collection deletion operations.
* **`PubType`**: Structure for publishing events, including collection, data, and event type (create, read, update, delete, query, stop).
* **`QuipubaseRequest`**: Generic request body for event-driven operations on collections.
* **`UpsertText`**: Request body for upserting text content for vector storage.
* **`UpsertResponse`**: Response for upsert operations, detailing upserted contents.
* **`QueryText`**: Request body for querying vector store with text content and parameters.
* **`QueryMatch`**: Represents a single match from a vector similarity search.
* **`QueryResponse`**: Response for vector queries, including matched items and read count.
* **`DeleteText`**: Request body for deleting specific embeddings from the vector store.
* **`DeleteResponse`**: Response for delete operations on embeddings.
* **`EmbedText`**: Request body for generating embeddings from raw text.
* **`EmbedResponse`**: Response containing generated embeddings.
* **`Embedding`**: Detailed structure of a text embedding (id, content, vector).
* **`SemanticContent`**: Typed dictionary for semantic content.

---

## Getting Started

To get started with Quipubase, you'll typically:

1.  **Deploy Quipubase:** Set up the Quipubase server in your environment.
2.  **Create Collections:** Define your document schemas using the `/v1/collections` POST endpoint.
3.  **Ingest Data:** Add documents to your collections. For AI applications, you might also upsert texts into the vector store.
4.  **Query and Interact:** Perform document queries, vector similarity searches, and subscribe to real-time events to build reactive features.

For detailed examples and more in-depth usage, please refer to the official Quipubase documentation.

---

## Contributing

We welcome contributions to Quipubase! Please refer to our contribution guidelines for how to get involved.

---

Is there anything else you'd like to add or modify in this README, or perhaps a specific section you want to elaborate on?
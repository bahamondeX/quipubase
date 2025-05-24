import "reflect-metadata";
import { z, type ZodTypeAny } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export abstract class BaseModel<T extends { id?: string }> {
  id?: string;

  public constructor(props: T) {
    const cls = this.constructor as typeof BaseModel;
    const schema = cls.schema();
    const result = schema.parse(props);
    Object.assign(this, result);
  }

  public static schema(): ZodTypeAny {
    return z.object({
      id: z.string().optional(),
    });
  }

  public static modelJsonSchema() {
    return {
      ...zodToJsonSchema(this.schema()),
      title: this.name, // This correctly gets the class name
    };
  }

  static safeParse<T extends typeof BaseModel>(
    this: T,
    data: unknown,
  ):
    | { success: true; data: InstanceType<T> }
    | { success: false; error: z.ZodError } {
    const result = this.schema().safeParse(data);
    if (result.success) {
      const instance = new (this as any)(result.data) as InstanceType<T>;
      return { success: true, data: instance };
    }
    return result;
  }

  modelDumpJson() {
    return JSON.stringify({ ...this });
  }

  modelDump() {
    return { ...this };
  }

  static modelValidateJson<T extends typeof BaseModel>(
    this: T,
    json: string,
  ): InstanceType<T> | null {
    try {
      const data = JSON.parse(json);
      const result = this.safeParse(data);
      if (result.success) {
        return result.data;
      }
    } catch (error) {
      console.error("Failed to parse JSON:", error);
    }
    return null;
  }

  static modelValidate<T extends typeof BaseModel>(
    this: T,
    data: Record<string, unknown>,
  ): InstanceType<T> | null {
    const result = this.safeParse(data);
    if (result.success) {
      return result.data;
    }
    return null;
  }
}

export type QuipuActions =
  | "create"
  | "read"
  | "update"
  | "delete"
  | "query"
  | "stop";

export type EmbedModel = "poly-sage" | "deep-pulse" | "mini-scope";

export type EmbedText = {
  content: string[];
  model: EmbedModel;
};

export type EmbedResponse = {
  data: Embedding[];
  created: number;
  embedCount: number;
};

export type Embedding = {
  id?: string;
  content: string | string[];
  embedding: number[];
};

export type UpsertText = {
  namespace: string;
  texts: string[];
  model: EmbedModel;
};

export type UpsertResponse = {
  ids: string[];
  upsertedCount: number;
};

export type QueryText = {
  namespace: string;
  query: string;
  top_k: number;
  model: EmbedModel;
};

export type QueryResponse = {
  matches: Array<{
    id: string;
    content: string;
    score: number;
  }>;
  top_k: number;
};

export type DeleteText = {
  namespace: string;
  ids: string[];
};

export type DeleteResponse = {
  embeddings: string[];
  deletedCount: number;
};

export type JsonSchemaPrimitive = {
  title?: string;
  name?: string;
  type: "string" | "number" | "integer" | "boolean" | "binary" | "null";
  format?:
  | "date-time"
  | "base64"
  | "binary"
  | "uuid"
  | "email"
  | "hostname"
  | "ipv4"
  | "ipv6"
  | "uri"
  | "uri-reference";
  default?: any;
  description?: string;
  required?: boolean;
  readOnly?: boolean;
  writeOnly?: boolean;
  examples?: any[];
  enum?: any[];
  nullable?: boolean;
};

export type JsonSchemaObject = {
  title?: string;
  name?: string;
  type: "object";
  properties: Record<string, JsonSchema>;
  required?: string[];
  nullable?: boolean;
};

export type JsonSchemaArray = {
  title?: string;
  name?: string;
  type: "array";
  items: JsonSchema;
  anyOf?: (JsonSchemaPrimitive | JsonSchemaObject)[];
  oneOf?: (JsonSchemaPrimitive | JsonSchemaObject)[];
  allOf?: (JsonSchemaPrimitive | JsonSchemaObject)[];
  nullable?: boolean;
};

export type JsonSchema =
  | JsonSchemaPrimitive
  | JsonSchemaObject
  | JsonSchemaArray;

export type DeleteReturnType = {
  code: number;
};

export type CollectionMetadataType = {
  id: string;
  name: string;
};

export type CollectionType = {
  id: string;
  name: string;
  schema: JsonSchema;
};

export type ChunkFileResponse = {
  chunks: string[];
  created: number;
  chunkedCount: number;
};

export type UploadedFileResponse = {
  url: string;
  created: number;
  key: string;
  size: number;
  content_type: string;
};

export type GetFileResponse = {
  url: string;
  created: number;
  key: string;
};

export type DeleteFileResponse = {
  code: number; // Assuming 'code' in the Python dict[str, bool] maps to a number
  created: number; // Based on the Python return type, it was { "code": 0, "created": created }
};

// Type for a node in the recursive file tree
export type FileTreeNode = {
  type: "file" | "dir";
  name: string;
  path: string;
  content: string | FileTreeNode[]; // String content for files, list of children for directories
  created?: number; // Optional, as it's only on the root of the scan response
  error?: string; // Optional, if an error occurred during scan
};

export type ScanResponse = {
  tree: FileTreeNode[];
  created: number;
  bucket: string;
  prefix: string;
  item_count: number;
};

export type QuipubaseRequest<T> = {
  event: QuipuActions;
  id?: string | null;
  data?: T | Partial<T> | null;
};

export type SSEEvent<T> = {
  data: T | Array<T>;
  event: "create" | "read" | "update" | "delete" | "query" | "stop";
};

export type User = {
  sub: string;
  name: string;
  picture: string;
  access_token: string;
};

export class QuipuBase<T extends { id?: string }> {
  baseUrl: string;
  constructor(
    baseUrl: string = "https://quipubase-1004773754699.southamerica-west1.run.app",
  ) {
    this.baseUrl = baseUrl;
  }

  buildUrl(endpoint: string, id?: string): string {
    return `${this.baseUrl}${endpoint}${id ? `/${id}` : ""}`;
  }

  // --- Collection Management ---
  async createCollection(data: typeof BaseModel<T>): Promise<CollectionType> {
    const url = this.buildUrl("/v1/collections");

    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data.modelJsonSchema()),
    };

    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as CollectionType;
  }

  async getCollection(collectionId: string): Promise<CollectionType> {
    const url = this.buildUrl("/v1/collections", collectionId);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as CollectionType;
  }

  async deleteCollection(collectionId: string): Promise<DeleteReturnType> {
    const url = this.buildUrl("/v1/collections", collectionId);
    const options = {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    };

    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as DeleteReturnType;
  }

  async listCollections(): Promise<CollectionMetadataType[]> {
    const url = this.buildUrl("/v1/collections");
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as CollectionMetadataType[];
  }
  // --- PubSub Operations ---
  async publishEvent(
    collectionId: string,
    actionRequest: QuipubaseRequest<T>,
  ): Promise<T> {
    const url = this.buildUrl("/v1/events", collectionId);
    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(actionRequest),
    };

    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as T;
  }

  // Stream subscription with custom handling
  async subscribeToEvents(
    collectionId: string,
    callback: (chunk: SSEEvent<T>) => void,
  ): Promise<() => void> {
    const url = this.buildUrl("/v1/events", collectionId);
    const eventSource = new EventSource(url);
    eventSource.onmessage = (evt: MessageEvent) => {
      try {
        const { event, data } = JSON.parse(evt.data);

        callback({ event, data });
      } catch (error) {
        console.error(`Error parsing event:`, error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
    };

    return () => {
      eventSource.close();
    };
  }
  // --- VectorStore Methods ---

  async embed(body: EmbedText): Promise<EmbedResponse> {
    const response = await fetch(this.buildUrl("/v1/vector/embed"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as EmbedResponse;
  }

  async upsertVectors(body: UpsertText): Promise<UpsertResponse> {
    const response = await fetch(this.buildUrl("/v1/vector/upsert"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as UpsertResponse;
  }

  async queryVectors(body: QueryText): Promise<QueryResponse> {
    const response = await fetch(this.buildUrl("/v1/vector/query"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as QueryResponse;
  }

  async deleteVectors(body: DeleteText): Promise<DeleteResponse> {
    const response = await fetch(this.buildUrl("/v1/vector/delete"), {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as DeleteResponse;
  }

  // --- File Operations ---

  async chunkFile(
    file: File,
    format: "html" | "text",
  ): Promise<ChunkFileResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(this.buildUrl(`/v1/files?format=${format}`), {
      method: "POST", // FastAPI endpoint is POST for chunkFile
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as ChunkFileResponse;
  }

  async uploadFile(
    file: File,
    bucket?: string,
  ): Promise<UploadedFileResponse> {
    const formData = new FormData();
    formData.append("file", file);
    let url = this.buildUrl("/v1/files");
    if (bucket) {
      url += `?bucket=${bucket}`;
    }
    const response = await fetch(url, {
      method: "PUT", // FastAPI endpoint is PUT for file upload
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as UploadedFileResponse;
  }

  async getFile(key: string, bucket?: string): Promise<GetFileResponse> {
    let url = this.buildUrl("/v1/files", key);
    if (bucket) {
      url += `?bucket=${bucket}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as GetFileResponse;
  }

  async deleteFile(key: string): Promise<DeleteFileResponse> {
    const url = this.buildUrl("/v1/files", key);
    const options = {
      method: "DELETE",
    };
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as DeleteFileResponse;
  }

  async subscribeToScan(
    callback: (data: FileTreeNode) => void,
    prefix: string = "",
    bucket?: string,
    onComplete?: () => void,
    onError?: (error: Event) => void,
  ): Promise<() => void> {
    let url = this.buildUrl("/v1/files/tree/default"); // Path from FastAPI: /v1/files/tree/{default}
    const params = new URLSearchParams();
    if (prefix) {
      params.append("prefix", prefix);
    }
    if (bucket) {
      params.append("bucket", bucket);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const eventSource = new EventSource(url);

    eventSource.onmessage = (evt: MessageEvent) => {
      try {
        // Each `onmessage` event carries one chunk (one node) from the generator
        const node: FileTreeNode = JSON.parse(evt.data);
        callback(node);
      } catch (error) {
        console.error(`Error parsing SSE chunk:`, error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
      if (onError) {
        onError(error);
      }
      eventSource.close(); // Close on error to prevent constant retries if unrecoverable
    };

    // EventSource doesn't have a direct 'oncomplete' event for the stream ending,
    // but onclose can be used if you anticipate the server closing the connection
    // cleanly when done. In practice, you might rely on the server side closing.
    eventSource.onopen = () => {
      console.log("SSE connection opened for scan.");
    };

    eventSource.onerror = () => {
      console.log("SSE connection closed for scan.");
      if (onComplete) {
        onComplete();
      }
    };


    return () => {
      eventSource.close();
    };
  }

  login(
    provider: "google" | "github",
    redirectUrl: string = window.location.origin,
  ) {
    if (!["github", "google"].includes(provider)) {
      console.error("Invalid OAuth provider:", provider);
      return;
    }

    // Store redirectUrl in localStorage (as FastAPI reads from cookie in Python side,
    // or you adjust FastAPI to read from query param).
    // The previous Python code indicated reading from cookie, but the JS sent it via query param.
    // Let's ensure consistency: send via query param for simplicity.
    // Also, localStorage.setItem(key, value) takes two arguments.
    localStorage.setItem('auth_redirect_url', redirectUrl); // Use a specific key

    const authUrl = `${this.baseUrl}/v1/auth/${provider}?redirect_url=${encodeURIComponent(redirectUrl)}`;
    window.location.href = authUrl;


    const params = new URLSearchParams(window.location.search);
    const name = params.get('name');
    const sub = params.get('sub');
    const picture = params.get('picture');
    const accessToken = params.get('access_token');

    if (window.history.pushState) {
      const newUrl = new URL(window.location.href);
      newUrl.search = ''; // Clear all query parameters
      window.history.pushState({ path: newUrl.href }, '', newUrl.href);
    }

    localStorage.removeItem('auth_redirect_url'); // Remove the specific key

    if (name && sub && accessToken) {
      return {
        name,
        sub,
        picture: picture ?? "",
        access_token: accessToken,
      };
    } else {
      console.warn("No valid authentication parameters found in URL.");
      return null;
    }
  }

  // A separate function to handle the redirect callback on the destination page
  static handleAuthRedirectCallback(): User | null {
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name');
    const sub = params.get('sub');
    const picture = params.get('picture');
    const accessToken = params.get('access_token');

    // Clean up the URL
    if (window.history.pushState) {
      const newUrl = new URL(window.location.href);
      newUrl.search = ''; // Clear all query parameters
      window.history.pushState({ path: newUrl.href }, '', newUrl.href);
    }

    // Clean up local storage if a redirect URL was stored
    // localStorage.removeItem('auth_redirect_url'); // Uncomment if you use this to retrieve the original redirect url on the client

    if (name && sub && accessToken) {
      return {
        name,
        sub,
        picture: picture ?? "",
        access_token: accessToken,
      };
    } else {
      console.warn("No valid authentication parameters found in URL after redirect.");
      return null;
    }
  }
}
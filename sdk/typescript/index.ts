import "reflect-metadata";
import { z, ZodType } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export abstract class BaseModel {
	static schema(): ZodType<any> {
		throw new Error("Must implement schema()");
	}

	static jsonSchema() {
		return zodToJsonSchema((this as any).schema());
	}
	static safeParse<T extends typeof BaseModel>(
		this: T,
		data: unknown
	): { success: true; data: InstanceType<T> } | { success: false; error: z.ZodError } {
		const result = this.schema().safeParse(data);
		if (result.success) {
			// @ts-ignore
			const instance = new this() as InstanceType<T>;
			Object.assign(instance, result.data);
			return { success: true, data: instance };
		} else {
			return result;
		}
	}

	toJSON() {
		return JSON.stringify({ ...this });
	}
}

export type QuipuActions = "create" | "read" | "update" | "delete" | "query" | "stop";

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
	title?: string
	name?: string
    type: "string" | "number" | "integer" | "boolean" | "binary" | "null"
    format?: "date-time" | "base64" | "binary" | "uuid" | "email" | "hostname" | "ipv4" | "ipv6" | "uri" | "uri-reference"
	default?: any
    description?: string
    required?: boolean
    readOnly?: boolean
    writeOnly?: boolean
	examples?: any[]
	enum?: any[]
    nullable?: boolean    
}

export type JsonSchemaObject = {
	title?: string
	name?: string
    type: "object"
	properties: Record<string, JsonSchema>
    required?: string[]
    nullable?: boolean
}

export type JsonSchemaArray = {
	title?: string
	name?: string
    type: "array"
	items: JsonSchema
	anyOf?: (JsonSchemaPrimitive | JsonSchemaObject)[]
	oneOf?: (JsonSchemaPrimitive | JsonSchemaObject)[]
	allOf?: (JsonSchemaPrimitive | JsonSchemaObject)[]
    nullable?: boolean
}

export type JsonSchema = JsonSchemaPrimitive | JsonSchemaObject | JsonSchemaArray


export type DeleteReturnType = {
	code:number 
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

export type QuipubaseRequest<T> = {
	event: QuipuActions;
	id?: string | null;
	data?: T | Partial<T> | null;
};


export type SSEEvent<T extends BaseModel> = {
	data: T;
	event: "create" | "read" | "update" | "delete" | "query" | "stop";
};


export class QuipuBase<T extends BaseModel> {
	constructor(
		public baseUrl: string = "http://localhost:5454",
	) { }

	buildUrl(endpoint: string, id?: string): string {
		return `${this.baseUrl}${endpoint}${id ? `/${id}` : ""}`;
	}

	// Collection Management
	async createCollection(data: T): Promise<CollectionType> {
		const url = this.buildUrl("/v1/collections");
		const collectionData = {
			// @ts-ignore
			schema: data.schema()
		};

		const options = {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(collectionData),
		};

		const response = await fetch(url, options);
		return await response.json() as CollectionType;
	}

	async getCollection(collectionId: string): Promise<CollectionType> {
		const url = this.buildUrl("/v1/collections", collectionId);
		const response = await fetch(url);
		return await response.json() as CollectionType;
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
		return await response.json() as DeleteReturnType;
	}

	async listCollections(limit: number = 100, offset: number = 0): Promise<CollectionMetadataType[]> {
		const params = new URLSearchParams();
		params.set("limit", limit.toString());
		params.set("offset", offset.toString());

		const url = `${this.buildUrl("/v1/collections")}?${params.toString()}`;
		const response = await fetch(url);
		return await response.json() as CollectionMetadataType[];
	}
	// PubSub Operations
	async publishEvent(collectionId: string, actionRequest: QuipubaseRequest<T>): Promise<T> {
		const url = this.buildUrl("/v1/events", collectionId);
		const options = {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(actionRequest),
		};

		const response = await fetch(url, options);
		return await response.json() as T
	}

	// Stream subscription with custom handling

	async subscribeToEvents(collectionId: string, callback: (chunk: SSEEvent<T>) => void): Promise<() => void> {
		const url = this.buildUrl("/v1/events", collectionId);
		const eventSource = new EventSource(url);

		const eventTypes: QuipuActions[] = ["create", "read", "update", "delete", "query", "stop"];

		eventTypes.forEach(eventType => {
			eventSource.addEventListener(eventType, (event: MessageEvent) => {
				try {
					const parsedData = JSON.parse(event.data) as SSEEvent<T>
					callback({
						data: parsedData.data,
						event: eventType
					});

					// If stop event is received, close the connection
					if (eventType === 'stop') {
						eventSource.close();
					}
				} catch (error) {
					console.error(`Error parsing ${eventType} event:`, error);
				}
			});
		});

		eventSource.onerror = (error) => {
			console.error("EventSource error:", error);
			eventSource.close();
		};

		// Return a function to close the connection
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
		return await response.json() as EmbedResponse
	}

	async upsertVectors(body: UpsertText): Promise<UpsertResponse> {
		const response = await fetch(this.buildUrl("/v1/vector/upsert"), {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body),
		});
		return await response.json() as UpsertResponse
	}

	async queryVectors(body: QueryText): Promise<QueryResponse> {
		const response = await fetch(this.buildUrl("/v1/vector/query"), {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body),
		});
		return await response.json() as QueryResponse
	}

	async deleteVectors(body: DeleteText): Promise<DeleteResponse> {
		const response = await fetch(this.buildUrl("/v1/vector/delete"), {
			method: "DELETE",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body),
		});
		return await response.json() as DeleteResponse
	}
}

class Message extends BaseModel {
	id?: string
	role: "assistant" | "user" | "system"
	content: string
	createdAt: string

	constructor(role: "assistant" | "user" | "system", content: string) {
		super()
		this.role = role
		this.content = content
		this.createdAt = new Date().toISOString()
	}

	static schema() {
		return z.object({
			id: z.string().optional(),
			role: z.enum(["assistant", "user", "system"]),
			content: z.string(),
			createdAt: z.string(),
		})
	}
}

class Thread extends BaseModel {
	id?: string
	title: string
	createdAt: string
	updatedAt?: string
	messages: Message[]

	constructor(title: string, messages: Message[]) {
		super()
		this.title = title
		this.createdAt = new Date().toISOString()
		this.messages = messages
	}

	static schema() {
		return z.object({
			id: z.string().optional(),
			title: z.string(),
			createdAt: z.string(),
			updatedAt: z.string().optional(),
			messages: z.array(Message.schema()),
		})
	}
}

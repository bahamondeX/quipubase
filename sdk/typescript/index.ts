import "reflect-metadata";
import { z, type ZodTypeAny } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

export abstract class BaseModel {
	id!: string
	public constructor(data?: Partial<z.infer<ReturnType<typeof BaseModel.schema>>>) {
		const cls = this.constructor as typeof BaseModel;
		const schema = cls.schema();
		const result = schema.parse(data ?? {});
		Object.assign(this, result);
	}

	public static schema(): ZodTypeAny {
		throw new Error("Must implement schema()");
	}

	public static jsonSchema() {
		// 'this' here refers to the class constructor (e.g., 'User' or 'Product')
		// So, 'this.name' will be "User" or "Product"
		return {
			...zodToJsonSchema(this.schema()),
			title: this.name // This correctly gets the class name
		};
	}

	static safeParse<T extends typeof BaseModel>(
		this: T,
		data: unknown
	): { success: true; data: InstanceType<T> } | { success: false; error: z.ZodError } {
		const result = this.schema().safeParse(data);
		if (result.success) {
			const instance = new (this as any)(result.data) as InstanceType<T>;
			return { success: true, data: instance };
		}
		return result;
	}

	toJSON() {
		return JSON.stringify({ ...this });
	}

	toDict() {
		return { ...this }
	}


	static from<T extends BaseModel>(this: new () => T, data: Partial<T>): T {
		const instance = new this()
		Object.assign(instance, data)
		return instance
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
	code: number
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
}

export type QuipubaseRequest<T> = {
	event: QuipuActions;
	id?: string | null;
	data?: T | Partial<T> | null;
};


export type SSEEvent<T extends BaseModel> = {
	data: T | Array<T>;
	event: "create" | "read" | "update" | "delete" | "query" | "stop";
};


export class QuipuBase<T extends BaseModel> {
	baseUrl: string
	constructor(
		baseUrl: string = "http://localhost:5454",
	) {
		this.baseUrl = baseUrl

	}

	buildUrl(endpoint: string, id?: string): string {
		return `${this.baseUrl}${endpoint}${id ? `/${id}` : ""}`;
	}

	// Collection Management
	async createCollection(data: typeof BaseModel): Promise<CollectionType> {
		const url = this.buildUrl("/v1/collections");


		const options = {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(data.jsonSchema()
			),
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

	async listCollections(): Promise<CollectionMetadataType[]> {

		const url = this.buildUrl("/v1/collections");
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

	async subscribeToEvents(
		collectionId: string,
		callback: (chunk: SSEEvent<T>) => void
	): Promise<() => void> {
		const url = this.buildUrl("/v1/events", collectionId);
		const eventSource = new EventSource(url);
		eventSource.onmessage = (evt: MessageEvent) => {
			try {
				const { event, data } = JSON.parse(evt.data)

				callback({ event, data });
			} catch (error) {
				console.error(`Error parsing event:`, error);
			}
		};

		eventSource.onerror = (error) => {
			console.error("EventSource error:", error);
			eventSource.close();
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

	async chunkFile(file: File, format: "html" | "text"): Promise<ChunkFileResponse> {
		const formData = new FormData()
		formData.append("file", file)
		const response = await fetch(this.buildUrl(`/v1/file?format=${format}`))
		return await response.json() as ChunkFileResponse
	}

}

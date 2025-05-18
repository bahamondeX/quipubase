import { InstanceOf } from 'prop-types'; // Note: You might need a different library for this

// Type aliases
type QuipuActions = "create" | "read" | "update" | "delete" | "query" | "stop";
type JsonSchemaType = "object" | "array" | "string" | "number" | "integer" | "boolean" | "null";

// Pydantic BaseModel equivalent in TypeScript (approximation)
interface BaseModel {
	[key: string]: any; // Allow arbitrary properties
}

// First define the JsonSchema as a regular interface
interface JsonSchemaModel {
	title: string;
	description?: string | null;
	type?: JsonSchemaType;
	properties: { [key: string]: any };  //  Equivalent of Dict[str, Any]
	required?: string[] | null;
	enum?: any[] | null;
	items?: any | null;
}


// Keep TypedDict version if needed elsewhere.  Note the question marks for optional.
interface JsonSchema {
	title: string;
	description?: string;
	type: JsonSchemaType;
	properties: { [key: string]: any };
	enum?: any[];
	items?: any;
}

interface CollectionType {
	id: string;
	name: string;
	schema: JsonSchema;
}

interface CollectionMetadataType {
	id: string;
	name: string;
}

interface DeleteCollectionReturnType {
	code: number;
}

interface PubReturnType {
	collection: string;
	data: BaseModel; //  Could be improved if you have a base class for Pydantic models
	event: QuipuActions;
}

interface QuipubaseRequest {
	event?: QuipuActions;
	id?: string;  //  UUID equivalent in TS is string
	data?: { [key: string]: any };
}

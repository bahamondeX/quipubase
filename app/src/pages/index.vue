<script setup lang="ts">
import { ref, onMounted, reactive, watch } from 'vue';

// Type definitions
interface JsonSchema {
  title: string;
  description?: string;
  type?: "object" | "array" | "string" | "number" | "integer" | "boolean" | "null";
  properties?: Record<string, any>;
  required?: string[];
  enum?: any[];
  items?: any;
}

interface ActionRequest {
  event: "create" | "read" | "update" | "delete" | "query" | "stop";
  id?: string | null;
  data?: object | null;
}

interface CollectionType {
  id: string;
  definition: JsonSchema;
}

interface Status {
  code: number;
  message: string;
  id?: string;
  definition?: JsonSchema;
}

// QuipuBase client class
class QuipuBase<T> {
  constructor(public collectionId: string) {}

  async createCollection(schema: JsonSchema): Promise<CollectionType> {
    const url = `${BASE_URL}/v1/collections`;
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(schema),
    };

    const response = await fetch(url, options);
    return await response.json() as CollectionType;
  }

  async getCollection(): Promise<CollectionType> {
    const url = `${BASE_URL}/v1/collections/${this.collectionId}`;
    const response = await fetch(url);
    return await response.json() as CollectionType;
  }

  async deleteCollection(): Promise<Record<string, boolean>> {
    const url = `${BASE_URL}/v1/collections/${this.collectionId}`;
    const options = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const response = await fetch(url, options);
    return await response.json() as Record<string, boolean>;
  }

  async listCollections(limit: number = 100, offset: number = 0): Promise<string[]> {
    const params = new URLSearchParams();
    params.set("limit", limit.toString());
    params.set("offset", offset.toString());

    const url = `${BASE_URL}/v1/collections?${params.toString()}`;
    const response = await fetch(url);
    return await response.json() as string[];
  }

  async create(data: T): Promise<T> {
    const actionRequest: ActionRequest = {
      event: "create",
      data: data || null,
    };

    return await this.fetch(actionRequest) as T;
  }

  async read(id: string): Promise<T> {
    const actionRequest: ActionRequest = {
      event: "read",
      id,
    };

    return await this.fetch(actionRequest) as T;
  }

  async update(id: string, data: Partial<T>): Promise<T> {
    const actionRequest: ActionRequest = {
      event: "update",
      id,
      data,
    };

    return await this.fetch(actionRequest) as T;
  }

  async delete(id: string): Promise<Status> {
    const actionRequest: ActionRequest = {
      event: "delete",
      id,
    };

    return await this.fetch(actionRequest) as Status;
  }

  async query(data: Partial<T>): Promise<T[]> {
    const actionRequest: ActionRequest = {
      event: "query",
      data,
    };

    return await this.fetch(actionRequest) as T[];
  }

  async publishEvent(actionRequest: ActionRequest): Promise<object> {
    const url = `${BASE_URL}/v1/pubsub/events/${this.collectionId}`;
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(actionRequest),
    };

    const response = await fetch(url, options);
    return await response.json();
  }

  async subscribeToEvents(callback: (event: any) => void): Promise<() => void> {
    const url = `${BASE_URL}/v1/pubsub/events/${this.collectionId}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      callback(JSON.parse(event.data));
    };

    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
      eventSource.close();
    };
    
    // Return a function to close the connection
    return () => {
      eventSource.close();
    };
  }

  async subscribeWithCustomHandler(callback: (data: string) => any): Promise<void> {
    const url = `${BASE_URL}/v1/pubsub/events/${this.collectionId}`;

    // Using fetch with a reader for more control
    const response = await fetch(url);
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      callback(chunk);
    }
  }

  private async fetch(actionRequest: ActionRequest): Promise<Status | T | T[] | CollectionType> {
    const url = `${BASE_URL}/v1/collections/${this.collectionId}`;
    const options = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(actionRequest),
    };

    const response = await fetch(url, options);
    return await response.json();
  }
}

// State management
const collections = ref<string[]>([]);
const currentCollection = ref<string>('');
const collectionSchema = ref<JsonSchema | null>(null);
const documents = ref<any[]>([]);
const loading = ref<boolean>(false);
const notification = reactive({
  show: false,
  message: '',
  type: 'success'
});

// Form data
const newCollectionForm = reactive({
  id: '',
  schema: {
    title: '',
    type: 'object',
    properties: {},
    required: []
  } as JsonSchema
});

const newDocumentForm = reactive({
  data: {} as any
});

const newSchemaProperty = reactive({
  name: '',
  type: 'string',
  required: false
});

// UI state
const isMenuOpen = ref(false);
const activeTab = ref('installation');
const activeSection = ref('hero');

// Base URL for API
const BASE_URL = "https://db.oscarbahamonde.cloud";

// Initialize QuipuBase client
const quipuClient = ref<QuipuBase<any> | null>(null);

// Scroll handling for animations
const handleScroll = () => {
  const sections = ['hero', 'features', 'explorer', 'docs'];
  for (const section of sections) {
    const element = document.getElementById(section);
    if (element) {
      const rect = element.getBoundingClientRect();
      if (rect.top <= 100 && rect.bottom >= 100) {
        activeSection.value = section;
        break;
      }
    }
  }
};

onMounted(async () => {
  // Load collections on initial render
  await fetchCollections();
  
  // Set up scroll handler for animations
  window.addEventListener('scroll', handleScroll);
  
  // Check for hash in URL for direct navigation
  if (window.location.hash) {
    const targetId = window.location.hash.substring(1);
    scrollToSection(targetId);
  }
});

// Collection management
async function fetchCollections() {
  try {
    loading.value = true;
    
    // Create a temporary client without a collection ID for listing collections
    const tempClient = new QuipuBase<any>('');
    collections.value = await tempClient.listCollections();
  } catch (error) {
    showNotification(`Error fetching collections: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function createCollection() {
  if (!newCollectionForm.id || !newCollectionForm.schema.title) {
    showNotification('Collection ID and schema title are required', 'error');
    return;
  }
  
  try {
    loading.value = true;
    
    // Create client with the new collection ID
    const client = new QuipuBase<any>(newCollectionForm.id);
    
    // Create the collection with the schema
    const result = await client.createCollection(newCollectionForm.schema);
    
    // Add to collections list if not already present
    if (!collections.value.includes(result.id)) {
      collections.value.push(result.id);
    }
    
    showNotification(`Collection ${result.id} created successfully!`, 'success');
    
    // Reset form
    newCollectionForm.id = '';
    newCollectionForm.schema = {
      title: '',
      type: 'object',
      properties: {},
      required: []
    };
    
    // Select the newly created collection
    selectCollection(result.id);
  } catch (error) {
    showNotification(`Error creating collection: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function selectCollection(id: string) {
  try {
    loading.value = true;
    currentCollection.value = id;
    
    // Initialize QuipuBase client with selected collection
    quipuClient.value = new QuipuBase<any>(id);
    
    // Fetch collection schema
    const collection = await quipuClient.value.getCollection();
    collectionSchema.value = collection.definition;
    
    // Fetch documents in collection
    const data = await quipuClient.value.query({});
    documents.value = data;
    
    // Initialize new document form based on schema
    newDocumentForm.data = generateEmptyDocument(collection.definition);
  } catch (error) {
    showNotification(`Error selecting collection: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function deleteCollection() {
  if (!currentCollection.value) return;
  
  if (!confirm(`Are you sure you want to delete collection "${currentCollection.value}"?`)) {
    return;
  }
  
  try {
    loading.value = true;
    await quipuClient.value?.deleteCollection();
    
    // Remove from list and reset state
    collections.value = collections.value.filter(c => c !== currentCollection.value);
    currentCollection.value = '';
    collectionSchema.value = null;
    documents.value = [];
    
    showNotification('Collection deleted successfully!', 'success');
  } catch (error) {
    showNotification(`Error deleting collection: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

// Document operations
async function createDocument() {
  if (!quipuClient.value) return;
  
  try {
    loading.value = true;
    
    // Handle case where user enters JSON as string
    let docData = newDocumentForm.data;
    if (typeof docData === 'string') {
      try {
        docData = JSON.parse(docData);
      } catch (e) {
        throw new Error('Invalid JSON format');
      }
    }
    
    const result = await quipuClient.value.create(docData);
    documents.value.push(result);
    
    // Reset form
    newDocumentForm.data = generateEmptyDocument(collectionSchema.value);
    
    showNotification('Document created successfully!', 'success');
  } catch (error) {
    showNotification(`Error creating document: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function updateDocument(id: string, data: any) {
  if (!quipuClient.value) return;
  
  try {
    loading.value = true;
    const result = await quipuClient.value.update(id, data);
    
    // Update document in list
    const index = documents.value.findIndex(doc => doc.id === id);
    if (index !== -1) {
      documents.value[index] = result;
    }
    
    showNotification('Document updated successfully!', 'success');
  } catch (error) {
    showNotification(`Error updating document: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

async function deleteDocument(id: string) {
  if (!quipuClient.value) return;
  
  if (!confirm('Are you sure you want to delete this document?')) {
    return;
  }
  
  try {
    loading.value = true;
    await quipuClient.value.delete(id);
    
    // Remove from list
    documents.value = documents.value.filter(doc => doc.id !== id);
    
    showNotification('Document deleted successfully!', 'success');
  } catch (error) {
    showNotification(`Error deleting document: ${error}`, 'error');
  } finally {
    loading.value = false;
  }
}

// Schema management
function addPropertyToSchema() {
  if (!newSchemaProperty.name) {
    showNotification('Property name is required', 'error');
    return;
  }
  
  // Add property to schema
  newCollectionForm.schema.properties![newSchemaProperty.name] = {
    type: newSchemaProperty.type
  };
  
  // Add to required fields if marked as required
  if (newSchemaProperty.required) {
    if (!newCollectionForm.schema.required) {
      newCollectionForm.schema.required = [];
    }
    newCollectionForm.schema.required.push(newSchemaProperty.name);
  }
  
  // Reset form
  newSchemaProperty.name = '';
  newSchemaProperty.type = 'string';
  newSchemaProperty.required = false;
}

// Utility functions
function generateEmptyDocument(schema: JsonSchema | null): any {
  if (!schema || !schema.properties) return {};
  
  const result: any = {};
  
  for (const [key, prop] of Object.entries(schema.properties)) {
    if (typeof prop === 'object' && prop !== null) {
      // Handle different types
      switch (prop.type) {
        case 'string':
          result[key] = '';
          break;
        case 'number':
        case 'integer':
          result[key] = 0;
          break;
        case 'boolean':
          result[key] = false;
          break;
        case 'array':
          result[key] = [];
          break;
        case 'object':
          result[key] = generateEmptyDocument(prop as JsonSchema);
          break;
        default:
          result[key] = null;
      }
    }
  }
  
  return result;
}

function showNotification(message: string, type: 'success' | 'error' = 'success') {
  notification.message = message;
  notification.type = type;
  notification.show = true;
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    notification.show = false;
  }, 5000);
}

// Helper to display JSON prettily
function prettyJson(obj: any): string {
  return JSON.stringify(obj, null, 2);
}

// Smooth scroll to section
function scrollToSection(sectionId: string) {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
    isMenuOpen.value = false; // Close mobile menu after clicking
    
    // Update URL hash without triggering a jump
    history.pushState(null, '', `#${sectionId}`);
  }
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}

function setActiveTab(tab: string) {
  activeTab.value = tab;
}
</script>
<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-slate-200 antialiased">
    <!-- Toast Notification -->
    <div v-if="notification.show" 
         :class="[
           'fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-md transition-all duration-300 transform translate-y-0 opacity-100',
           notification.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
         ]">
      <div class="flex items-center">
        <svg v-if="notification.type === 'success'" class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        <svg v-else class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        <span>{{ notification.message }}</span>
      </div>
      <button @click="notification.show = false" class="absolute top-2 right-2 text-white">
        &times;
      </button>
    </div>

    <!-- Header -->
    <header class="fixed top-0 left-0 right-0 z-40 bg-slate-900 bg-opacity-90 backdrop-blur-md border-b border-slate-700">
      <div class="container mx-auto px-4 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <img src="./assets/quipubase-logo.png" alt="QuipuBase Logo" class="w-10 h-10 rounded-md mr-3 shadow-[0_0_15px_rgba(212,175,55,0.5)]" />
            <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">QuipuBase</span>
          </div>
          
          <nav class="hidden md:flex items-center space-x-8">
            <a @click.prevent="scrollToSection('hero')" :class="['cursor-pointer hover:text-amber-400 transition-colors', activeSection === 'hero' ? 'text-amber-400' : '']">
              Home
            </a>
            <a @click.prevent="scrollToSection('features')" :class="['cursor-pointer hover:text-amber-400 transition-colors', activeSection === 'features' ? 'text-amber-400' : '']">
              Features
            </a>
            <a @click.prevent="scrollToSection('explorer')" :class="['cursor-pointer hover:text-amber-400 transition-colors', activeSection === 'explorer' ? 'text-amber-400' : '']">
              Explorer
            </a>
            <a @click.prevent="scrollToSection('docs')" :class="['cursor-pointer hover:text-amber-400 transition-colors', activeSection === 'docs' ? 'text-amber-400' : '']">
              Documentation
            </a>
            <a href="https://github.com/yourusername/quipubase" target="_blank" class="px-4 py-2 rounded-md border border-amber-500 text-amber-500 hover:bg-amber-500 hover:text-slate-900 transition-colors">
              GitHub
            </a>
          </nav>
          
          <button @click="toggleMenu" class="md:hidden flex items-center">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!isMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Mobile Menu -->
      <div v-if="isMenuOpen" class="md:hidden bg-slate-800 border-b border-slate-700">
        <div class="container mx-auto px-4 py-2">
          <div class="flex flex-col space-y-3">
            <a @click.prevent="scrollToSection('hero')" class="py-2 hover:text-amber-400 transition-colors cursor-pointer">
              Home
            </a>
            <a @click.prevent="scrollToSection('features')" class="py-2 hover:text-amber-400 transition-colors cursor-pointer">
              Features
            </a>
            <a @click.prevent="scrollToSection('explorer')" class="py-2 hover:text-amber-400 transition-colors cursor-pointer">
              Explorer
            </a>
            <a @click.prevent="scrollToSection('docs')" class="py-2 hover:text-amber-400 transition-colors cursor-pointer">
              Documentation
            </a>
            <a href="https://github.com/yourusername/quipubase" target="_blank" class="py-2 text-amber-500 transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section id="hero" class="relative pt-32 pb-20 overflow-hidden">
      <!-- Decorative pattern -->
      <div class="absolute top-0 left-0 right-0 h-20 bg-amber-500 opacity-5 pattern-zigzag"></div>
      <div class="absolute bottom-0 left-0 right-0 h-20 bg-amber-500 opacity-5 pattern-zigzag"></div>
      
      <div class="container mx-auto px-4">
        <div class="flex flex-col md:flex-row items-center gap-8 md:gap-16">
          <div class="w-full md:w-1/2 space-y-6">
            <h1 class="text-3xl md:text-5xl font-bold leading-tight">
              <span class="block bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600 animate-pulse">Real-time Document Database</span>
              <span class="mt-2 block">for AI-native Applications</span>
            </h1>
            <p class="text-slate-400 text-lg">
              Built on top of RocksDB, QuipuBase enables dynamic, schema-driven collections
              using jsonschema for flexible document modeling with native support for vector similarity search.
            </p>
            <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 pt-4">
              <button @click="scrollToSection('explorer')" class="px-6 py-3 rounded-md bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-semibold shadow-md hover:shadow-amber-500/20 hover:shadow-lg transition-all duration-300 group">
                <span class="flex items-center justify-center">
                  <span>Try Explorer</span>
                  <svg class="w-5 h-5 ml-2 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                  </svg>
                </span>
              </button>
              <button @click="scrollToSection('docs')" class="px-6 py-3 rounded-md bg-slate-800 text-amber-400 border border-amber-500/30 hover:border-amber-500 transition-colors duration-300">
                Documentation
              </button>
            </div>
          </div>
          
          <div class="w-full md:w-1/2 flex justify-center">
            <div class="relative">
              <div class="absolute inset-0 bg-amber-500/20 blur-3xl rounded-full"></div>
              <img src="./assets/quipubase-logo.png" alt="QuipuBase Logo" class="relative w-64 h-64 object-contain rounded-2xl shadow-[0_0_30px_rgba(212,175,55,0.3)]" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="relative py-20 bg-slate-800/50">
      <!-- Decorative pattern -->
      <div class="absolute top-0 left-0 right-0 h-20 bg-amber-500 opacity-5 pattern-zigzag transform rotate-180"></div>
      
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold mb-4">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">Key Features</span>
          </h2>
          <p class="text-slate-400 max-w-3xl mx-auto">Powerful capabilities designed for modern AI applications</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Feature 1 -->
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-amber-500/50 transition-colors duration-300 group">
            <div class="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
              <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-2 group-hover:text-amber-400 transition-colors">Dynamic Schema</h3>
            <p class="text-slate-400">Create and evolve document schemas on the fly with JSON Schema validation.</p>
          </div>
          
          <!-- Feature 2 -->
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-amber-500/50 transition-colors duration-300 group">
            <div class="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
              <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-2 group-hover:text-amber-400 transition-colors">Vector Search</h3>
            <p class="text-slate-400">Native support for vector similarity search to power AI applications.</p>
          </div>
          
          <!-- Feature 3 -->
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-amber-500/50 transition-colors duration-300 group">
            <div class="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
              <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-2 group-hover:text-amber-400 transition-colors">Real-time Events</h3>
            <p class="text-slate-400">Subscribe to document-level events with built-in pub/sub architecture.</p>
          </div>
          
          <!-- Feature 4 -->
          <div class="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-amber-500/50 transition-colors duration-300 group">
            <div class="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
              <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-2 group-hover:text-amber-400 transition-colors">High Performance</h3>
            <p class="text-slate-400">Built on RocksDB for speed and reliability at scale.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Explorer Section -->
    <section id="explorer" class="py-20">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold mb-4">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">Database Explorer</span>
          </h2>
          <p class="text-slate-400 max-w-3xl mx-auto">Interact with your QuipuBase collections</p>
        </div>
        
        <div class="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
          <div class="grid grid-cols-1 lg:grid-cols-4">
            <!-- Sidebar -->
            <div class="lg:col-span-1 border-r border-slate-700 bg-slate-900">
              <div class="p-4 border-b border-slate-700 flex items-center justify-between">
                <h3 class="font-semibold">Collections</h3>
                <button @click="fetchCollections" class="p-1 rounded-md hover:bg-slate-800 transition-colors" title="Refresh">
                  <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                  </svg>
                </button>
              </div>
              
              <div v-if="loading" class="p-4 flex items-center justify-center">
                <div class="animate-spin rounded-full h-5 w-5 border-t-2 border-amber-500"></div>
                <span class="ml-2 text-slate-400">Loading...</span>
              </div>
              
              <div v-else-if="collections.length === 0" class="p-4 text-center text-slate-400">
                No collections found
              </div>
              
              <ul v-else class="divide-y divide-slate-700 max-h-64 overflow-y-auto">
                <li 
                  v-for="collection in collections" 
                  :key="collection"
                  @click="selectCollection(collection)"
                  :class="['px-4 py-3 cursor-pointer hover:bg-slate-800/70 transition-colors', 
                          currentCollection === collection ? 'bg-slate-800 text-amber-400' : '']"
                >
                  {{ collection }}
                </li>
              </ul>
              
              <div class="p-4 border-t border-slate-700">
                <h4 class="font-semibold mb-4 text-amber-400">Create Collection</h4>
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm mb-1">Collection ID</label>
                    <input 
                      v-model="newCollectionForm.id" 
                      type="text" 
                      placeholder="my-collection"
                      class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
                    />
                  </div>
                  
                  <div>
                    <label class="block text-sm mb-1">Schema Title</label>
                    <input 
                      v-model="newCollectionForm.schema.title" 
                      type="text" 
                      placeholder="My Collection"
                      class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
                    />
                  </div>
                  
                  <div class="pt-2">
                    <h5 class="text-sm font-medium mb-2">Properties</h5>
                    <div class="space-y-2">
                      <div class="grid grid-cols-2 gap-2">
                        <input
                          v-model="newSchemaProperty.name"
                          type="text"
                          placeholder="Property name"
                          class="px-3 py-2 bg-slate-900 border border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
                        />
                        <select 
                          v-model="newSchemaProperty.type"
                          class="px-3 py-2 bg-slate-900 border border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
                        >
                          <option value="string">String</option>
                          <option value="number">Number</option>
                          <option value="integer">Integer</option>
                          <option value="boolean">Boolean</option>
                          <option value="array">Array</option>
                          <option value="object">Object</option>
                        </select>
                      </div>
                      
                      <div class="flex items-center">
                        <input 
                          id="required-field" 
                          v-model="newSchemaProperty.required" 
                          type="checkbox" 
                          class="h-4 w-4 text-amber-500 focus:ring-amber-500 border-slate-700 rounded bg-slate-900"
                        />
                        <label for="required-field" class="ml-2 text-sm">Required</label>
                      </div>
                      
                      <button 
                        @click="addPropertyToSchema" 
                        class="w-full px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md transition-colors text-sm"
                      >
                        Add Property
                      </button>
                    </div>
                  </div>
                  
                  <div class="border border-slate-700 rounded-md p-3 bg-slate-900/50 max-h-40 overflow-auto">
                    <h5 class="text-sm font-medium mb-1">Current Schema</h5>
                    <pre class="text-xs text-slate-400 whitespace-pre-wrap break-words overflow-x-auto">{{ prettyJson(newCollectionForm.schema) }}</pre>
                  </div>
                  
                  <button 
                    @click="createCollection" 
                    class="w-full px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-medium rounded-md hover:shadow-lg hover:shadow-amber-500/20 transition-all duration-300"
                  >
                    Create Collection
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Main Content -->
            <div class="lg:col-span-3">
              <div v-if="!currentCollection" class="h-full flex flex-col items-center justify-center p-8 text-center">
                <div class="w-16 h-16 mb-4 opacity-30">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="w-16 h-16">
                    <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"></path>
                  </svg>
                </div>
                <h3 class="text-xl font-medium mb-2">Select or create a collection to get started</h3>
                <p class="text-slate-400 max-w-md">Collections will appear in the sidebar once created.</p>
              </div>
              
              <div v-else class="h-full">
                <div class="border-b border-slate-700 p-4 flex items-center justify-between bg-slate-900">
                  <h3 class="font-medium">
                    <span class="text-amber-400">Collection:</span> {{ currentCollection }}
                  </h3>
                  <button 
                    @click="deleteCollection" 
                    class="px-3 py-1.5 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-md text-sm transition-colors"
                  >
                    Delete Collection
                  </button>
                </div>
                
                <div class="p-6">
                  <div class="mb-8">
                    <h4 class="text-lg font-medium mb-3 flex items-center">
                      <svg class="w-5 h-5 mr-2 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                      </svg>
                      Collection Schema
                    </h4>
                    <div class="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                      <pre class="p-4 text-sm text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">{{ prettyJson(collectionSchema) }}</pre>
                    </div>
                  </div>
                  
                  <div>
                    <h4 class="text-lg font-medium mb-3 flex items-center">
                      <svg class="w-5 h-5 mr-2 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                      Documents
                    </h4>
                    
                    <div v-if="loading" class="flex items-center justify-center p-8">
                      <div class="animate-spin rounded-full h-6 w-6 border-t-2 border-amber-500"></div>
                      <span class="ml-2 text-slate-400">Loading documents...</span>
                    </div>
                    
                    <div v-else-if="documents.length === 0" class="text-center py-12 bg-slate-900/50 border border-slate-700 rounded-lg">
                      <svg class="w-12 h-12 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                      <p class="text-slate-400">No documents found in this collection</p>
                    </div>
                    
                    <div v-else class="space-y-4 mb-8">
                      <div v-for="doc in documents" :key="doc.id" class="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                        <div class="p-3 border-b border-slate-700 flex items-center justify-between">
                          <div class="font-mono text-sm text-amber-400">ID: {{ doc.id }}</div>
                          <button 
                            @click="deleteDocument(doc.id)" 
                            class="px-2 py-1 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded text-xs transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                        <pre class="p-4 text-sm text-slate-300 overflow-x-auto">{{ prettyJson(doc) }}</pre>
                      </div>
                    </div>
                    
                    <div class="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                      <div class="p-3 border-b border-slate-700">
                        <h4 class="font-medium text-amber-400">Create Document</h4>
                      </div>
                      <div class="p-4">
                        <div class="mb-4">
                          <label class="block text-sm mb-1">Document JSON</label>
                          <textarea
                            v-model="newDocumentForm.data"
                            rows="8"
                            placeholder="{ ... }"
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 font-mono"
                          ></textarea>
                        </div>
                        <button 
                          @click="createDocument"
                          class="w-full px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-medium rounded-md hover:shadow-lg hover:shadow-amber-500/20 transition-all duration-300"
                        >
                          Create Document
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Documentation Section -->
    <section id="docs" class="py-20 bg-slate-800/50">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold mb-4">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">Documentation</span>
          </h2>
          <p class="text-slate-400 max-w-3xl mx-auto">Get started with QuipuBase in minutes</p>
        </div>
        
        <div class="max-w-4xl mx-auto bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
          <div class="border-b border-slate-700">
            <div class="flex">
              <button 
                @click="setActiveTab('installation')" 
                :class="['px-4 py-3 text-sm font-medium transition-colors border-b-2 focus:outline-none', 
                        activeTab === 'installation' ? 'border-amber-500 text-amber-400' : 'border-transparent hover:border-slate-600']"
                        >
                Installation
              </button>
              <button 
                @click="setActiveTab('usage')" 
                :class="['px-4 py-3 text-sm font-medium transition-colors border-b-2 focus:outline-none', 
                        activeTab === 'usage' ? 'border-amber-500 text-amber-400' : 'border-transparent hover:border-slate-600']"
              >
                Basic Usage
              </button>
              <button 
                @click="setActiveTab('schema')" 
                :class="['px-4 py-3 text-sm font-medium transition-colors border-b-2 focus:outline-none', 
                        activeTab === 'schema' ? 'border-amber-500 text-amber-400' : 'border-transparent hover:border-slate-600']"
              >
                Schema Definition
              </button>
              <button 
                @click="setActiveTab('events')" 
                :class="['px-4 py-3 text-sm font-medium transition-colors border-b-2 focus:outline-none', 
                        activeTab === 'events' ? 'border-amber-500 text-amber-400' : 'border-transparent hover:border-slate-600']"
              >
                Real-time Events
              </button>
            </div>
          </div>
          
          <div class="p-6">
            <!-- Installation Tab -->
            <div v-if="activeTab === 'installation'">
              <h3 class="text-xl font-semibold mb-4">Installation</h3>
              <p class="mb-4 text-slate-400">Add QuipuBase to your project using npm or yarn:</p>
              
              <div class="mb-6">
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">npm</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">npm install quipubase</pre>
                </div>
              </div>
              
              <div class="mb-6">
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">yarn</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">yarn add quipubase</pre>
                </div>
              </div>
              
              <p class="mb-4 text-slate-400">Or import it directly in your project:</p>
              
              <div class="bg-slate-800 rounded-md overflow-hidden">
                <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                  <span class="text-sm font-medium">HTML</span>
                  <button class="text-slate-400 hover:text-slate-300 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                  </button>
                </div>
                <pre class="p-4 text-sm overflow-x-auto text-slate-300">&lt;script src="https://cdn.quipubase.io/quipubase.min.js"&gt;&lt;/script&gt;</pre>
              </div>
            </div>
            
            <!-- Basic Usage Tab -->
            <div v-if="activeTab === 'usage'" class="space-y-6">
              <h3 class="text-xl font-semibold mb-4">Basic Usage</h3>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Initialize QuipuBase</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">import { QuipuBase } from 'quipubase';

// Define your data type (optional but recommended for TypeScript)
interface User {
  name: string;
  email: string;
  age: number;
}

// Initialize the client with your collection ID
const userDb = new QuipuBase&lt;User&gt;('users');
</pre>
                </div>
              </div>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Create a Document</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">// Create a new user
const newUser = await userDb.create({
  name: 'Jane Doe',
  email: 'jane@example.com',
  age: 28
});

console.log('Created user with ID:', newUser.id);
</pre>
                </div>
              </div>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Query Documents</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">// Find all users over the age of 25
const users = await userDb.query({ 
  age: { $gt: 25 } 
});

console.log(`Found ${users.length} users`);
</pre>
                </div>
              </div>
            </div>
            
            <!-- Schema Definition Tab -->
            <div v-if="activeTab === 'schema'" class="space-y-6">
              <h3 class="text-xl font-semibold mb-4">Schema Definition</h3>
              
              <p class="text-slate-400 mb-4">QuipuBase uses JSON Schema to define collection models. Here's an example:</p>
              
              <div class="bg-slate-800 rounded-md overflow-hidden">
                <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                  <span class="text-sm font-medium">JSON Schema</span>
                  <button class="text-slate-400 hover:text-slate-300 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                  </button>
                </div>
                <pre class="p-4 text-sm overflow-x-auto text-slate-300">{
  "title": "User",
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "age": {
      "type": "integer",
      "minimum": 0
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "lastLogin": {
          "type": "string",
          "format": "date-time"
        }
      }
    }
  },
  "required": ["name", "email"]
}</pre>
              </div>
              
              <div class="mt-6">
                <h4 class="text-lg font-medium mb-2">Creating a Collection with Schema</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">import { QuipuBase, JsonSchema } from 'quipubase';

// Create the database instance
const userDb = new QuipuBase&lt;User&gt;('users');

// Define the schema
const userSchema: JsonSchema = {
  title: "User",
  type: "object",
  properties: {
    name: { type: "string" },
    email: { type: "string" },
    age: { type: "integer" }
  },
  required: ["name", "email"]
};

// Create the collection with the schema
const collection = await userDb.createCollection(userSchema);
console.log('Collection created:', collection.id);</pre>
                </div>
              </div>
            </div>
            
            <!-- Real-time Events Tab -->
            <div v-if="activeTab === 'events'" class="space-y-6">
              <h3 class="text-xl font-semibold mb-4">Real-time Events</h3>
              
              <p class="text-slate-400 mb-4">QuipuBase provides a powerful pub/sub architecture for real-time event handling:</p>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Subscribe to Collection Events</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">// Subscribe to all events
const unsubscribe = await userDb.subscribeToEvents((event) => {
  console.log('Event type:', event.event);
  console.log('Document ID:', event.id);
  console.log('Document data:', event.data);
  
  // Handle different event types
  switch (event.event) {
    case 'create':
      console.log('New user created!');
      break;
    case 'update':
      console.log('User updated!');
      break;
    case 'delete':
      console.log('User deleted!');
      break;
  }
});

// Later, unsubscribe when no longer needed
unsubscribe();</pre>
                </div>
              </div>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Custom Event Handling</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">// Use custom handler for more control
await userDb.subscribeWithCustomHandler((chunk) => {
  // Process the raw event data
  try {
    const event = JSON.parse(chunk);
    console.log('Received event:', event);
  } catch (error) {
    console.error('Error parsing event:', error);
  }
});</pre>
                </div>
              </div>
              
              <div>
                <h4 class="text-lg font-medium mb-2">Publishing Custom Events</h4>
                <div class="bg-slate-800 rounded-md overflow-hidden">
                  <div class="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
                    <span class="text-sm font-medium">TypeScript</span>
                    <button class="text-slate-400 hover:text-slate-300 transition-colors">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                      </svg>
                    </button>
                  </div>
                  <pre class="p-4 text-sm overflow-x-auto text-slate-300">// Publish a custom event
await userDb.publishEvent({
  event: 'custom',
  id: 'user-123',
  data: {
    action: 'login',
    timestamp: new Date().toISOString()
  }
});</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mt-12 max-w-4xl mx-auto">
          <h3 class="text-xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">API Reference</h3>
          
          <div class="space-y-4">
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">POST /v1/collections</h4>
                  <p class="text-slate-400 mt-1">Create a new collection with the provided JSON schema.</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">GET /v1/collections</h4>
                  <p class="text-slate-400 mt-1">List all available collections.</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">GET /v1/collections/{collection_id}</h4>
                  <p class="text-slate-400 mt-1">Get details of a specific collection by ID.</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">DELETE /v1/collections/{collection_id}</h4>
                  <p class="text-slate-400 mt-1">Delete a collection by ID.</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">PUT /v1/collections/{collection_id}</h4>
                  <p class="text-slate-400 mt-1">Unified endpoint for collection actions (create, read, update, delete, query).</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">POST /v1/pubsub/events/{collection_id}</h4>
                  <p class="text-slate-400 mt-1">Publish an event to a collection's subscribers.</p>
                </div>
              </div>
            </div>
            
            <div class="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div class="flex items-start">
                <div class="flex-shrink-0 bg-amber-500/10 p-3 rounded-lg">
                  <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                  </svg>
                </div>
                <div class="ml-4">
                  <h4 class="text-lg font-medium">GET /v1/pubsub/events/{collection_id}</h4>
                  <p class="text-slate-400 mt-1">Subscribe to events from a collection.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Footer -->
    <footer class="py-12 bg-slate-900 border-t border-slate-800">
      <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div class="md:col-span-1">
            <div class="flex items-center mb-4">
              <img src="./assets/quipubase-logo.png" alt="QuipuBase Logo" class="w-10 h-10 rounded-md mr-3 shadow-[0_0_15px_rgba(212,175,55,0.5)]" />
              <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-amber-600">QuipuBase</span>
            </div>
            <p class="text-slate-400 text-sm">
              Real-time document database designed for AI-native applications. Built on top of RocksDB with native vector similarity search.
            </p>
          </div>
          
          <div class="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-8">
            <div>
              <h4 class="text-lg font-medium mb-4">Resources</h4>
              <ul class="space-y-2">
                <li><a href="#docs" @click.prevent="scrollToSection('docs')" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Documentation</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Tutorials</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">API Reference</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">SDK Documentation</a></li>
              </ul>
            </div>
            
            <div>
              <h4 class="text-lg font-medium mb-4">Community</h4>
              <ul class="space-y-2">
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">GitHub</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Discord</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Twitter</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Blog</a></li>
              </ul>
            </div>
            
            <div>
              <h4 class="text-lg font-medium mb-4">Company</h4>
              <ul class="space-y-2">
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">About</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Contact</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Privacy Policy</a></li>
                <li><a href="#" class="text-slate-400 hover:text-amber-400 transition-colors text-sm">Terms of Service</a></li>
              </ul>
            </div>
          </div>
        </div>
        
        <div class="mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row md:items-center justify-between">
          <p class="text-slate-500 text-sm">&copy; 2025 QuipuBase. All rights reserved.</p>
          <div class="mt-4 md:mt-0 flex space-x-4">
            <a href="#" class="text-slate-400 hover:text-amber-400 transition-colors">
              <span class="sr-only">GitHub</span>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"></path>
              </svg>
            </a>
            <a href="#" class="text-slate-400 hover:text-amber-400 transition-colors">
              <span class="sr-only">Twitter</span>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
              </svg>
            </a>
            <a href="#" class="text-slate-400 hover:text-amber-400 transition-colors">
              <span class="sr-only">Discord</span>
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"></path>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>

    <!-- Incan-inspired decorative elements -->
    <div class="fixed inset-0 pointer-events-none z-0 opacity-5">
      <!-- Top border pattern -->
      <div class="absolute top-0 left-0 right-0 h-8 bg-gradient-to-r from-amber-600 to-amber-500 pattern-zigzag"></div>
      
      <!-- Bottom border pattern -->
      <div class="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-r from-amber-500 to-amber-600 pattern-zigzag"></div>
      
      <!-- Left border pattern -->
      <div class="absolute top-8 bottom-8 left-0 w-8 bg-gradient-to-b from-amber-600 to-amber-500 pattern-zigzag-vertical"></div>
      
      <!-- Right border pattern -->
      <div class="absolute top-8 bottom-8 right-0 w-8 bg-gradient-to-b from-amber-500 to-amber-600 pattern-zigzag-vertical"></div>
      
      <!-- Corner decorations -->
      <div class="absolute top-0 left-0 w-32 h-32 bg-amber-500 opacity-10" style="clip-path: polygon(0 0, 100% 0, 0 100%)"></div>
      <div class="absolute top-0 right-0 w-32 h-32 bg-amber-500 opacity-10" style="clip-path: polygon(0 0, 100% 0, 100% 100%)"></div>
      <div class="absolute bottom-0 left-0 w-32 h-32 bg-amber-500 opacity-10" style="clip-path: polygon(0 0, 0 100%, 100% 100%)"></div>
      <div class="absolute bottom-0 right-0 w-32 h-32 bg-amber-500 opacity-10" style="clip-path: polygon(100% 0, 0 100%, 100% 100%)"></div>
    </div>
  </div>
</template>
<style>
/* Base styles */
html {
  scroll-behavior: smooth;
}

body {
  @apply bg-slate-900;
}

/* Custom animations */
@keyframes pulse-glow {
  0%, 100% {
    filter: drop-shadow(0 0 8px rgba(217, 119, 6, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 15px rgba(217, 119, 6, 0.8));
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes slide-up {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Incan-inspired patterns */
.pattern-zigzag {
  background-image: url("data:image/svg+xml,%3Csvg width='84' height='48' viewBox='0 0 84 48' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h12v6H0V0zm24 0h12v6H24V0zm36 0h12v6H60V0zm12 0h12v6H72V0zm0 12h12v6H72v-6zm-12 0h12v6H60v-6zm-36 0h12v6H24v-6zm-24 0h12v6H0v-6zm0 12h12v6H0v-6zm24 0h12v6H24v-6zm36 0h12v6H60v-6zm12 0h12v6H72v-6zm0 12h12v6H72v-6zm-12 0h12v6H60v-6zm-36 0h12v6H24v-6zm-24 0h12v6H0v-6zm0 12h12v6H0v-6zm24 0h12v6H24v-6zm36 0h12v6H60v-6zm12 0h12v6H72v-6z' fill='%23d97706' fill-opacity='0.2' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.pattern-zigzag-vertical {
  background-image: url("data:image/svg+xml,%3Csvg width='48' height='84' viewBox='0 0 48 84' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0v12h6V0H0zm0 24v12h6V24H0zm0 36v12h6V60H0zm12 0v12h6V60h-6zm0-12v12h6V48h-6zm0-36V0h6v12h-6zm0 24v12h6V36h-6zm12 0v12h6V36h-6zm0 12v12h6V48h-6zm0-36V0h6v12h-6zm0 24v12h6V36h-6zm12 0v12h6V36h-6zm0 12v12h6V48h-6zm0-36V0h6v12h-6zm0 24v12h6V36h-6zm12 0v12h6V36h-6z' fill='%23d97706' fill-opacity='0.2' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.pattern-sun {
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M50 0 L50 100 M0 50 L100 50 M25 25 L75 75 M25 75 L75 25' stroke='%23d97706' stroke-width='1' stroke-opacity='0.15'/%3E%3Ccircle cx='50' cy='50' r='20' fill='none' stroke='%23d97706' stroke-width='2' stroke-opacity='0.15'/%3E%3C/svg%3E");
  background-size: 50px 50px;
}

/* Animation applied classes */
.header-hidden {
  transform: translateY(-100%);
  transition: transform 0.3s ease;
}

.hero-content.animated {
  animation: slide-up 0.8s ease forwards;
}

.hero-image.animated .image-container {
  animation: float 6s ease-in-out infinite;
}

.glow-effect {
  animation: pulse-glow 3s ease-in-out infinite;
}

/* Call to action button */
.btn-primary.pulsing {
  position: relative;
  overflow: hidden;
}

.btn-primary.pulsing::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.2);
  border-radius: inherit;
  transform: scale(0);
  animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  70% {
    transform: scale(1.3);
    opacity: 0;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-slate-800;
}

::-webkit-scrollbar-thumb {
  @apply bg-slate-600 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-amber-600;
}

/* Loading spinner */
.loading-spinner {
  @apply animate-spin rounded-full h-5 w-5 border-t-2 border-amber-500;
  border-right-color: transparent;
}

/* Ancient symbols */
.ancient-symbol {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 2rem;
  opacity: 0.3;
}

.ancient-symbol::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='40' fill='none' stroke='%23d97706' stroke-width='3' /%3E%3Ccircle cx='50' cy='50' r='20' fill='none' stroke='%23d97706' stroke-width='2' /%3E%3Cpath d='M50 10 L50 90 M10 50 L90 50 M22 22 L78 78 M22 78 L78 22' stroke='%23d97706' stroke-width='2' /%3E%3C/svg%3E");
  background-size: contain;
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Notification system */
.notification {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.notification.hidden {
  transform: translateY(-20px);
  opacity: 0;
}

/* Feature card hover effects */
.feature-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(217, 119, 6, 0.1);
}

/* Incan inspired decorative border for focused elements */
input:focus, 
textarea:focus, 
select:focus {
  box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.3);
  border-color: #d97706;
}

/* Custom transitions for tab switching */
.tab-content {
  transition: opacity 0.3s ease;
}

.tab-content.hidden {
  opacity: 0;
}

/* Button animations */
.btn {
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
  transition: transform 0.5s ease;
  z-index: -1;
  transform: skewX(-15deg);
}

.btn:hover::after {
  transform: translateX(100%) skewX(-15deg);
}

/* Document item hover effects */
.document-item {
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.document-item:hover {
  border-color: rgba(217, 119, 6, 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Active menu item indicator */
nav a.active::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #d97706;
  animation: slide-in 0.3s ease forwards;
}

@keyframes slide-in {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

/* Code block styling */
pre {
  position: relative;
  font-family: 'Fira Code', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  tab-size: 2;
}

pre::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}

/* Make sure code stays readable in dark theme */
pre code {
  color: #e2e8f0;
}

/* Fix for mobile nav menu */
@media (max-width: 768px) {
  .container {
    width: 100%;
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  .hero {
    padding-top: 100px;
  }
  
  .explorer-layout {
    display: block;
  }
  
  .sidebar {
    width: 100%;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid var(--slate-700);
  }
}
</style>
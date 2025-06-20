import os
import typing as tp
from functools import wraps

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing_extensions import ParamSpec

from prisma import Prisma

from .utils import get_logger

P = ParamSpec("P")

logger = get_logger()

LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quipubase | The Data API for AI - Extending OpenAI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'stone-warm': '#d4c4a7',
                        'copper': '#b87333',
                        'teal-deep': '#2d5a5a',
                        'sage': '#7a8471'
                    }
                }
            }
        }
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="/static/favicon.svg" rel="icon">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }

        .gradient-bg {
            background: linear-gradient(135deg, #2d5a5a 0%, #4a6741 100%);
        }

        .code-block {
            background: #1e1e1e;
            border-radius: 8px;
            border: 1px solid #333;
            position: relative;
            overflow: hidden;
        }

        .tab-button {
            transition: all 0.2s ease;
        }

        .tab-button.active {
            background: #2d5a5a;
            color: white;
        }

        .copy-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            background: #b87333;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
        }

        .code-block:hover .copy-btn {
            opacity: 1;
        }

        .section {
            display: none;
        }

        .section.active {
            display: block;
        }

        .nav-item {
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }

        .nav-item:hover {
            background: rgba(45, 90, 90, 0.1);
            border-left-color: #b87333;
        }

        .nav-item.active {
            background: rgba(45, 90, 90, 0.15);
            border-left-color: #2d5a5a;
            font-weight: 500;
        }

        .feature-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(45, 90, 90, 0.15);
        }

        .logo-container {
            width: 48px;
            height: 48px;
            background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjQiIGN5PSIyNCIgcj0iMjMiIGZpbGw9IiMyZDVhNWEiIHN0cm9rZT0iI2I4NzMzMyIgc3Ryb2tlLXdpZHRoPSIyIi8+CjxwYXRoIGQ9MTE2IDE2SDMyVjMyaDE2VjE2WiIgZmlsbD0iI2I4NzMzMyIvPgo8cGF0aCBkPSJNMjAgMjBINjBWMjhINjBWMjBaIiBmaWxsPSIjN0E4NDcxIi8+Cjwvc3ZnPgo=') center/contain no-repeat;
        }

        /* Styles for Todo List example */
        .todo-list {
            background-color: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            max-width: 600px;
            margin: 0 auto;
        }

        .todo-list h2 {
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2d5a5a;
        }

        .todo-list form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .todo-list input[type="text"] {
            flex-grow: 1;
            padding: 10px 15px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .todo-list input[type="text"]:focus {
            border-color: #b87333;
        }

        .todo-list button {
            background-color: #b87333;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: background-color 0.2s;
        }

        .todo-list button:hover {
            background-color: #a0662d;
        }

        .todo-list ul {
            list-style: none;
            padding: 0;
        }

        .todo-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }

        .todo-item:last-child {
            border-bottom: none;
        }

        .todo-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
            accent-color: #2d5a5a;
            cursor: pointer;
        }

        .todo-item span {
            flex-grow: 1;
            font-size: 1rem;
            color: #374151;
        }

        .todo-item span.completed {
            text-decoration: line-through;
            opacity: 0.6;
            color: #6b7280;
        }

        .todo-item button {
            background-color: #dc2626;
            padding: 6px 12px;
            font-size: 0.875rem;
            border-radius: 6px;
        }

        .todo-item button:hover {
            background-color: #b91c1c;
        }

        .todo-list .loading,
        .todo-list .error {
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-style: italic;
        }
    </style>
</head>

<body class="bg-gray-50">
    <header class="gradient-bg text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="logo-container">
                    <img src='static/favicon.svg' />
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold">Quipubase</h1>
                        <p class="text-teal-100 text-sm">Real-time Database for Modern Frontend</p>
                    </div>
                </div>
                <div class="hidden md:flex items-center space-x-6">
                    <a href="https://github.com/bahamondeX/quipubase-client-typescript"
                        class="text-teal-100 hover:text-white flex items-center space-x-2" target="_blank">
                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path fill-rule="evenodd"
                                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.499.09.679-.217.679-.481 0-.237-.008-.865-.013-1.703-2.782.602-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.46-1.11-1.46-.908-.618.069-.606.069-.606 1.003.07 1.531 1.032 1.531 1.032.892 1.529 2.341 1.089 2.91.833.091-.647.351-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.931 0-1.091.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.701.114 2.503.344 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.099 2.65.64.7 1.028 1.597 1.028 2.688 0 3.839-2.339 4.675-4.562 4.922.357.307.676.917.676 1.854 0 1.338-.012 2.419-.012 2.747 0 .268.18.577.685.479C21.133 20.283 24 16.529 24 12.017 24 6.484 19.522 2 14 2h-2z" />
                        </svg>
                        <span>GitHub</span>
                    </a>
                    <a href="/docs" class="bg-copper px-4 py-2 rounded-lg hover:bg-opacity-90 transition">Get
                        Started</a>
                </div>
            </div>
        </div>
    </header>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <aside class="lg:col-span-1">
                <nav class="sticky top-8 space-y-1">
                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2">Getting Started
                    </div>
                    <a href="#overview" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md active"
                        data-section="overview">Overview</a>
                    <a href="#installation" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="installation">Installation</a>
                    <a href="#quickstart" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="quickstart">Quick Start</a>

                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2 mt-6">Vue.js
                        Integration</div>
                    <a href="#vue-setup" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="vue-setup">Vue
                        Setup</a>
                    <a href="#vue-examples" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="vue-examples">Vue Examples</a>
                    
                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2 mt-6">React
                        Integration</div>
                    <a href="#react-setup" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="react-setup">React Setup</a>
                    <a href="#react-examples" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="react-examples">React Examples</a>
                    
                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2 mt-6">Quipubase Data APIs for AI</div>
                    <a href="#collections-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="collections-api">Collections API</a>
                    <a href="#vector-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="vector-api">Vector API (Embeddings & Search)</a>
                    <a href="#chat-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="chat-api">Chat API (Completions)</a>
                    <a href="#files-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="files-api">Files API (Upload, Process & Retrieve)</a>
                    <a href="#audio-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="audio-api">Audio API (Speech & Transcriptions)</a>
                    <a href="#models-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="models-api">Models API</a>
                    <a href="#auth-api" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="auth-api">Auth API</a>


                    <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2 mt-6">Core Features & Concepts</div>
                    <a href="#realtime" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md" data-section="realtime">Real-time
                        Updates</a>
                    <a href="#schema-validation" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="schema-validation">JSON Schema & Validation</a>
                    <a href="#document-processing" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="document-processing">Document Processing</a>
                    <a href="#file-chunking" class="nav-item block px-3 py-2 text-sm text-gray-700 rounded-md"
                        data-section="file-chunking">File Chunking</a>
                    </nav>
                    </aside>
            <main class="lg:col-span-3">
                <section id="overview" class="section active">
                    <div class="mb-8">
                        <h2 class="text-3xl font-bold text-gray-900 mb-4">Welcome to Quipubase: Your Frontend's New Best
                            Friend!</h2>
                        <p class="text-lg text-gray-600 mb-6">
                            Quipubase is a modern, real-time document collection database crafted specifically for
                            frontend developers.
                            Say goodbye to backend complexities and hello to building reactive, data-driven applications
                            with Vue.js, React, and beyond, effortlessly.
                            It's a database that speaks your language: JavaScript, JSON, and real-time magic!
                        </p>
                        <p class="text-lg text-gray-600 mb-6">
                            At its core, Quipubase is powered by **JSON Schema**, ensuring your data is always
                            structured, validated, and ready for prime time.
                            With built-in **AI capabilities** and **vector embeddings for similarity search**, your
                            applications can understand and retrieve data in ways never before possible.
                            <strong class="text-teal-deep">Notably, Quipubase extends the OpenAI API, providing familiar
                            interfaces for chat completions, image generations, and audio processing, allowing for a
                            seamless transition for developers already familiar with OpenAI's ecosystem. This makes Quipubase
                            the ultimate <span class="text-copper">Data API for AI</span>, combining robust database features
                            with powerful generative AI capabilities.</strong>
                            Plus, it's designed to make **document processing** a breeze, letting you focus on the user
                            experience.
                        </p>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="feature-card">
                            <div class="w-12 h-12 bg-teal-deep rounded-lg flex items-center justify-center mb-4">
                                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                </svg>
                            </div>
                            <h3 class="text-lg font-semibold text-gray-900 mb-2">Blazing Fast Real-time Updates</h3>
                            <p class="text-gray-600">Experience instant data synchronization across all connected
                                clients with our robust WebSocket-based pub/sub system. Your UI updates before you can
                                even blink!</p>
                            </div>
                            <div class="feature-card">
                                <div class="w-12 h-12 bg-copper rounded-lg flex items-center justify-center mb-4">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                                        </path>
                                    </svg>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Rock-Solid JSON Schema Validation</h3>
                                <p class="text-gray-600">Leverage built-in Zod integration for type-safe data models and
                                    automatic validation. Keep your data clean and consistent without breaking a sweat.</p>
                            </div>
                            <div class="feature-card">
                                <div class="w-12 h-12 bg-sage rounded-lg flex items-center justify-center mb-4">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">AI-Powered Vector Search</h3>
                                <p class="text-gray-600">Unlock intelligent data retrieval with AI-powered semantic search
                                    and built-in embedding models. Find what you mean, not just what you type!</p>
                            </div>
                            <div class="feature-card">
                                <div class="w-12 h-12 bg-stone-warm rounded-lg flex items-center justify-center mb-4">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37-2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z">
                                        </path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z">
                                        </path>
                                    </svg>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Framework Agnostic & Developer Friendly
                                </h3>
                                <p class="text-gray-600">Works seamlessly with Vue.js, React, and any modern JavaScript
                                    framework. Designed for developers, by developers, with a focus on delightful DX.</p>
                            </div>
                            <div class="feature-card">
                                <div class="w-12 h-12 bg-teal-deep rounded-lg flex items-center justify-center mb-4">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                                        </path>
                                    </svg>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Effortless Document Processing</h3>
                                <p class="text-gray-600">Store, manage, and query diverse document types with ease.
                                    Quipubase is your go-to for building content management systems, knowledge bases, and
                                    more!</p>
                            </div>
                            <div class="feature-card">
                                <div class="w-12 h-12 bg-sage rounded-lg flex items-center justify-center mb-4">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Collections, Not Tables</h3>
                                <p class="text-gray-600">Organize your data into flexible document collections, designed for
                                    the dynamic needs of modern applications. No rigid tables, just pure data freedom.</p>
                            </div>
                            </div>
                            </section>
                            <section id="installation" class="section">
                                <h2 class="text-3xl font-bold text-gray-900 mb-6">Installation</h2>
                                <p class="text-lg text-gray-600 mb-6">Getting Quipubase up and running is as easy as pie. Choose
                                    your preferred method below!</p>

                    <div class="mb-6">
                        <h3 class="text-xl font-semibold text-gray-800 mb-3">Package Manager</h3>
                        <div class="code-block">
                            <button class="copy-btn">Copy</button>
                            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code># npm
                                                                                                    npm install quipubase

# yarn
yarn add quipubase

# pnpm
pnpm add quipubase</code></pre>
</div>
</div>
<div class="mb-6">
    <h3 class="text-xl font-semibold text-gray-800 mb-3">CDN (Browser)</h3>
    <p class="text-gray-600 mb-3">For quick prototyping or simple projects, you can include
        Quipubase directly in your HTML:</p>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre
            class="p-4 text-sm text-gray-300 overflow-x-auto"><code>&lt;script src="https://cdn.jsdelivr.net/npm/quipubase@latest/dist/index.umd.js"&gt;&lt;/script&gt;</code></pre>
    </div>
</div>
</section>
                <section id="quickstart" class="section">
                    <h2 class="text-3xl font-bold text-gray-900 mb-6">Quick Start: Your First Quipubase App!</h2>
                    <p class="text-lg text-gray-600 mb-6">
                        Let's get your hands dirty and build a simple application with Quipubase.
                        We'll define a data model, initialize the client, and create your first collection.
                    </p>

                    <div class="mb-6">
                        <h3 class="text-xl font-semibold text-gray-800 mb-3">1. Define Your Model (with Zod!)</h3>
                        <p class="text-gray-600 mb-3">
                            Quipubase loves structured data! Define your data models using Zod schemas for robust
                            validation and type safety.
                            It's like giving your data a superpower!
                        </p>
                        <div class="code-block">
                            <button class="copy-btn">Copy</button>
                            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { z } from 'zod';
import { BaseModel } from 'quipubase'; // Updated import

class Todo extends BaseModel {
    title!: string;
    completed!: boolean;
    createdAt!: Date;

    static schema() {
        return z.object({
            id: z.string().optional(),
            title: z.string().min(1, 'Title is required'),
            completed: z.boolean().default(false),
            createdAt: z.date().default(() => new Date())
        });
    }
}</code></pre>
                        </div>
                    </div>
                    <div class="mb-6">
                        <h3 class="text-xl font-semibold text-gray-800 mb-3">2. Initialize Your Quipubase Client</h3>
                        <p class="text-gray-600 mb-3">
                            Connect to your Quipubase server. Think of this as opening the door to your real-time data
                            kingdom!
                        </p>
                        <div class="code-block">
                            <button class="copy-btn">Copy</button>
                            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase'; // Updated import

// Replace 'http://localhost:5454' with your Quipubase server URL
const client = new QuipuBase&lt;Todo&gt;('http://localhost:5454');</code></pre>
</div>
                    </div>
                    <div class="mb-6">
                        <h3 class="text-xl font-semibold text-gray-800 mb-3">3. Create a Collection & Add Data</h3>
                        <p class="text-gray-600 mb-3">
                            Collections are where your documents live. Let's create one and add some initial data.
                            The `publishEvent` method makes your data available in real-time to all subscribers!
                        </p>
                        <div class="code-block">
                            <button class="copy-btn">Copy</button>
                            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// Create a new collection for your Todos. Uses modelJsonSchema() for schema definition.
const collection = await client.createCollection(Todo);

// Add some data to your new collection. Use .modelDump() to get plain object.
await client.publishEvent(collection.id, {
    event: 'create', // 'create', 'update', or 'delete'
    data: new Todo({
        title: 'Learn Quipubase like a boss!',
        completed: false
    }).modelDump() // Updated: Use .modelDump()
});

console.log('First todo added to Quipubase!');</code></pre>
                        </div>
                        </div>
                </section>
                <section id="vue-setup" class="section">
                    <h2 class="text-3xl font-bold text-gray-900 mb-6">Vue.js Setup: Reactive Data, Vue-Style!</h2>
                    <p class="text-lg text-gray-600 mb-6">
                        Integrating Quipubase into your Vue.js application is seamless.
                        We recommend using a plugin for global access and a composable for reactive data fetching.
                    </p>

                    <div class="mb-6">
                        <h3 class="text-xl font-semibold text-gray-800 mb-3">Plugin Installation (<code>main.js</code>)
                        </h3>
                        <p class="text-gray-600 mb-3">
                            Make your Quipubase client globally available across your Vue app.
                        </p>
                        <div class="code-block">
                            <button class="copy-btn">Copy</button>
                            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// plugins/quipubase.js
import { QuipuBase } from 'quipubase'; // Updated import

export default {
    install(app, options) {
        const client = new QuipuBase(options.baseUrl);
        app.config.globalProperties.$quipu = client; // For Options API
        app.provide('quipu', client); // For Composition API
    }
};

// main.js
import { createApp } from 'vue';
import App from './App.vue';
import QuipubasePlugin from './plugins/quipubase';

const app = createApp(App);
app.use(QuipubasePlugin, { baseUrl: 'http://localhost:5454' }); // Your Quipubase server URL
app.mount('#app');</code></pre>
</div>
</div>
<div class="mb-6">
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Composable (Recommended for Vue 3)</h3>
    <p class="text-gray-600 mb-3">
        A custom composable simplifies subscribing to real-time data and publishing events within
        your components.
        It's reactive, clean, and keeps your components focused on presentation!
    </p>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// composables/useQuipubase.js
import { ref, onMounted, onUnmounted, inject } from 'vue';
import { BaseModel } from 'quipubase'; // Ensure BaseModel is imported if used in types

export function useQuipubase(collectionId) {
    const client = inject('quipu'); // Get the Quipubase client from provide/inject
    const data = ref([]);
    const loading = ref(false);
    const error = ref(null);

    let unsubscribe = null;

    const subscribe = async () => {
        if (!client) {
            error.value = new Error('Quipubase client not injected. Ensure QuipubaseProvider is used.');
            return;
        }
        try {
            loading.value = true;
            // The callback now receives SSEEvent<T>
            unsubscribe = await client.subscribe(collectionId, (event) => {
                const todo = new BaseModel().load(event.data); // Load the raw data into a Todo model instance
                
                // Reactive update logic based on event type
                if (event.event === 'create') {
                    data.value.push(todo);
                } else if (event.event === 'update') {
                    const index = data.value.findIndex(t => t.id === todo.id);
                    if (index !== -1) {
                        data.value[index] = todo;
                    }
                } else if (event.event === 'delete') {
                    data.value = data.value.filter(t => t.id !== todo.id);
                }
            });
            // Initial fetch of data (optional, depending on your needs)
            // You might want to fetch existing data before subscribing to events
            const initialData = await client.getCollectionRecords(collectionId);
            data.value = initialData.map(d => new BaseModel().load(d)); // Map initial data to Todo models
        } catch (err) {
            error.value = err;
            console.error("Subscription error:", err);
        } finally {
            loading.value = false;
        }
    };

    const publish = async (event, payload) => {
        if (!client) {
            error.value = new Error('Quipubase client not injected.');
            return;
        }
        try {
            await client.publishEvent(collectionId, { event, data: payload });
        } catch (err) {
            error.value = err;
            console.error("Publish error:", err);
        }
    };

    onMounted(() => {
        subscribe();
    });

    onUnmounted(() => {
        if (unsubscribe) {
            unsubscribe(); // Clean up the subscription
        }
    });

    return { data, loading, error, publish };
}</code></pre>
</div>
</section>

<section id="vue-examples" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Vue.js Examples: Building a Real-time Todo App</h2>
    <p class="text-lg text-gray-600 mb-6">
        Let's put it all together! Here's how you can create a simple real-time Todo application using
        Quipubase with Vue.js's Composition API.
    </p>

    <h3 class="text-xl font-semibold text-gray-800 mb-3">Todo List Component (<code>TodoList.vue</code>)</h3>
    <p class="text-gray-600 mb-3">
        This component uses the `useQuipubase` composable to fetch and manage todos in real-time.
    </p>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>&lt;template&gt;
    &lt;div class="todo-list"&gt;
        &lt;h2&gt;My Real-time Todos&lt;/h2&gt;
        &lt;form @submit.prevent="addTodo"&gt;
            &lt;input type="text" v-model="newTodoTitle" placeholder="Add a new todo..." /&gt;
            &lt;button type="submit"&gt;Add Todo&lt;/button&gt;
        &lt;/form&gt;
        &lt;div v-if="loading" class="loading"&gt;Loading todos...&lt;/div&gt;
        &lt;div v-else-if="error" class="error"&gt;Error: {{ error.message }}&lt;/div&gt;
        &lt;ul v-else&gt;
            &lt;li v-for="todo in data" :key="todo.id" class="todo-item"&gt;
                &lt;input type="checkbox" :checked="todo.completed" @change="toggleTodo(todo)" /&gt;
                &lt;span :class="{ 'completed': todo.completed }"&gt;{{ todo.title }}&lt;/span&gt;
                &lt;button @click="deleteTodo(todo.id)"&gt;Delete&lt;/button&gt;
            &lt;/li&gt;
        &lt;/ul&gt;
    &lt;/div&gt;
&lt;/template&gt;

&lt;script setup&gt;
import { ref, inject } from 'vue';
import { useQuipubase } from '../composables/useQuipubase';
import { BaseModel, QuipuBase } from 'quipubase'; // Ensure QuipuBase and BaseModel are imported for use in methods
import { z } from 'zod'; // Import Zod

// Define the Todo model inline or import it from a shared file
class Todo extends BaseModel {
    title;
    completed;
    createdAt;

    static schema() {
        return z.object({
            id: z.string().optional(),
            title: z.string().min(1, 'Title is required'),
            completed: z.boolean().default(false),
            createdAt: z.date().default(() => new Date())
        });
    }
}

// Assume 'todos' is your collection ID
const collectionId = 'todos'; 
const { data, loading, error, publish } = useQuipubase(collectionId);
const newTodoTitle = ref('');

// Initialize client to create collection if it doesn't exist
const client = inject('quipu');
if (client && !(await client.getCollection(collectionId))) {
    await client.createCollection(Todo, collectionId);
    console.log(`Collection '${collectionId}' created.`);
}


const addTodo = async () => {
    if (newTodoTitle.value.trim()) {
        const newTodo = new Todo({ title: newTodoTitle.value.trim(), completed: false });
        await publish('create', newTodo.modelDump());
        newTodoTitle.value = '';
    }
};

const toggleTodo = async (todo) => {
    const updatedTodo = new Todo().load({ ...todo, completed: !todo.completed });
    await publish('update', updatedTodo.modelDump());
};

const deleteTodo = async (id) => {
    await publish('delete', { id: id }); // For delete, typically just need the ID
};
&lt;/script&gt;
</code></pre>
    </div>
</section>

<section id="react-setup" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">React Setup: Hooks, Context, and Real-time Bliss!</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase plays perfectly with React. We'll use React Context for client provision and a custom hook
        for real-time data synchronization.
    </p>

    <div class="mb-6">
        <h3 class="text-xl font-semibold text-gray-800 mb-3">Context Provider (<code>QuipubaseProvider.js</code>)</h3>
        <p class="text-600 mb-3">
            Provide the Quipubase client instance to your entire React application.
        </p>
        <div class="code-block">
            <button class="copy-btn">Copy</button>
            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// contexts/QuipubaseContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';
import { QuipuBase } from 'quipubase';

const QuipubaseContext = createContext(null);

export const QuipubaseProvider = ({ children, baseUrl }) => {
    const [client, setClient] = useState(null);

    useEffect(() => {
        const qpClient = new QuipuBase(baseUrl);
        setClient(qpClient);
    }, [baseUrl]);

    return (
        &lt;QuipubaseContext.Provider value={client}&gt;
            {children}
        &lt;/QuipubaseContext.Provider&gt;
    );
};

export const useQuipubaseClient = () => {
    const client = useContext(QuipubaseContext);
    if (!client) {
        throw new Error('useQuipubaseClient must be used within a QuipubaseProvider');
    }
    return client;
};</code></pre>
        </div>
    </div>

    <div class="mb-6">
        <h3 class="text-xl font-semibold text-gray-800 mb-3">Custom Hook (<code>useQuipubase.js</code>)</h3>
        <p class="text-gray-600 mb-3">
            This hook abstracts the real-time subscription logic, making your components clean and declarative.
        </p>
        <div class="code-block">
            <button class="copy-btn">Copy</button>
            <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// hooks/useQuipubase.js
import { useState, useEffect, useCallback } from 'react';
import { useQuipubaseClient } from '../contexts/QuipubaseContext';
import { BaseModel } from 'quipubase';

export function useQuipubase(collectionId, ModelClass) {
    const client = useQuipubaseClient();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const publish = useCallback(async (event, payload) => {
        try {
            await client.publishEvent(collectionId, { event, data: payload });
        } catch (err) {
            setError(err);
            console.error("Publish error:", err);
        }
    }, [client, collectionId]);

    useEffect(() => {
        if (!client) return;

        let unsubscribe;
        const init = async () => {
            try {
                setLoading(true);
                // Ensure collection exists
                let collection = await client.getCollection(collectionId);
                if (!collection) {
                    await client.createCollection(ModelClass, collectionId);
                }

                // Initial fetch
                const initialData = await client.getCollectionRecords(collectionId);
                setData(initialData.map(d => new ModelClass().load(d)));

                // Subscribe to real-time updates
                unsubscribe = await client.subscribe(collectionId, (event) => {
                    const modelInstance = new ModelClass().load(event.data);
                    
                    setData(currentData => {
                        if (event.event === 'create') {
                            return [...currentData, modelInstance];
                        } else if (event.event === 'update') {
                            return currentData.map(item => item.id === modelInstance.id ? modelInstance : item);
                        } else if (event.event === 'delete') {
                            return currentData.filter(item => item.id !== modelInstance.id);
                        }
                        return currentData; // No change
                    });
                });
            } catch (err) {
                setError(err);
                console.error("Quipubase hook error:", err);
            } finally {
                setLoading(false);
            }
        };

        init();

        return () => {
            if (unsubscribe) {
                unsubscribe(); // Clean up on unmount
            }
        };
    }, [client, collectionId, ModelClass]);

    return { data, loading, error, publish };
}</code></pre>
        </div>
    </div>
</section>

<section id="react-examples" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">React Examples: Building a Real-time Todo App</h2>
    <p class="text-lg text-gray-600 mb-6">
        Here’s a full example of a real-time Todo application in React using the `useQuipubase` hook and `QuipubaseProvider`.
    </p>

    <h3 class="text-xl font-semibold text-gray-800 mb-3">Root App Component (<code>App.js</code>)</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// App.js
import React from 'react';
import { QuipubaseProvider } from './contexts/QuipubaseContext';
import TodoList from './components/TodoList'; // Assuming TodoList component is in ./components/TodoList.js
import { BaseModel } from 'quipubase';
import { z } from 'zod';

// Define the Todo model (can be in a shared models/Todo.js file)
class Todo extends BaseModel {
    title;
    completed;
    createdAt;

    static schema() {
        return z.object({
            id: z.string().optional(),
            title: z.string().min(1, 'Title is required'),
            completed: z.boolean().default(false),
            createdAt: z.date().default(() => new Date())
        });
    }
}

function App() {
    return (
        &lt;QuipubaseProvider baseUrl="http://localhost:5454"&gt; {/* Replace with your Quipubase server URL */}
            &lt;div class="container mx-auto p-4"&gt;
                &lt;TodoList TodoModel={Todo} /&gt; {/* Pass the model class */}
            &lt;/div&gt;
        &lt;/QuipubaseProvider&gt;
    );
}

export default App;</code></pre>
    </div>

    <h3 class="text-xl font-semibold text-gray-800 mb-3">Todo List Component (<code>TodoList.js</code>)</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// components/TodoList.js
import React, { useState } from 'react';
import { useQuipubase } from '../hooks/useQuipubase';

function TodoList({ TodoModel }) {
    const collectionId = 'todos'; // Consistent collection ID
    const { data, loading, error, publish } = useQuipubase(collectionId, TodoModel);
    const [newTodoTitle, setNewTodoTitle] = useState('');

    const addTodo = async (e) => {
        e.preventDefault();
        if (newTodoTitle.trim()) {
            const newTodo = new TodoModel({ title: newTodoTitle.trim(), completed: false });
            await publish('create', newTodo.modelDump());
            setNewTodoTitle('');
        }
    };

    const toggleTodo = async (todo) => {
        const updatedTodo = new TodoModel().load({ ...todo, completed: !todo.completed });
        await publish('update', updatedTodo.modelDump());
    };

    const deleteTodo = async (id) => {
        await publish('delete', { id: id });
    };

    return (
        &lt;div class="todo-list"&gt;
            &lt;h2&gt;My Real-time Todos (React)&lt;/h2&gt;
            &lt;form onSubmit={addTodo}&gt;
                &lt;input
                    type="text"
                    value={newTodoTitle}
                    onChange={(e) => setNewTodoTitle(e.target.value)}
                    placeholder="Add a new todo..."
                /&gt;
                &lt;button type="submit"&gt;Add Todo&lt;/button&gt;
            &lt;/form&gt;
            {loading && &lt;div class="loading"&gt;Loading todos...&lt;/div&gt;}
            {error && &lt;div class="error"&gt;Error: {error.message}&lt;/div&gt;}
            {!loading && !error && data.length === 0 && &lt;div class="text-center text-gray-500 mt-4"&gt;No todos yet! Add one above.&lt;/div&gt;}
            &lt;ul&gt;
                {data.map((todo) => (
                    &lt;li key={todo.id} class="todo-item"&gt;
                        &lt;input
                            type="checkbox"
                            checked={todo.completed}
                            onChange={() => toggleTodo(todo)}
                        /&gt;
                        &lt;span className={todo.completed ? 'completed' : ''}&gt;{todo.title}&lt;/span&gt;
                        &lt;button onClick={() => deleteTodo(todo.id)}&gt;Delete&lt;/button&gt;
                    &lt;/li&gt;
                ))}
            &lt;/ul&gt;
        &lt;/div&gt;
    );
}

export default TodoList;</code></pre>
    </div>
</section>

<section id="collections-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Collections API: Your Flexible Data Foundation</h2>
    <p class="text-lg text-gray-600 mb-6">
        The Collections API in Quipubase provides the core functionality for managing your real-time document database. Unlike traditional relational databases, Quipubase uses a schema-driven document model based on JSON Schema, offering unparalleled flexibility for your evolving data needs. This is the foundation upon which your AI applications store and retrieve their operational data.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoints:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>GET /v1/collections</code>: List all existing collections.</li>
        <li><code>POST /v1/collections</code>: Create a new collection with a defined JSON Schema.</li>
        <li><code>GET /v1/collections/{collection_id}</code>: Retrieve metadata for a specific collection.</li>
        <li><code>DELETE /v1/collections/{collection_id}</code>: Delete an entire collection and its data.</li>
        <li><code>POST /v1/collections/objects/{collection_id}</code>: Publish new documents or updates to a collection (pub/sub).</li>
        <li><code>GET /v1/collections/objects/{collection_id}</code>: Subscribe to real-time events for a specific collection.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Creating and Interacting with a Collection</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase, BaseModel } from 'quipubase';
import { z } from 'zod';

class Product extends BaseModel {
    name!: string;
    price!: number;
    description?: string;

    static schema() {
        return z.object({
            id: z.string().optional(),
            name: z.string().min(1, 'Product name is required'),
            price: z.number().positive('Price must be positive'),
            description: z.string().optional()
        });
    }
}

const client = new QuipuBase&lt;Product&gt;('http://localhost:5454');

async function manageProducts() {
    // Create a new collection for products
    const productsCollection = await client.createCollection(Product, 'products');
    console.log('Products collection created:', productsCollection.id);

    // Add a new product
    const newProduct = new Product({ name: 'Wireless Headphones', price: 99.99 });
    await client.publishEvent(productsCollection.id, { event: 'create', data: newProduct.modelDump() });
    console.log('Added new product.');

    // Subscribe to real-time updates for products
    const unsubscribe = await client.subscribe(productsCollection.id, (event) => {
        console.log('Product event received:', event.event, event.data);
    });

    // Clean up subscription after some time (or on component unmount)
    // setTimeout(() => {
    //     unsubscribe();
    //     console.log('Unsubscribed from products.');
    // }, 5000);
}

// manageProducts();
</code></pre>
    </div>
</section>

<section id="vector-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Vector API: AI-Powered Search and Embeddings</h2>
    <p class="text-lg text-gray-600 mb-6">
        The Vector API is central to Quipubase's role as a **Data API for AI**. It enables you to integrate powerful vector similarity search capabilities directly into your applications. By allowing you to store and query high-dimensional vector embeddings, you can perform semantic searches, find conceptually similar data, and power advanced AI features like Retrieval Augmented Generation (RAG).
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoints:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>POST /v1/vector/{namespace}</code>: Upsert (update or insert) texts and their embeddings into a specified vector namespace.</li>
        <li><code>DELETE /v1/vector/{namespace}</code>: Delete embeddings from a vector namespace by ID.</li>
        <li><code>PUT /v1/vector/{namespace}</code>: Query the vector store for texts similar to a given query.</li>
        <li><code>POST /v1/embeddings</code>: Generate embeddings for input text(s) using specified models.</li>
        <li><code>GET /v1/vector/{namespace}/{id}</code>: Retrieve a specific embedding by ID from a namespace.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Semantic Search for Documentation</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase';

const client = new QuipuBase('http://localhost:5454');

async function performSemanticSearch() {
    const namespace = "documentation-snippets";

    // 1. Upsert some text snippets into the vector store
    const textsToEmbed = [
        "Quipubase is a real-time document database.",
        "It supports schema-driven collections using JSON schema.",
        "Vector search enables finding similar content semantically.",
        "Real-time pub/sub allows instant updates to UI.",
        "Quipubase extends OpenAI API for AI capabilities."
    ];

    const upsertResponse = await client.embedText({
        input: textsToEmbed,
        model: "poly-sage" // Use one of the supported models: 'poly-sage', 'deep-pulse', 'mini-scope'
    }, namespace);
    console.log('Upserted embeddings:', upsertResponse.data);

    // 2. Query for similar content
    const query = "how to get live data updates?";
    const queryResponse = await client.queryText({
        namespace: namespace,
        query: query,
        top_k: 2, // Get top 2 most similar results
        model: "poly-sage"
    });
    console.log(`\nResults for query "${query}":`);
    queryResponse.matches.forEach(match => {
        console.log(`  - Content: "${match.content}" (Score: ${match.score.toFixed(4)})`);
    });

    // 3. (Optional) Delete an embedding
    // if (upsertResponse.data.length > 0) {
    //     const idToDelete = upsertResponse.data[0].id;
    //     await client.deleteEmbeddings(namespace, [idToDelete]);
    //     console.log(`\nDeleted embedding with ID: ${idToDelete}`);
    // }
}

// performSemanticSearch();
</code></pre>
    </div>
</section>

<section id="chat-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Chat API: Powering Conversational AI (OpenAI API Extension)</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase extends the **OpenAI Chat Completions API**, providing a familiar and powerful interface for building conversational AI into your applications. This allows you to leverage large language models (LLMs) for generating human-like text, conducting dialogues, and more, directly through your Quipubase backend.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoint:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>POST /v1/chat/completions</code>: Generate chat completions based on a sequence of messages and a specified model.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Simple Chat Completion</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase';

const client = new QuipuBase('http://localhost:5454'); // Initialize with your Quipubase server URL

async function getChatCompletion() {
    try {
        const response = await client.chatCompletions({
            model: "gemini-2.5-pro-preview-06-05", // Or any other supported model
            messages: [
                { role: "system", content: "You are a helpful assistant." },
                { role: "user", content: "Tell me a fun fact about the ocean." }
            ],
            max_tokens: 100
        });
        console.log('Chat Completion:', response.choices[0].message.content);
    } catch (error) {
        console.error("Error getting chat completion:", error);
    }
}

// getChatCompletion();
</code></pre>
    </div>
</section>

<section id="files-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Files API: Centralized Document Management for AI Workflows</h2>
    <p class="text-lg text-gray-600 mb-6">
        The Files API enables robust document storage, management, and processing within Quipubase. This is crucial for AI applications that deal with diverse content, allowing you to easily ingest and prepare data for tasks like vector embedding, RAG, and more.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoints:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>POST /v1/files</code>: Upload a file and optionally chunk its content.</li>
        <li><code>PUT /v1/files/{path}</code>: Update an existing file by its path.</li>
        <li><code>DELETE /v1/files/{path}</code>: Delete a file from storage.</li>
        <li><code>GET /v1/file/{path}</code>: Retrieve a specific file by its path.</li>
        <li><code>GET /v1/filestree/{path}</code>: List files and directories (useful for exploring stored documents).</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Uploading and Retrieving a Document</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// This example assumes you are running in a browser environment or a Node.js environment with FormData support.
// You would typically use the client-side library to abstract these fetch calls.

async function uploadAndRetrieveFile() {
    const fileContent = "This is a sample document for Quipubase file API.";
    const fileBlob = new Blob([fileContent], { type: 'text/plain' });
    const file = new File([fileBlob], 'my-document.txt', { type: 'text/plain' });

    const formData = new FormData();
    formData.append('file', file);

    const uploadUrl = 'http://localhost:5454/v1/files?format=text'; // Specify format
    try {
        const uploadResponse = await fetch(uploadUrl, {
            method: 'POST',
            body: formData,
        });
        const uploadResult = await uploadResponse.json();
        console.log('File Uploaded:', uploadResult);

        // Assuming the API returns a 'path' or similar identifier for retrieval
        const filePath = uploadResult.path || 'my-document.txt'; // Adjust based on actual API response structure

        const retrieveUrl = `http://localhost:5454/v1/file/${filePath}`;
        const retrieveResponse = await fetch(retrieveUrl);
        const retrieveResult = await retrieveResponse.json();
        console.log('File Retrieved:', retrieveResult);

    } catch (error) {
        console.error('Error during file operations:', error);
    }
}

// uploadAndRetrieveFile();
</code></pre>
    </div>
</section>

<section id="audio-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Audio API: Speech-to-Text and Text-to-Speech for AI (OpenAI API Extension)</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase extends the **OpenAI Audio API**, offering powerful speech-to-text (transcriptions) and text-to-speech (speech generation) capabilities. This allows your AI applications to seamlessly interact with audio data, transcribe spoken language, or generate natural-sounding speech from text, enhancing user experiences and enabling new voice-driven features.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoints:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>POST /v1/audio/speech</code>: Generate audio from input text.</li>
        <li><code>POST /v1/audio/transcriptions</code>: Create a transcription of an audio file.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Generating Speech from Text</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase';

const client = new QuipuBase('http://localhost:5454');

async function generateSpeech() {
    try {
        const speechParams = {
            model: "tts-1", // Example model, check Quipubase documentation for supported models
            input: "Hello, this is Quipubase's text-to-speech in action.",
            voice: "alloy" // Example voice, check documentation for available options
        };
        // This will typically return an audio stream or a URL to the audio file
        const response = await client.audioSpeech(speechParams);
        console.log('Speech generation response:', response);
        // In a browser, you might play the audio:
        // const audioBlob = await response.blob();
        // const audioUrl = URL.createObjectURL(audioBlob);
        // const audio = new Audio(audioUrl);
        // audio.play();
    } catch (error) {
        console.error("Error generating speech:", error);
    }
}

async function transcribeAudio() {
    // This example assumes you have an audio file (e.g., from an input element)
    // For a real application, you'd get the file from user input or a server endpoint.
    const audioBlob = new Blob(['example audio data'], { type: 'audio/wav' }); // Placeholder
    const audioFile = new File([audioBlob], 'my-audio.wav', { type: 'audio/wav' });

    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('model', 'whisper-large-v3'); // Or 'whisper-large-v3-turbo'

    try {
        const response = await fetch('http://localhost:5454/v1/audio/transcriptions', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        console.log('Audio Transcription:', result.text);
    } catch (error) {
        console.error('Error transcribing audio:', error);
    }
}

// generateSpeech();
// transcribeAudio();
</code></pre>
    </div>
</section>

<section id="models-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Models API: Discover Available AI Models</h2>
    <p class="text-lg text-gray-600 mb-6">
        The Models API allows you to programmatically discover the various AI models available through Quipubase, including those used for chat completions, embeddings, and other generative tasks. This ensures your application can adapt to and utilize the best models for its needs.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoints:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>GET /v1/models</code>: List all available AI models.</li>
        <li><code>GET /v1/models/{model}</code>: Retrieve details for a specific AI model.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Listing Available Models</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase';

const client = new QuipuBase('http://localhost:5454');

async function listModels() {
    try {
        const models = await client.listModels();
        console.log('Available Models:', models);

        // Get details for a specific model
        const specificModel = await client.getModel('gemini-2.5-pro-preview-06-05');
        console.log('Details for gemini-2.5-pro-preview-06-05:', specificModel);
    } catch (error) {
        console.error("Error fetching models:", error);
    }
}

// listModels();
</code></pre>
    </div>
</section>

<section id="images-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Images API: Generative AI for Visual Content (OpenAI API Extension)</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase extends the **OpenAI Image Generation API**, empowering your applications to create visual content programmatically. This allows you to integrate dynamic image creation directly into your AI workflows, from generating custom avatars to creating unique visual assets based on prompts.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoint:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>POST /v1/images/generations</code>: Generate images based on a text prompt.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Generating an Image</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { QuipuBase } from 'quipubase';

const client = new QuipuBase('http://localhost:5454');

async function generateImage() {
    try {
        const imageParams = {
            prompt: "a futuristic city at sunset, highly detailed, cyberpunk style",
            n: 1, // Number of images to generate
            size: "1024x1024", // Desired image size
            response_format: "b64_json" // or "url" if supported
        };
        const response = await client.imageGenerations(imageParams);
        console.log('Generated Image Response:', response);
        // If response_format is "b64_json", you'd get base64 encoded image data
        // If response_format is "url", you'd get an image URL
        // Example for displaying base64 in browser:
        // if (response.data && response.data[0] && response.data[0].b64_json) {
        //     const img = document.createElement('img');
        //     img.src = `data:image/png;base64,${response.data[0].b64_json}`;
        //     document.body.appendChild(img);
        // }
    } catch (error) {
        console.error("Error generating image:", error);
    }
}

// generateImage();
</code></pre>
    </div>
</section>

<section id="auth-api" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Auth API: Secure Integration with OAuth Providers</h2>
    <p class="text-lg text-gray-600 mb-6">
        The Auth API in Quipubase simplifies integration with external OAuth providers, such as GitHub and Google. This allows you to implement secure authentication flows for your users, ensuring controlled access to your Quipubase-powered applications and data.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Key Endpoint:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><code>GET /v1/auth/{provider}</code>: Initiate or complete an OAuth authentication flow for a specified provider (e.g., `github`, `google`).</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Example: Initiating GitHub OAuth</h3>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// In your frontend, to initiate GitHub login:
function initiateGitHubLogin() {
    // Redirect user to Quipubase's auth endpoint
    window.location.href = 'http://localhost:5454/v1/auth/github';
}

// After successful authentication, Quipubase will redirect back to your app
// with a 'code' query parameter. You would then handle that code.
// Example:
// const urlParams = new URLSearchParams(window.location.search);
// const code = urlParams.get('code');
// if (code) {
//     console.log('Received OAuth code:', code);
//     // You might send this code to your own backend or directly to Quipubase
//     // depending on your authentication flow.
// }

// initiateGitHubLogin();
</code></pre>
    </div>
</section>


<section id="realtime" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Real-time Updates: The Heart of Quipubase</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase delivers real-time data synchronization through a powerful **WebSocket-based Pub/Sub (Publish/Subscribe)** mechanism. This means any changes to your documents are immediately broadcast to all subscribed clients, keeping your frontend always up-to-date without constant polling.
    </p>
    <p class="text-lg text-gray-600 mb-6">
        The `publishEvent` method allows you to push `create`, `update`, or `delete` events for a specific document within a collection. On the client side, the `subscribe` method sets up a listener that receives these events as they happen.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">How it Works:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><strong>Publishers:</strong> Your application (or other services) publishes events to a specific collection, indicating changes to a document (creation, modification, deletion).</li>
        <li><strong>Subscribers:</strong> Frontend clients (like your Vue or React app) subscribe to a collection. When an event is published, the client instantly receives it.</li>
        <li><strong>Event Data:</strong> Each event contains the `event` type (`create`, `update`, `delete`) and the `data` (the document itself or just its ID for deletions).</li>
    </ul>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// Publishing an update
await client.publishEvent(collection.id, {
    event: 'update',
    data: updatedTodo.modelDump()
});

// Subscribing to events
const unsubscribe = await client.subscribe(collectionId, (event) => {
    console.log('Real-time event received:', event);
    // Update UI based on event.event and event.data
});

// Don't forget to unsubscribe when component unmounts
// unsubscribe();</code></pre>
    </div>
</section>

<section id="schema-validation" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">JSON Schema & Validation: Structured Data, Happy Devs</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase leverages **JSON Schema** for defining the structure and validation rules for your documents. This ensures data consistency and integrity, preventing malformed data from entering your database. We've integrated with <code class="bg-gray-700 rounded px-1">Zod</code>, a TypeScript-first schema declaration and validation library, making schema definition intuitive and type-safe.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Benefits:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><strong>Data Integrity:</strong> Guarantees that all documents conform to a predefined structure.</li>
        <li><strong>Type Safety:</strong> With Zod, you get compile-time type safety for your data models in TypeScript projects.</li>
        <li><strong>Automatic Validation:</strong> Data is automatically validated against its schema when you attempt to create or update documents.</li>
        <li><strong>Clear Documentation:</strong> Your schemas serve as living documentation for your data structure.</li>
    </ul>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>import { z } from 'zod';
import { BaseModel } from 'quipubase';

class UserProfile extends BaseModel {
    name!: string;
    email!: string;
    age?: number;
    isActive!: boolean;

    static schema() {
        return z.object({
            id: z.string().optional(),
            name: z.string().min(3, 'Name must be at least 3 characters'),
            email: z.string().email('Invalid email address'),
            age: z.number().int().positive().optional(),
            isActive: z.boolean().default(true)
        });
    }
}

// When you create a collection, Quipubase uses this schema
// const usersCollection = await client.createCollection(UserProfile);

// Any data you try to publish will be validated against this schema
// await client.publishEvent(usersCollection.id, {
//     event: 'create',
//     data: new UserProfile({ name: 'Jane Doe', email: 'jane@example.com' }).modelDump()
// });</code></pre>
    </div>
</section>

<section id="document-processing" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">Document Processing: Beyond Simple Text</h2>
    <p class="text-lg text-gray-600 mb-6">
        Quipubase simplifies the ingestion and management of various document types. Whether it's PDFs, Word documents, HTML files, or plain text, Quipubase provides tools to process these into a format suitable for storage and retrieval, including for AI-driven applications.
    </p>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">Capabilities:</h3>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><strong>File Upload & Storage:</strong> Securely upload and manage files.</li>
        <li><strong>Automated Chunking:</strong> Large documents can be automatically broken down into smaller, more manageable chunks, which is essential for vector embeddings and contextual understanding by AI models.</li>
        <li><strong>Format Conversion:</strong> Process different file formats (e.g., HTML, text) into a unified representation.</li>
        <li><strong>Retrieval by Path:</strong> Easily retrieve documents or their processed chunks using a simple file path.</li>
    </ul>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// Example: Upload and chunk an HTML file
const file = new File(["&lt;h1&gt;Hello World&lt;/h1&gt;&lt;p&gt;This is a test paragraph.&lt;/p&gt;"], "example.html", { type: "text/html" });

const formData = new FormData();
formData.append('file', file);

// Assuming a client method for file upload, or a direct fetch to the API endpoint
// This demonstrates the concept based on the API schema
const uploadResponse = await fetch('http://localhost:5454/v1/files?format=html', {
    method: 'POST',
    body: formData,
});
const result = await uploadResponse.json();
console.log('Uploaded and chunked file:', result); // result contains chunks and metadata

// Example: Retrieve a file by path
// const retrievedFile = await client.getFile('/path/to/your/document.pdf');
// console.log('Retrieved file:', retrievedFile);</code></pre>
    </div>
</section>

<section id="file-chunking" class="section">
    <h2 class="text-3xl font-bold text-gray-900 mb-6">File Chunking: Optimizing for AI Context</h2>
    <p class="text-lg text-gray-600 mb-6">
        For effective AI processing, especially with Large Language Models (LLMs) and vector search, it's often necessary to break down large documents into smaller, coherent segments known as **chunks**. Quipubase offers built-in capabilities to automatically chunk files, optimizing them for contextual understanding and efficient retrieval.
    </p>
    <p class="text-lg text-gray-600 mb-6">
        This process is critical for:
    </p>
    <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
        <li><strong>Context Window Management:</strong> Ensuring that document segments fit within the token limits of AI models.</li>
        <li><strong>Improved Relevance:</strong> Allows AI models to focus on specific, relevant parts of a document during retrieval.</li>
        <li><strong>Efficient Embedding:</strong> Smaller chunks can be embedded more effectively, leading to more precise vector representations.</li>
    </ul>
    <h3 class="text-xl font-semibold text-gray-800 mb-3">How Quipubase Chunks:</h3>
    <p class="text-gray-600 mb-3">
        When you upload a document via the `/v1/files` endpoint, you can specify the desired `format` (e.g., `html`, `text`). Quipubase intelligently processes the content, segments it, and provides you with an array of text chunks, along with metadata like the original creation timestamp and the count of generated chunks. These chunks can then be directly used for embedding and vector search operations.
    </p>
    <div class="code-block">
        <button class="copy-btn">Copy</button>
        <pre class="p-4 text-sm text-gray-300 overflow-x-auto"><code>// The API response for a chunked file looks like this:
{
    "chunks": [
        "This is the first chunk of text.",
        "This is the second chunk of text.",
        "And this is the final chunk."
    ],
    "created": 1678886400, // Unix timestamp
    "chunkedCount": 3
}

// You can then take these chunks and embed them for vector search
// For example:
// const chunksToEmbed = result.chunks;
// await client.embedText({
//     input: chunksToEmbed,
//     model: "deep-pulse"
// }, "document-chunks-namespace");</code></pre>
    </div>
</section>

            </main>
        </div>
    </div>

    <footer class="bg-gray-800 text-white py-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-400">
            <p>&copy; 2023 Quipubase. All rights reserved.</p>
            <div class="flex justify-center space-x-4 mt-4">
                <a href="https://github.com/bahamondeX/quipubase-client-typescript" target="_blank" class="hover:text-white transition-colors duration-200">GitHub</a>
                <a href="#" class="hover:text-white transition-colors duration-200">Privacy Policy</a>
                <a href="#" class="hover:text-white transition-colors duration-200">Terms of Service</a>
            </div>
        </div>
    </footer>

    <script>
        // JavaScript for sidebar navigation
        document.addEventListener('DOMContentLoaded', () => {
            const navItems = document.querySelectorAll('.nav-item');
            const sections = document.querySelectorAll('.section');

            const showSection = (sectionId) => {
                sections.forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById(sectionId).classList.add('active');

                navItems.forEach(item => {
                    item.classList.remove('active');
                    if (item.getAttribute('data-section') === sectionId) {
                        item.classList.add('active');
                    }
                });
            };

            // Set initial active section from URL hash or default to 'overview'
            const initialSection = window.location.hash ? window.location.hash.substring(1) : 'overview';
            showSection(initialSection);

            navItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const sectionId = item.getAttribute('data-section');
                    history.pushState(null, '', `#${sectionId}`); // Update URL hash
                    showSection(sectionId);
                });
            });

            // Handle browser back/forward buttons
            window.addEventListener('hashchange', () => {
                const sectionId = window.location.hash ? window.location.hash.substring(1) : 'overview';
                showSection(sectionId);
            });

            // JavaScript for copy to clipboard
            document.querySelectorAll('.copy-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const codeBlock = button.nextElementSibling; // Assuming pre is the next sibling
                    const textToCopy = codeBlock.textContent;

                    // Use a temporary textarea to copy to clipboard
                    const textarea = document.createElement('textarea');
                    textarea.value = textToCopy;
                    textarea.style.position = 'fixed'; // Prevent scrolling to bottom of page
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
                    try {
                        const successful = document.execCommand('copy');
                        const msg = successful ? 'Copied!' : 'Failed to copy.';
                        button.textContent = msg; // Temporarily change button text
                        setTimeout(() => {
                            button.textContent = 'Copy';
                        }, 2000); // Reset text after 2 seconds
                    } catch (err) {
                        console.error('Failed to copy text: ', err);
                        button.textContent = 'Error!';
                        setTimeout(() => {
                            button.textContent = 'Copy';
                        }, 2000);
                    } finally {
                        document.body.removeChild(textarea);
                    }
                });
            });
        });
    </script>
</body>

</html>
"""
db = Prisma(auto_register=True)


def setup(func: tp.Callable[P, FastAPI]):
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> FastAPI:
        app = func(*args, **kwargs)
        static = StaticFiles(directory="static", html=True)
        app.mount("/static", static)

        @app.get("/", include_in_schema=False)
        def _():
            return HTMLResponse(LANDING_PAGE)

        @app.on_event("startup")
        async def _():
            await db.connect()
            logger.info(f"Connected to Database at {os.environ['DATABASE_URL']}")

        @app.on_event("shutdown")
        async def _():
            await db.disconnect()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

    return wrapper

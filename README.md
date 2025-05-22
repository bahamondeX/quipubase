<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quipubase Interactive API Documentation</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Visualization & Content Choices: 
        - Report Info: Quipubase general description. Goal: Introduce Quipubase. Viz/Presentation: Formatted text block. Interaction: Read. Justification: Standard intro. Library/Method: HTML/Tailwind.
        - Report Info: SDK Setup code. Goal: Show how to install/init. Viz/Presentation: Styled code block. Interaction: Read, Copy. Justification: Essential for developers. Library/Method: HTML <pre><code>, JS for copy.
        - Report Info: Each SDK function (e.g., listCollections, createCollection). Goal: Explain function and show usage. Viz/Presentation: Description text + styled code block for the example. Interaction: Read, Copy. Justification: Core of API docs. Library/Method: HTML/Tailwind, <pre><code>, JS for copy.
        - Report Info: Navigation elements. Goal: Allow users to switch between sections. Viz/Presentation: Clickable list items in a sidebar. Interaction: Click to show/hide content sections. Justification: Standard SPA navigation. Library/Method: HTML/Tailwind, JS for click handling and content visibility.
    -->
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f9fafb; /* bg-gray-50 */
            color: #334155; /* text-slate-700 */
        }
        .content-section {
            display: none;
        }
        .content-section.active {
            display: block;
        }
        .code-block {
            background-color: #1e293b; /* bg-slate-800 */
            color: #e2e8f0; /* text-slate-200 */
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            position: relative;
        }
        .copy-button {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background-color: #38bdf8; /* bg-sky-500 */
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .copy-button:hover {
            background-color: #0ea5e9; /* bg-sky-600 */
        }
        .nav-link {
            display: block;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            transition: background-color 0.2s, color 0.2s;
            cursor: pointer;
        }
        .nav-link:hover {
            background-color: #e0f2fe; /* sky-100 */
            color: #0284c7; /* sky-600 */
        }
        .nav-link.active {
            background-color: #0ea5e9; /* sky-600 */
            color: white;
            font-weight: 600;
        }
        h1, h2, h3 {
            color: #0f172a; /* text-slate-900 */
        }
        .prose {
            max-width: none;
        }
        .prose p {
            margin-bottom: 1em;
            line-height: 1.75;
        }
        .prose strong {
            color: #1e293b; /* text-slate-800 */
        }
        .prose code { /* Inline code */
            background-color: #e2e8f0; /* slate-200 */
            color: #0ea5e9; /* sky-600 */
            padding: 0.125rem 0.25rem;
            border-radius: 0.25rem;
            font-size: 0.9em;
        }
        /* Custom scrollbar for webkit browsers */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #e2e8f0; /* slate-200 */
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #94a3b8; /* slate-400 */
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #64748b; /* slate-500 */
        }
    </style>
</head>
<body class="flex h-screen overflow-hidden">

    <aside id="sidebar" class="w-64 bg-white p-6 space-y-4 border-r border-slate-200 overflow-y-auto transition-transform duration-300 ease-in-out transform -translate-x-full sm:translate-x-0 fixed sm:static h-full z-20">
        <h1 class="text-2xl font-bold text-sky-600">Quipubase Docs</h1>
        <nav>
            <a class="nav-link active" data-target="overview">✨ Overview</a>
            <a class="nav-link" data-target="setup">🚀 Setup</a>
            <a class="nav-link" data-target="collections">📦 Collections</a>
            <a class="nav-link" data-target="events">⚡ Real-time Events</a>
            <a class="nav-link" data-target="vector-store">🧠 Vector Store</a>
            <a class="nav-link" data-target="auth">🔐 Authentication</a>
            <a class="nav-link" data-target="file-processing">📄 File Processing</a>
        </nav>
    </aside>

    <button id="menuButton" class="sm:hidden fixed top-4 left-4 z-30 p-2 bg-sky-600 text-white rounded-md">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7" />
        </svg>
    </button>

    <main class="flex-1 p-6 sm:p-10 overflow-y-auto">
        <div class="max-w-4xl mx-auto prose">

            <section id="overview" class="content-section active">
                <h2 class="text-3xl font-semibold mb-6">Quipubase: Your Go-To Real-time Database for Awesome AI Apps! ✨</h2>
                <p>Hey there! So, <strong>Quipubase</strong>? It's not just <em>any</em> database. It's the <strong>super-powered backbone</strong> your <em>AI apps</em> have been dreaming of! Built on the rock-solid <code>RocksDB</code>, Quipubase is all about giving you top-notch performance and tons of flexibility. We've built it from the ground up to really boost your intelligent systems with data that moves as fast as you do.</p>
                <p>This interactive guide will walk you through its core features and how to use the TypeScript SDK to build amazing things!</p>
            </section>

            <section id="setup" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Ready to Dive In? Let's Get Started with the Quipubase TypeScript SDK! 🚀</h2>
                <p>First things first, let's hook you up with our cool Quipubase TypeScript SDK. You'll just need to set up your data models using <code>zod</code> and then extend our <code>BaseModel</code>. Easy peasy!</p>
                <h3 class="text-xl font-semibold mt-6 mb-3">1. Define Your Models</h3>
                <p>Create a file, for example <code>src/models.ts</code>:</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// src/models.ts
import { z } from "zod";
import { BaseModel } from "./quipubase-sdk"; // Assuming your SDK is in quipubase-sdk.ts

export class Task extends BaseModel {
    title!: string;
    description?: string;
    done!: boolean;

    static schema() {
        return z.object({
            id: z.string().optional(), // ID is optional for creation, assigned by Quipubase
            title: z.string().min(1, "Title cannot be empty"),
            description: z.string().optional(),
            done: z.boolean().default(false),
        });
    }
}</code></pre>
                </div>
                <h3 class="text-xl font-semibold mt-6 mb-3">2. Initialize the Client</h3>
                <p>In your main application file (e.g., <code>src/index.ts</code>):</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// src/index.ts or your main application file
import { QuipuBase } from "./quipubase-sdk";
import { Task } from "./models";

// Time to get our Quipubase client ready!
const quipu = new QuipuBase&lt;Task&gt;("http://localhost:5454"); // Pop in your Quipubase instance URL here!</code></pre>
                </div>
                 <p class="mt-4 bg-sky-100 border-l-4 border-sky-500 text-sky-700 p-4 rounded-md">
                    <strong>Heads up!</strong> Make sure you have the Quipubase SDK file (<code>quipubase-sdk.ts</code> or similar) in your project, containing the <code>BaseModel</code> and <code>QuipuBase</code> class definitions you provided.
                </p>
            </section>

            <section id="collections" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Dynamic Collections Management: Your Data, Your Rules, All in Real-time. 🚀</h2>
                <p>Quipubase makes handling your data a total breeze. Just define your models with <code>zod</code>, and Quipubase takes care of the rest. You get a super flexible, schema-driven way to manage your data!</p>

                <h3 class="text-xl font-semibold mt-6 mb-3">List Collections</h3>
                <p>Want to see all your data at a glance? Just list 'em! Get a quick overview of all your dynamic collections.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's see all our collections!
async function listAllCollections() {
    try {
        const collections = await quipu.listCollections();
        console.log("Here are all your Collections:", collections);
    } catch (error) {
        console.error("Oops! Couldn't list collections:", error);
    }
}
listAllCollections();</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Create Collection</h3>
                <p>Forget about strict, old-school schemas! You can whip up new collections on the fly using <code>jsonschema</code> (it's automatically made from your <code>zod</code> schema!). This lets your data models change right along with your AI. Talk about agile data modeling!</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's make a new 'tasks' collection using our Task model!
async function createTasksCollection() {
    try {
        const newCollection = await quipu.createCollection(Task);
        console.log("Awesome! New 'tasks' collection created:", newCollection);
    } catch (error) {
        console.error("Darn! Failed to create collection:", error);
    }
}
createTasksCollection();</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Get Collection</h3>
                <p>Need to dig into a specific collection? Just give us the ID! You'll get all the juicy details in a flash.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Grab the details for a specific collection
async function getCollectionDetails(collectionId: string) {
    try {
        const collectionDetails = await quipu.getCollection(collectionId);
        console.log(\`Here are the details for collection '\${collectionId}':\`, collectionDetails);
    } catch (error) {
        console.error(\`Uh oh! Couldn't get collection \${collectionId}:\`, error);
    }
}
// Try it out with one of your collection IDs from Quipubase!
// getCollectionDetails("your-collection-id");</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Delete Collection</h3>
                <p>Time for a clean-up? Easily remove entire collections and their data when you don't need them anymore.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's delete a collection!
async function deleteMyCollection(collectionId: string) {
    try {
        const result = await quipu.deleteCollection(collectionId);
        if (result.code === 200) { // Assuming 200 is success, adjust if API returns different
            console.log(\`Poof! Collection '\${collectionId}' deleted successfully!\`);
        } else {
            console.warn(\`Hmm, couldn't delete collection '\${collectionId}':\`, result);
        }
    } catch (error) {
        console.error(\`Error deleting collection \${collectionId}:\`, error);
    }
}
// Give it a whirl with one of your collection IDs from Quipubase!
// deleteMyCollection("your-collection-id");</code></pre>
                </div>
            </section>

            <section id="events" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Real-time Events (Pub/Sub): Your AI's Instant Messenger! ⚡</h2>
                <p>Quipubase's built-in Pub/Sub system means your apps can react <em>instantly</em> to data changes. This powers truly dynamic and super responsive AI experiences!</p>

                <h3 class="text-xl font-semibold mt-6 mb-3">Publish Event</h3>
                <p>Want your apps to know what's up right away? Just send out document-level events to your collections. This kicks off immediate reactions and dynamic workflows!</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Send out a 'create' event for a brand new Task document!
async function publishNewTask(collectionId: string) {
    const newTask = new Task({ title: "Learn Quipubase SDK", done: false });
    try {
        const publishedTask = await quipu.publishEvent(collectionId, {
            event: "create",
            data: newTask.toDict(), // Send the plain object
        });
        console.log("New task sent out:", publishedTask);
    } catch (error) {
        console.error("Whoops! Failed to publish event:", error);
    }
}
// Give it a shot with one of your collection IDs!
// publishNewTask("your-collection-id");</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Subscribe to Events</h3>
                <p>Stay totally in the loop! Listen in on all the live action in your data. Your apps can react instantly as changes happen. This is how you build truly reactive AI!</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's subscribe to events for a specific collection!
async function subscribeToTaskEvents(collectionId: string) {
    console.log(\`Getting ready to listen for events on collection '\${collectionId}'...\`);
    const unsubscribe = await quipu.subscribeToEvents(collectionId, (event) => {
        console.log(\`Got an event: \${event.event}\`, event.data);
        // This is where your AI app can do its real-time magic!
        if (event.event === "create" && event.data) {
            // Assuming event.data is an object or array of objects matching Task structure
            if (Array.isArray(event.data)) {
                 event.data.forEach(itemData => {
                    const createdTask = new Task(itemData as Partial&lt;Task&gt;);
                    console.log("Yay! New Task created (from array):", createdTask);
                 });
            } else {
                 const createdTask = new Task(event.data as Partial&lt;Task&gt;);
                 console.log("Yay! New Task created:", createdTask);
            }
        }
    });

    // To stop listening after a bit (say, 30 seconds)
    // setTimeout(() => {
    //     unsubscribe();
    //     console.log("Alright, stopped listening for events.");
    // }, 30000);
}
// Try it out with one of your collection IDs!
// subscribeToTaskEvents("your-collection-id");</code></pre>
                </div>
            </section>

            <section id="vector-store" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Vector Store & Cutting-Edge Similarity Search: Smart Data Finding! 🧠🔍</h2>
                <p>Quipubase's built-in vector similarity search helps your AI <em>understand</em> what your data means, not just what words are in it. This means super smart information retrieval!</p>

                <h3 class="text-xl font-semibold mt-6 mb-3">Upsert Texts (Vectors)</h3>
                <p>Easily turn your plain text into powerful vector embeddings. Store them in Quipubase's special vector store, getting your data all ready for smart searching.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's get some documents into our vector namespace!
async function upsertDocuments() {
    const textsToEmbed = [
        "The quick brown fox jumps over the lazy dog.",
        "A dog barks loudly at the cat.",
        "Cats are known for their agility and grace.",
        "Foxes are clever and cunning animals."
    ];
    const upsertPayload = {
        // Note: SDK shows 'texts', API spec shows 'content'. Assuming 'content' based on API. Adjust if SDK is different.
        content: textsToEmbed, 
        model: "poly-sage", // Pick your favorite embedding model: "poly-sage", "deep-pulse", or "mini-scope"!
        namespace: "my-documents"
    };
    try {
        // Using upsertVectors method as per SDK, but payload field name discrepancy noted.
        const response = await quipu.upsertVectors({
            texts: textsToEmbed, // Using 'texts' as per SDK UpsertText type
            model: "poly-sage",
            namespace: "my-documents"
        });
        console.log("Documents are in and ready:", response);
    } catch (error) {
        console.error("Oh no! Couldn't upsert documents:", error);
    }
}
upsertDocuments();</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Query Vector Store</h3>
                <p>Unlock true semantic search! Find texts that are <em>conceptually</em> similar, not just matching keywords. Our advanced vector embeddings give you super precise, intelligent results.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's find some similar documents!
async function querySimilarDocuments() {
    const queryText = "animals playing"; // SDK QueryText expects 'query: string', not array.
    const queryPayload = {
        query: queryText, 
        model: "poly-sage",
        namespace: "my-documents",
        top_k: 2 // We want the top 2 closest matches!
    };
    try {
        const response = await quipu.queryVectors(queryPayload);
        console.log("Found these similar documents:", response.matches);
    } catch (error) {
        console.error("Bummer! Couldn't query similar documents:", error);
    }
}
querySimilarDocuments();</code></pre>
                </div>

                <h3 class="text-xl font-semibold mt-6 mb-3">Delete Embeddings</h3>
                <p>Keep your data tidy! Easily remove specific embeddings from your vector store to keep things optimized.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Time to delete some embeddings by ID!
async function deleteSpecificEmbeddings(idsToDelete: string[]) {
    const deletePayload = {
        namespace: "my-documents",
        ids: idsToDelete
    };
    try {
        const response = await quipu.deleteVectors(deletePayload);
        console.log("Embeddings deleted:", response);
    } catch (error) {
        console.error("Couldn't delete embeddings:", error);
    }
}
// Use actual embedding IDs from your upsert response here!
// deleteSpecificEmbeddings(["embedding-id-1", "embedding-id-2"]);</code></pre>
                </div>
                
                <h3 class="text-xl font-semibold mt-6 mb-3">Embed Text</h3>
                <p>Need a vector for some text right now? No problem! Generate high-quality vector embeddings for any text, ready for your AI models to use instantly.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Let's get some embeddings for our text!
async function getEmbeddingsForText() {
    const embedPayload = {
        content: ["This is a sentence to embed.", "Another sentence for embedding."],
        model: "poly-sage"
    };
    try {
        const response = await quipu.embed(embedPayload);
        console.log("Here are your generated embeddings:", response.data);
    } catch (error) {
        console.error("Failed to get embeddings:", error);
    }
}
getEmbeddingsForText();</code></pre>
                </div>
            </section>

            <section id="auth" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Seamless Authentication: Easy-Peasy Security! 🔐</h2>
                <p>Quipubase makes getting users authenticated a snap, so you can focus on building those amazing AI features!</p>
                <h3 class="text-xl font-semibold mt-6 mb-3">OAuth Integration</h3>
                <p>Give your users secure, super easy access. Quipubase plays nicely with popular OAuth providers like GitHub and Google. No fuss, just strong authentication!</p>
                <p class="mt-2">The SDK doesn't provide direct methods for initiating OAuth flows as this is typically handled by redirecting the user's browser. You would construct the URL as per the API specification.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Example: Directing the user to GitHub to log in (this usually happens in their browser)
// const quipubaseAuthUrl = "http://localhost:5454"; // Your Quipubase base URL
// window.location.href = \`\${quipubaseAuthUrl}/v1/auth/github\`;

console.log("To kick off GitHub OAuth, just head to: http://YOUR_QUIPUBASE_URL/v1/auth/github in your browser!");
console.log("Replace YOUR_QUIPUBASE_URL with your instance's address.");
</code></pre>
                </div>
            </section>

            <section id="file-processing" class="content-section">
                <h2 class="text-3xl font-semibold mb-6">Intelligent File Processing: From Messy Data to Smart Insights! 📄➡️💡</h2>
                <p>Turn all that raw, unstructured data into useful insights with Quipubase's file processing powers!</p>
                <h3 class="text-xl font-semibold mt-6 mb-3">Process File</h3>
                <p>Upload and smartly break down files (HTML or plain text) right inside Quipubase. This gets them all ready for advanced stuff like embedding and analysis.</p>
                <div class="code-block">
                    <button class="copy-button">Copy</button>
                    <pre><code>// Upload and process a text file (this is a conceptual example for browsers or Node.js)
async function processMyFile(file: File) { // 'file' would come from an input element, like a file upload
    try {
        const response = await quipu.chunkFile(file, "text"); // Or "html" if it's an HTML file!
        console.log("File processed and all chunked up:", response.chunks);
    } catch (error) {
        console.error("Couldn't process the file:", error);
    }
}

// In a browser, you'd grab the File object from an &lt;input type="file"&gt; like this:
// const fileInput = document.getElementById('myFileInput') as HTMLInputElement;
// fileInput.addEventListener('change', (event) => {
//     const fileList = (event.target as HTMLInputElement).files;
//     if (fileList && fileList.length > 0) {
//         const file = fileList[0];
//         processMyFile(file);
//     }
// });
// For this to work, you'd need an input element in your HTML:
// &lt;input type="file" id="myFileInput" /&gt;</code></pre>
                </div>
                 <p class="mt-4 bg-amber-100 border-l-4 border-amber-500 text-amber-700 p-4 rounded-md">
                    <strong>Note:</strong> The <code>chunkFile</code> method in the provided SDK snippet takes <code>(file: File, format: "html" | "text")</code> and then attempts to build a URL like <code>this.buildUrl(\`/v1/file?format=\${format}\`)</code>. However, the API for file upload is a POST request and typically involves sending <code>FormData</code>. The SDK's <code>fetch</code> call for <code>chunkFile</code> is missing the <code>method: "POST"</code> and <code>body: formData</code>. The example above assumes the SDK method correctly handles this internally. If not, the SDK method would need adjustment.
                </p>
            </section>

            <footer class="mt-12 pt-8 border-t border-slate-200 text-center text-slate-500 text-sm">
                Quipubase isn't just a database; it's your <strong>best pal</strong> for building the next generation of smart, reactive AI systems. Get ready for super flexible data handling, lightning-fast real-time action, and amazing semantic search. It's all here, designed to take your AI apps to the next level! 🚀
            </footer>
        </div>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', function () {
            const navLinks = document.querySelectorAll('.nav-link');
            const contentSections = document.querySelectorAll('.content-section');
            const sidebar = document.getElementById('sidebar');
            const menuButton = document.getElementById('menuButton');

            function setActiveSection(targetId) {
                navLinks.forEach(link => {
                    link.classList.toggle('active', link.dataset.target === targetId);
                });
                contentSections.forEach(section => {
                    section.classList.toggle('active', section.id === targetId);
                });

                // Scroll to top of main content area on section change
                document.querySelector('main').scrollTop = 0;
            }

            navLinks.forEach(link => {
                link.addEventListener('click', function (e) {
                    e.preventDefault();
                    const targetId = this.dataset.target;
                    setActiveSection(targetId);
                    if (sidebar.classList.contains('translate-x-0')) {
                        sidebar.classList.remove('translate-x-0');
                        sidebar.classList.add('-translate-x-full');
                    }
                });
            });

            menuButton.addEventListener('click', function() {
                sidebar.classList.toggle('-translate-x-full');
                sidebar.classList.toggle('translate-x-0');
            });

            // Copy button functionality
            document.querySelectorAll('.copy-button').forEach(button => {
                button.addEventListener('click', function () {
                    const codeBlock = this.parentElement;
                    const pre = codeBlock.querySelector('pre');
                    if (pre) {
                        const code = pre.innerText;
                        navigator.clipboard.writeText(code).then(() => {
                            this.innerText = 'Copied!';
                            setTimeout(() => {
                                this.innerText = 'Copy';
                            }, 2000);
                        }).catch(err => {
                            console.error('Failed to copy: ', err);
                            this.innerText = 'Failed';
                             setTimeout(() => {
                                this.innerText = 'Copy';
                            }, 2000);
                        });
                    }
                });
            });

            // Set initial active section (overview)
            setActiveSection('overview');
        });
    </script>

</body>
</html>

import React, { useState } from "react";
import {
  Database,
  Server,
  Cpu,
  Zap,
  Code,
  GitBranch,
  ChevronRight,
  ExternalLink,
  Menu,
  X,
} from "lucide-react";

const QuipubaseWebsite = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900 sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Database className="h-8 w-8 text-teal-400" />
                  <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-orange-400 tracking-tight">
                    Quipubase
                  </span>
                </div>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-6">
                <a
                  href="#features"
                  className="hover:text-teal-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Features
                </a>
                <a
                  href="#api"
                  className="hover:text-teal-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  API
                </a>
                <a
                  href="#docs"
                  className="hover:text-teal-400 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Documentation
                </a>
                <a
                  href="#start"
                  className="bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600 px-4 py-2 rounded-md text-sm font-medium"
                >
                  Get Started
                </a>
              </div>
            </div>
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none"
              >
                {isMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <a
                href="#features"
                className="hover:bg-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              >
                Features
              </a>
              <a
                href="#api"
                className="hover:bg-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              >
                API
              </a>
              <a
                href="#docs"
                className="hover:bg-gray-700 block px-3 py-2 rounded-md text-base font-medium"
              >
                Documentation
              </a>
              <a
                href="#start"
                className="bg-gradient-to-r from-teal-500 to-orange-500 block px-3 py-2 rounded-md text-base font-medium"
              >
                Get Started
              </a>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="relative">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-24 flex flex-col md:flex-row items-center">
          <div className="md:w-1/2 mb-12 md:mb-0">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold mb-6">
              <span className="block">A real-time</span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-orange-400">
                document database
              </span>
              <span className="block">for AI-native apps</span>
            </h1>
            <p className="text-gray-300 text-lg mb-8 max-w-xl">
              Built on <code className="bg-gray-800 px-1 rounded">RocksDB</code>
              , Quipubase enables dynamic, schema-driven collections using{" "}
              <code className="bg-gray-800 px-1 rounded">jsonschema</code> for
              flexible document modeling.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="#start"
                className="bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600 px-6 py-3 rounded-lg text-center font-bold text-lg shadow-lg shadow-teal-900/20"
              >
                Get Started
              </a>
              <a
                href="#api"
                className="border border-gray-700 hover:border-teal-500 px-6 py-3 rounded-lg text-center font-bold text-lg shadow-lg"
              >
                View API
              </a>
            </div>
          </div>
          <div className="md:w-1/2 flex justify-center">
            <img
              src="/favicon.svg"
              alt="Quipubase"
              className="w-full max-w-md rounded-lg shadow-2xl"
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-800/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-orange-400 mb-4">
              Key Features
            </h2>
            <p className="text-gray-300 max-w-2xl mx-auto">
              Powerful capabilities designed specifically for modern AI-native
              applications
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-teal-500 to-teal-700 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">
                Schema-Driven Collections
              </h3>
              <p className="text-gray-300">
                Dynamic, flexible document modeling using JSONSchema for instant
                validation and structure.
              </p>
            </div>

            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-teal-500 to-orange-500 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <Server className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">
                Vector Similarity Search
              </h3>
              <p className="text-gray-300">
                Native support for vector embeddings and fast similarity search
                for AI-powered retrieval.
              </p>
            </div>

            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-orange-500 to-orange-700 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <Zap className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">Real-time Pub/Sub</h3>
              <p className="text-gray-300">
                Built-in architecture allowing real-time subscriptions to
                document-level events.
              </p>
            </div>

            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-orange-500 to-teal-500 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">RocksDB Foundation</h3>
              <p className="text-gray-300">
                Built on the battle-tested RocksDB for lightning-fast
                performance and reliability.
              </p>
            </div>

            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-teal-700 to-teal-500 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <Code className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">Simple API</h3>
              <p className="text-gray-300">
                Clean, RESTful API that makes complex database operations
                straightforward.
              </p>
            </div>

            <div className="bg-gray-900 p-6 rounded-lg shadow-lg border border-gray-800 hover:border-teal-500 transition-all">
              <div className="bg-gradient-to-br from-orange-700 to-orange-500 w-12 h-12 rounded-lg flex items-center justify-center mb-4 shadow-md">
                <GitBranch className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">Live, Reactive Systems</h3>
              <p className="text-gray-300">
                Perfect backend for building responsive, event-driven AI
                applications.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* API Section */}
      <section id="api" className="py-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-orange-400 mb-4">
              Simple API Design
            </h2>
            <p className="text-gray-300 max-w-2xl mx-auto">
              Interact with collections through a clean, RESTful API
            </p>
          </div>

          <div className="max-w-3xl mx-auto bg-gray-900 rounded-lg shadow-xl overflow-hidden border border-gray-800">
            <div className="flex bg-gray-800 px-4 py-3 border-b border-gray-700">
              <span className="bg-red-500 w-3 h-3 rounded-full mr-2"></span>
              <span className="bg-yellow-500 w-3 h-3 rounded-full mr-2"></span>
              <span className="bg-green-500 w-3 h-3 rounded-full"></span>
              <span className="ml-4 text-gray-400 font-mono text-sm">
                /v1/collections
              </span>
            </div>
            <div className="p-4 font-mono text-sm overflow-x-auto">
              <pre className="language-json">
                <code>{`// Create a new collection
POST /v1/collections
{
  "title": "Users",
  "description": "Collection of user profiles",
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "email": { "type": "string" },
    "age": { "type": "integer" },
    "embedding": { "type": "array", "items": { "type": "number" } }
  },
  "required": ["name", "email"]
}

// Query documents
POST /v1/events/{collection_id}
{
  "event": "query",
  "data": {
    "age": 21
  }
}

// Subscribe to real-time changes
GET /v1/events/Users
// Server-sent events stream for real-time updates`}</code>
              </pre>
            </div>
          </div>

          <div className="mt-12 text-center">
            <a
              href="https://quipubase.online/docs"
              className="inline-flex items-center text-teal-400 hover:text-teal-300"
            >
              View full API documentation
              <ChevronRight className="h-4 w-4 ml-1" />
            </a>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="start" className="py-20 bg-gray-800/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-6">
              Ready to build with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-orange-400">
                Quipubase
              </span>
              ?
            </h2>
            <p className="text-gray-300 mb-8">
              Get started with our comprehensive documentation and examples.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="#"
                className="bg-gradient-to-r from-teal-500 to-orange-500 hover:from-teal-600 hover:to-orange-600 px-8 py-4 rounded-lg text-center font-bold text-lg shadow-lg"
              >
                Get API Key
              </a>
              <a
                href="#"
                className="border border-gray-700 hover:border-teal-500 px-8 py-4 rounded-lg text-center font-bold text-lg"
              >
                View Documentation
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-gray-800 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Database className="h-6 w-6 text-teal-400" />
                <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-orange-400">
                  Quipubase
                </span>
              </div>
              <p className="text-gray-400 text-sm">
                A real-time document database designed for AI-native
                applications.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">Links</h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Documentation
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    API Reference
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Examples
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    GitHub
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">Community</h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Discord
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Twitter
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    YouTube
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Blog
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">Legal</h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 text-sm"
                  >
                    Cookie Policy
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-800 text-center">
            <p className="text-gray-500 text-sm">
              &copy; {new Date().getFullYear()} Quipubase. All rights reserved.
            </p>
            <p className="text-gray-500 text-sm mt-2">
              <a
                href="https://quipubase.online"
                className="hover:text-teal-400 inline-flex items-center"
              >
                quipubase.online
                <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default QuipubaseWebsite;

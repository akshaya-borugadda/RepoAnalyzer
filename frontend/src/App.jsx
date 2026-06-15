import React, { useState, useEffect, useRef } from 'react';
import { 
  Code, 
  Terminal, 
  Cpu, 
  Layers, 
  Activity, 
  FileCode, 
  Trash2, 
  Send, 
  HelpCircle, 
  CheckCircle, 
  Folder, 
  FolderOpen, 
  FileText, 
  Database,
  ArrowRight,
  AlertCircle,
  Copy,
  Check,
  MessageSquare,
  Server,
  Play,
  Layout,
  Network
} from 'lucide-react';
import mermaid from 'mermaid';

// API Base URL configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Initialize Mermaid for dark rendering
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    background: '#0d121f',
    primaryColor: '#1e293b',
    primaryTextColor: '#f8fafc',
    lineColor: '#475569',
    secondaryColor: '#334155',
    tertiaryColor: '#0f172a'
  }
});

// Rich Sample Analysis Dataset for Demo Mode
const MOCK_DATA = {
  repo_name: "ai-chatbot-hub",
  total_files: 45,
  total_folders: 12,
  project_type: "Full-Stack Python/React",
  health_score: 92,
  health_report: {
    structure: 95,
    documentation: 90,
    unused_code: 88,
    configuration: 95
  },
  summary: "A full-stack artificial intelligence conversational assistant workspace. Features a React-based frontend dashboard with a FastAPI and WebSocket-based backend service. It connects to PostgreSQL for user history storage, uses Celery with Redis for heavy background embeddings generation, and integrates with the Google Gemini API for context-aware responses.",
  tech_stack: ["React", "FastAPI", "PostgreSQL", "Redis", "Celery", "Docker", "TailwindCSS"],
  frameworks: ["Vite", "Pydantic", "SQLAlchemy", "Uvicorn"],
  databases: ["PostgreSQL", "Redis"],
  languages: {
    "Python": 18,
    "TypeScript (JSX)": 12,
    "JSON": 6,
    "Markdown": 4,
    "Docker": 2,
    "Other": 3
  },
  important_files: [
    {
      file_path: "backend/app/main.py",
      file_type: "Source",
      purpose: "FastAPI application entrypoint. Configures middlewares, mounts CORS, and registers API/WebSocket routing routers.",
      importance_score: 10
    },
    {
      file_path: "frontend/src/App.jsx",
      file_type: "Source",
      purpose: "Main React application layout. Configures state for the chat screen, handles WebSocket connection, and renders the layout.",
      importance_score: 9
    },
    {
      file_path: "backend/app/services/gemini_service.py",
      file_type: "Service",
      purpose: "Interacts with the Google Gemini model for prompt building, prompt injection, and response parsing.",
      importance_score: 9
    },
    {
      file_path: "docker-compose.yml",
      file_type: "Configuration",
      purpose: "Multi-container configuration. Orchestrates backend API, frontend web server, PostgreSQL database, and Redis broker services.",
      importance_score: 8
    },
    {
      file_path: "README.md",
      file_type: "Documentation",
      purpose: "Project overview, system architecture specifications, local setup steps, and environment config instructions.",
      importance_score: 8
    }
  ],
  dead_files: [
    {
      file_path: "frontend/src/components/OldChatWindow.jsx",
      reason: "This component is not imported anywhere in the source tree since it was replaced by the modern glassmorphic chat widget.",
      confidence: "High"
    },
    {
      file_path: "backend/app/utils/legacy_parser.py",
      reason: "Contains old text cleaning routines. The module has no imports in app code and has been superseded by the AST-based parser.",
      confidence: "High"
    }
  ],
  api_routes: [
    {
      method: "POST",
      path: "/api/v1/chat",
      file_path: "backend/app/api/endpoints/chat.py"
    },
    {
      method: "GET",
      path: "/api/v1/health",
      file_path: "backend/app/api/endpoints/system.py"
    },
    {
      method: "POST",
      path: "/api/v1/embed",
      file_path: "backend/app/api/endpoints/embeddings.py"
    }
  ],
  architecture_flowchart: "graph TD\n    User[User Browser] -->|HTTP/WebSockets| FE[React Frontend]\n    FE -->|REST API Requests| BE[FastAPI Backend]\n    BE -->|Queries/Updates| DB[(PostgreSQL Database)]\n    BE -->|Enqueues Tasks| Redis{Redis Message Broker}\n    Redis -->|Pulls Jobs| Workers[Celery Background Workers]\n    Workers -->|Calls API| LLM[Google Gemini API]\n    Workers -->|Saves Cache| Redis",
  tree: [
    {
      name: "backend",
      type: "directory",
      path: "backend",
      children: [
        {
          name: "app",
          type: "directory",
          path: "backend/app",
          children: [
            {
              name: "main.py",
              type: "file",
              path: "backend/app/main.py"
            },
            {
              name: "services",
              type: "directory",
              path: "backend/app/services",
              children: [
                {
                  name: "gemini_service.py",
                  type: "file",
                  path: "backend/app/services/gemini_service.py"
                }
              ]
            }
          ]
        },
        {
          name: "requirements.txt",
          type: "file",
          path: "backend/requirements.txt"
        }
      ]
    },
    {
      name: "frontend",
      type: "directory",
      path: "frontend",
      children: [
        {
          name: "src",
          type: "directory",
          path: "frontend/src",
          children: [
            {
              name: "App.jsx",
              type: "file",
              path: "frontend/src/App.jsx"
            }
          ]
        },
        {
          name: "package.json",
          type: "file",
          path: "frontend/package.json"
        }
      ]
    },
    {
      name: "docker-compose.yml",
      type: "file",
      path: "docker-compose.yml"
    },
    {
      name: "README.md",
      type: "file",
      path: "README.md"
    }
  ]
};

// Mermaid Flowchart Renderer
function MermaidRenderer({ chart }) {
  const containerRef = useRef(null);
  const [renderError, setRenderError] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (containerRef.current && chart) {
      setRenderError(false);
      containerRef.current.innerHTML = "";
      
      const uniqueId = `mermaid-${Math.floor(Math.random() * 100000)}`;
      
      try {
        mermaid.render(uniqueId, chart)
          .then(({ svg }) => {
            if (containerRef.current) {
              containerRef.current.innerHTML = svg;
            }
          })
          .catch((err) => {
            console.error("Mermaid Render Catch:", err);
            setRenderError(true);
          });
      } catch (err) {
        console.error("Mermaid Render Sync Catch:", err);
        setRenderError(true);
      }
    }
  }, [chart]);

  const copyRaw = () => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (renderError || !chart) {
    return (
      <div className="flowchart-container">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-yellow-500 font-semibold flex items-center gap-1">
            <AlertCircle size={14} /> Render fallback (raw syntax)
          </span>
          <button onClick={copyRaw} className="text-xs text-gray-400 hover:text-white flex items-center gap-1 bg-white/5 px-2 py-1 rounded">
            {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
            {copied ? "Copied" : "Copy Code"}
          </button>
        </div>
        <div className="flowchart-raw-box">
          {chart || "No diagram defined."}
        </div>
      </div>
    );
  }

  return (
    <div className="flowchart-container">
      <div className="flex justify-end mb-2">
        <button onClick={copyRaw} className="text-xs text-gray-400 hover:text-white flex items-center gap-1 bg-white/5 px-2 py-1 rounded">
          {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          {copied ? "Copy Syntax" : "Copy Syntax"}
        </button>
      </div>
      <div className="mermaid-wrapper overflow-auto p-4 bg-[#05070c] rounded-xl border border-white/5 flex justify-center">
        <div ref={containerRef} className="mermaid-graph w-full flex justify-center" />
      </div>
    </div>
  );
}

// Recursive File Tree Node
function FileTreeNode({ node, openFolders, toggleFolder }) {
  const isDirectory = node.type === 'directory' || (node.children !== undefined);
  const isOpen = openFolders[node.path];

  if (isDirectory) {
    return (
      <div className="tree-node">
        <div className="tree-node-row" onClick={() => toggleFolder(node.path)}>
          <span className="tree-icon folder">
            {isOpen ? <FolderOpen size={15} /> : <Folder size={15} />}
          </span>
          <span className="tree-label">{node.name}</span>
        </div>
        {isOpen && node.children && (
          <div className="tree-node-children">
            {node.children.map((child, idx) => (
              <FileTreeNode
                key={idx}
                node={child}
                openFolders={openFolders}
                toggleFolder={toggleFolder}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="tree-node-row file-node">
      <span className="tree-icon file">
        <FileText size={15} />
      </span>
      <span className="tree-label">{node.name}</span>
    </div>
  );
}

export default function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);
  
  // Chat States
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  
  // UI States
  const [activeTab, setActiveTab] = useState('important'); // 'important' | 'dead'
  const [openFolders, setOpenFolders] = useState({});
  const [showLanding, setShowLanding] = useState(true);
  
  const chatEndRef = useRef(null);

  const loadingSteps = [
    "Cloning repository from GitHub to local disk...",
    "Scanning project workspace files & folder metrics...",
    "Detecting technology stacks and framework files...",
    "Building import dependency architecture graph...",
    "Preparing AI context & loading Gemini assistant models..."
  ];

  // Auto-scroll chat window
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  // Ping backend on mount to check status
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/`);
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch (e) {
        setBackendOnline(false);
      }
    };
    checkBackend();
  }, []);

  // Handle loading steps interval
  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep(prev => {
          if (prev < loadingSteps.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 1800);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  // Handle repository analyze submission
  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setError('');
    setAnalysisData(null);
    setChatMessages([]);
    setIsDemoMode(false);
    setShowLanding(false);

    try {
      const res = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({ repo_url: repoUrl.trim() })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || `Analysis failed with status ${res.status}`);
      }

      const data = await res.json();
      setAnalysisData(data);
      
      // Auto-open top level folders in file tree
      const initialOpen = {};
      if (data.tree) {
        data.tree.forEach(node => {
          if (node.type === 'directory' || node.children) {
            initialOpen[node.path] = true;
          }
        });
      }
      setOpenFolders(initialOpen);

      // Add welcome chat message from the analyzer
      setChatMessages([
        {
          sender: 'bot',
          text: `Hello! I have completed analyzing **${data.repo_name || "the repository"}**.\n\nI can answer questions regarding database integrations, routes, health metrics, dead code, or explain specific files. Ask me anything!`,
          sources: []
        }
      ]);

    } catch (err) {
      console.error(err);
      setError(err.message || "An unexpected error occurred during repository analysis.");
      // Auto-suggest Demo mode if backend is dead
      if (!backendOnline) {
        setError("Backend server is currently offline. You can still explore all features by clicking 'View Sample Demo' below.");
      }
      setShowLanding(true);
    } finally {
      setLoading(false);
    }
  };

  // Load sample data for demo mode
  const loadSampleDemo = () => {
    setIsDemoMode(true);
    setShowLanding(false);
    setAnalysisData(MOCK_DATA);
    setError('');
    
    // Auto-open directory nodes
    const initialOpen = {};
    MOCK_DATA.tree.forEach(node => {
      if (node.type === 'directory' || node.children) {
        initialOpen[node.path] = true;
      }
    });
    setOpenFolders(initialOpen);

    setChatMessages([
      {
        sender: 'bot',
        text: "Welcome to the **ai-chatbot-hub** sample interactive workspace demo!\n\nI can answer questions about PostgreSQL connection details, FastAPI main router, Celery workers, or Docker configuration. Try asking a question like *'Which file connects to database?'*.",
        sources: []
      }
    ]);
  };

  // Handle chat message submission
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading || !analysisData) return;

    const userQuestion = chatInput.trim();
    setChatMessages(prev => [...prev, { sender: 'user', text: userQuestion, sources: [] }]);
    setChatInput('');
    setChatLoading(true);

    // Mock Demo Mode response
    if (isDemoMode) {
      setTimeout(() => {
        let answer = "In this sample codebase, the frontend uses React components to render the UI, and queries are dispatched to FastAPI routes under `backend/app/api/`. Gemini-1.5-flash is configured as the default generator to process model inferences.";
        let sources = [{ file_path: "backend/app/services/gemini_service.py", reason: "Configures Gemini model initialization" }];

        const qLower = userQuestion.toLowerCase();
        if (qLower.includes("database") || qLower.includes("connect") || qLower.includes("sql") || qLower.includes("postgres") || qLower.includes("db")) {
          answer = "In the `ai-chatbot-hub` repository, database connections are managed primarily by `backend/app/core/db.py` (which initializes SQLAlchemy) and references are mapped in `backend/app/models/` for database schemas.\n\nThe `docker-compose.yml` file is configured with Postgres parameters for environment configuration.";
          sources = [{ file_path: "docker-compose.yml", reason: "Configures PostgreSQL credentials and service initialization" }];
        } else if (qLower.includes("explain") || qLower.includes("what does") || qLower.includes("about") || qLower.includes("project") || qLower.includes("summary")) {
          answer = "This project represents a fully functional AI-powered Chatbot Hub. The backend uses FastAPI and SQLAlchemy to connect to database entities, while Celery manages long-running embedding vector calculations in background tasks. Gemini provides generative response loops.";
          sources = [{ file_path: "README.md", reason: "System architecture description" }];
        } else if (qLower.includes("dead") || qLower.includes("unused") || qLower.includes("orphaned")) {
          answer = "According to our structural scans, there are two likely unused modules: `frontend/src/components/OldChatWindow.jsx` (replaced by the glassmorphic widget) and `backend/app/utils/legacy_parser.py` (deprecated legacy helper). No imports refer to these files in active workspaces.";
          sources = [
            { file_path: "frontend/src/components/OldChatWindow.jsx", reason: "No active imports detected" },
            { file_path: "backend/app/utils/legacy_parser.py", reason: "Superseded by new AST-based parser" }
          ];
        }

        setChatMessages(prev => [...prev, {
          sender: 'bot',
          text: answer,
          sources: sources
        }]);
        setChatLoading(false);
      }, 1000);
      return;
    }

    // Active Backend endpoint integration
    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          repo_name: analysisData.repo_name,
          question: userQuestion
        })
      });

      if (!res.ok) {
        throw new Error(`Chat failed with status ${res.status}`);
      }

      const chatRes = await res.json();
      setChatMessages(prev => [...prev, {
        sender: 'bot',
        text: chatRes.answer || "I could not generate an answer.",
        sources: chatRes.sources || []
      }]);

    } catch (err) {
      console.error(err);
      setChatMessages(prev => [...prev, {
        sender: 'bot',
        text: `Error: ${err.message || "Unable to reach the assistant model right now."}`,
        sources: []
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const toggleFolder = (path) => {
    setOpenFolders(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  return (
    <div className="app-layout">
      {/* Workspace Panel (Left Side) */}
      <div className="workspace-panel">
        
        {/* Top Header */}
        <header className="header-bar">
          <div className="logo-group cursor-pointer" onClick={() => { setShowLanding(true); setAnalysisData(null); setError(''); }}>
            <Code className="logo-icon" size={28} />
            <h1 className="logo-text">RepoInsight</h1>
          </div>
          
          <div className="status-badges-container">
            {isDemoMode && (
              <div className="status-badge">
                <span className="status-indicator"></span>
                Demo Mode Active
              </div>
            )}
            <div className={`status-badge ${backendOnline ? '' : 'offline'}`}>
              <span className={`status-indicator ${backendOnline ? '' : 'offline'}`}></span>
              {backendOnline ? "Live Backend Online" : "Demo Mode Only (Backend Offline)"}
            </div>
          </div>
        </header>

        {/* 1. Landing Hero Layout */}
        {showLanding && !loading && (
          <div className="landing-container">
            <span className="hero-tagline">AI-Powered Repository Intelligence</span>
            <h2 className="hero-title">Map, Scan & Converse with any GitHub Repository</h2>
            <p className="hero-description">
              Paste a public GitHub repository URL and instantly understand its codebase layouts, tech stacks, important documentation files, possible dead files, API route registries, architecture flowcharts, and ask natural language questions.
            </p>

            <div className="landing-action-card">
              <h3 className="text-lg font-semibold mb-2">Analyze Repository</h3>
              <p className="text-xs text-gray-400 mb-4">Provide a public Git URL to run cloning tasks and trigger RAG indexing processes.</p>
              
              <div className="input-container">
                <input 
                  type="text" 
                  placeholder="e.g. https://github.com/Jedi3301/resumer" 
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="input-url"
                />
                <button 
                  onClick={handleAnalyze} 
                  disabled={!repoUrl.trim()} 
                  className="btn-primary"
                >
                  Analyze Repository
                  <ArrowRight size={18} />
                </button>
              </div>

              {!backendOnline && (
                <div className="landing-info-banner">
                  <AlertCircle size={16} />
                  <span>Backend is currently unavailable. You can still click the sample demo button below to view a workspace.</span>
                </div>
              )}

              <div className="landing-buttons-row">
                <button onClick={loadSampleDemo} className="btn-secondary">
                  <Play size={16} className="text-cyan-400" />
                  View Sample Demo
                </button>
              </div>
            </div>

            <div className="features-preview-grid">
              <div className="feature-preview-card">
                <Layout className="feature-preview-icon" size={20} />
                <h4 className="feature-preview-title">Visual Code Audits</h4>
                <p className="feature-preview-desc">Maps entry points and documentation while flagging orphaned, unimported code nodes.</p>
              </div>
              <div className="feature-preview-card">
                <Network className="feature-preview-icon" size={20} />
                <h4 className="feature-preview-title">Architecture Flows</h4>
                <p className="feature-preview-desc">Generates interactive Mermaid.js dependency maps modeling browser-to-database interfaces.</p>
              </div>
              <div className="feature-preview-card">
                <MessageSquare className="feature-preview-icon" size={20} />
                <h4 className="feature-preview-title">Interactive RAG Chat</h4>
                <p className="feature-preview-desc">Retrieves matched content chunks from index files to answer technical queries with citations.</p>
              </div>
            </div>
          </div>
        )}

        {/* 2. Loading State */}
        {loading && (
          <div className="loading-scanner-container">
            <div className="loader-spinner"></div>
            <h3 className="loading-title">Analyzing Repository Context</h3>
            
            <div className="loading-steps-list">
              {loadingSteps.map((step, idx) => {
                let status = "pending";
                if (idx < loadingStep) status = "completed";
                else if (idx === loadingStep) status = "active";

                return (
                  <div key={idx} className={`loading-step-item ${status}`}>
                    <div className="step-indicator-circle">
                      {status === "completed" && <Check size={10} />}
                    </div>
                    <span>{step}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. Error Alert Notice */}
        {error && !loading && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3 text-rose-300 text-sm mb-6 max-w-4xl mx-auto">
            <AlertCircle size={20} className="text-rose-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block mb-1">Service Error Encountered:</span>
              <p>{error}</p>
              <button onClick={loadSampleDemo} className="mt-3 text-xs bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition-colors">
                <Play size={12} /> Load Interactive Sample Demo
              </button>
            </div>
          </div>
        )}

        {/* 4. Active Dashboard Panels */}
        {analysisData && !loading && !showLanding && (
          <div>
            
            {/* Quick Summary Cards (Vite/React upgrade) */}
            <div className="summary-cards-row">
              <div className="summary-mini-card">
                <span className="summary-card-label">Repository Name</span>
                <span className="summary-card-val">{analysisData.repo_name}</span>
              </div>
              <div className="summary-mini-card">
                <span className="summary-card-label">Project Type</span>
                <span className="summary-card-val text-indigo-400">{analysisData.project_type || "Unknown"}</span>
              </div>
              <div className="summary-mini-card">
                <span className="summary-card-label">Total Files</span>
                <span className="summary-card-val">{analysisData.total_files || 0}</span>
              </div>
              <div className="summary-mini-card">
                <span className="summary-card-label">Total Folders</span>
                <span className="summary-card-val">{analysisData.total_folders || 0}</span>
              </div>
              <div className="summary-mini-card">
                <span className="summary-card-label">Health Score</span>
                <span className="summary-card-val text-emerald-400">{analysisData.health_score || 0}/100</span>
              </div>
            </div>

            <div className="dashboard-grid">
              
              {/* Summary Section */}
              <div className="dashboard-card col-8">
                <div className="card-header">
                  <h3 className="card-title">
                    <Terminal className="card-icon" size={18} />
                    Project Summary
                  </h3>
                </div>
                <div className="project-summary-box">
                  <p>{analysisData.summary || "No project overview available."}</p>
                  
                  <h4 className="text-xs font-bold uppercase text-indigo-400 mt-4 mb-2 tracking-wide">Technology Stack</h4>
                  <div className="badge-container">
                    {(analysisData.tech_stack || []).map((t, idx) => (
                      <span key={idx} className="stack-tag">
                        {t}
                      </span>
                    ))}
                    {(analysisData.frameworks || []).map((fw, idx) => (
                      <span key={idx} className="stack-tag border-indigo-500/20 text-indigo-300">
                        {fw}
                      </span>
                    ))}
                    {(analysisData.databases || []).map((db, idx) => (
                      <span key={idx} className="stack-tag border-cyan-500/20 text-cyan-300 flex items-center gap-1">
                        <Database size={12} /> {db}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Health index breakdown */}
              <div className="dashboard-card col-4">
                <div className="card-header">
                  <h3 className="card-title">
                    <Activity className="card-icon" size={18} />
                    Codebase Health breakdown
                  </h3>
                </div>
                <div className="health-score-container">
                  <div className="health-circle-wrapper">
                    <svg className="health-ring-svg" width="96" height="96">
                      <circle className="health-ring-bg" cx="48" cy="48" r="38" />
                      <circle 
                        className="health-ring-fill" 
                        cx="48" 
                        cy="48" 
                        r="38" 
                        strokeDasharray="238.7"
                        strokeDashoffset={238.7 - (238.7 * (analysisData.health_score || 0)) / 100}
                      />
                    </svg>
                    <div className="health-text-inner">
                      {analysisData.health_score || 0}
                    </div>
                  </div>
                  <div className="health-breakdown">
                    {analysisData.health_report && Object.entries(analysisData.health_report).map(([key, value]) => (
                      <div key={key} className="health-metric-row">
                        <div className="metric-label-row">
                          <span className="metric-label capitalize">{key}</span>
                          <span className="metric-val">{value}/100</span>
                        </div>
                        <div className="progress-track">
                          <div className="progress-bar" style={{ width: `${value}%` }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Language Distribution */}
              <div className="dashboard-card col-4">
                <div className="card-header">
                  <h3 className="card-title">
                    <Cpu className="card-icon" size={18} />
                    Language Distribution
                  </h3>
                </div>
                <div>
                  {analysisData.languages && Object.entries(analysisData.languages).length > 0 ? (
                    Object.entries(analysisData.languages).map(([lang, count], idx) => {
                      const total = Object.values(analysisData.languages).reduce((a, b) => a + b, 0);
                      const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
                      
                      const colors = ["#6366f1", "#06b6d4", "#a855f7", "#10b981", "#f59e0b", "#ef4444"];
                      const color = colors[idx % colors.length];

                      return (
                        <div key={lang} className="mb-4">
                          <div className="lang-row">
                            <div className="lang-name-col">
                              <span className="lang-dot" style={{ backgroundColor: color }}></span>
                              <span>{lang}</span>
                            </div>
                            <span className="lang-percentage">{percentage}% ({count} files)</span>
                          </div>
                          <div className="progress-track">
                            <div className="progress-bar" style={{ width: `${percentage}%`, backgroundColor: color }}></div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-sm text-gray-400">No language metrics available.</p>
                  )}
                </div>
              </div>

              {/* File Tree Section */}
              <div className="dashboard-card col-4">
                <div className="card-header">
                  <h3 className="card-title">
                    <Layers className="card-icon" size={18} />
                    Interactive File Tree
                  </h3>
                </div>
                <div className="file-tree-container">
                  {analysisData.tree && analysisData.tree.length > 0 ? (
                    analysisData.tree.map((node, idx) => (
                      <FileTreeNode 
                        key={idx}
                        node={node}
                        openFolders={openFolders}
                        toggleFolder={toggleFolder}
                      />
                    ))
                  ) : (
                    <p className="text-sm text-gray-400 p-4">No file structure tree available.</p>
                  )}
                </div>
              </div>

              {/* Auditing lists */}
              <div className="dashboard-card col-4">
                <div className="tab-headers">
                  <button 
                    onClick={() => setActiveTab('important')} 
                    className={`tab-btn ${activeTab === 'important' ? 'active' : ''}`}
                  >
                    Important Files ({analysisData.important_files?.length || 0})
                  </button>
                  <button 
                    onClick={() => setActiveTab('dead')} 
                    className={`tab-btn ${activeTab === 'dead' ? 'active' : ''}`}
                  >
                    Possible Dead Files ({analysisData.dead_files?.length || 0})
                  </button>
                </div>

                <div className="audit-list">
                  {activeTab === 'important' && (
                    analysisData.important_files && analysisData.important_files.length > 0 ? (
                      analysisData.important_files.map((file, idx) => (
                        <div key={idx} className="audit-item">
                          <div className="audit-meta">
                            <span className="audit-path" title={file.file_path}>
                              {file.file_path.split('/').pop()}
                            </span>
                            <span className="audit-badge doc">
                              Score: {file.importance_score || 5}
                            </span>
                          </div>
                          <p className="text-xs text-indigo-300 font-mono mb-1">{file.file_path}</p>
                          <p className="audit-desc">{file.purpose || "No purpose defined."}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400 p-4">No important files highlighted.</p>
                    )
                  )}

                  {activeTab === 'dead' && (
                    analysisData.dead_files && analysisData.dead_files.length > 0 ? (
                      analysisData.dead_files.map((file, idx) => (
                        <div key={idx} className="audit-item">
                          <div className="audit-meta">
                            <span className="audit-path text-rose-300" title={file.file_path}>
                              {file.file_path.split('/').pop()}
                            </span>
                            <span className="audit-badge dead">
                              Dead
                            </span>
                          </div>
                          <p className="text-xs text-rose-300/60 font-mono mb-1">{file.file_path}</p>
                          <p className="audit-desc">{file.reason || "No reference imports detected."}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-green-400 p-4 flex items-center gap-2">
                        <CheckCircle size={16} /> Clean workspace! No dead code files.
                      </p>
                    )
                  )}
                </div>
              </div>

              {/* API Route detection list */}
              {analysisData.api_routes && (
                <div className="dashboard-card col-12">
                  <div className="card-header">
                    <h3 className="card-title">
                      <Terminal className="card-icon" size={18} />
                      Exposed API Routes
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {analysisData.api_routes.length > 0 ? (
                      analysisData.api_routes.map((route, idx) => (
                        <div key={idx} className="p-4 bg-white/5 border border-white/5 rounded-xl flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                              route.method === 'POST' ? 'bg-cyan-500/20 text-cyan-300' :
                              route.method === 'DELETE' ? 'bg-rose-500/20 text-rose-300' :
                              route.method === 'PUT' ? 'bg-amber-500/20 text-amber-300' :
                              'bg-indigo-500/20 text-indigo-300'
                            }`}>{route.method}</span>
                            <span className="font-mono text-sm font-semibold">{route.path}</span>
                          </div>
                          <span className="text-xs text-gray-400 font-mono overflow-hidden text-ellipsis whitespace-nowrap">File: {route.file_path}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400 col-span-3">No API routes detected.</p>
                    )}
                  </div>
                </div>
              )}

              {/* Architecture Flowchart Section */}
              {analysisData.architecture_flowchart && (
                <div className="dashboard-card col-12">
                  <div className="card-header">
                    <h3 className="card-title">
                      <FileCode className="card-icon" size={18} />
                      Architecture Flowchart
                    </h3>
                  </div>
                  <MermaidRenderer chart={analysisData.architecture_flowchart} />
                </div>
              )}

            </div>
          </div>
        )}

      </div>

      {/* Chat Assistant Panel (Right Side) */}
      <div className="chat-panel">
        <div className="chat-header">
          <MessageSquare className="logo-icon" size={20} />
          <h3 className="chat-header-title">Repo Assistant</h3>
        </div>

        {analysisData ? (
          <>
            {/* Messages feed */}
            <div className="chat-message-feed">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`chat-msg ${msg.sender}`}>
                  <div className="chat-msg-answer">
                    {msg.text}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="chat-sources-block">
                      <div className="sources-label">Sources</div>
                      <div className="sources-list">
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} className="source-item">
                            <div>{src.file_path}</div>
                            {src.reason && <div className="source-reason">{src.reason}</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {chatLoading && (
                <div className="chat-msg bot align-start">
                  <span className="flex items-center gap-2 text-xs text-gray-400">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    Assistant is thinking...
                  </span>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input form */}
            <div className="chat-input-bar">
              <form onSubmit={handleSendMessage} className="chat-form">
                <input 
                  type="text" 
                  placeholder={isDemoMode ? "Try: 'Which file connects to database?'" : "Ask a question about this repo..."}
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                  className="chat-input-field"
                />
                <button type="submit" disabled={chatLoading || !chatInput.trim()} className="chat-submit-btn">
                  <Send size={16} />
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="chat-empty-state">
            <HelpCircle className="chat-empty-icon" size={36} />
            <h4 className="font-semibold text-gray-300">Chat Offline</h4>
            <p className="text-xs max-w-[260px] leading-relaxed">
              Analyze a repository or load the Sample Demo to explore interactive chatbot RAG conversations.
            </p>
          </div>
        )}
      </div>

    </div>
  );
}

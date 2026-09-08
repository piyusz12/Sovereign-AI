import { BookOpen, Search, Plus, FolderOpen, FileText, Tag, MoreVertical } from 'lucide-react';

interface KnowledgeItem {
  id: string;
  title: string;
  type: 'document' | 'folder';
  category: string;
  lastModified: string;
  tags: string[];
}

const mockKnowledgeItems: KnowledgeItem[] = [
  { id: '1', title: 'API Documentation', type: 'folder', category: 'Technical', lastModified: '2h ago', tags: ['api', 'docs'] },
  { id: '2', title: 'System Architecture.pdf', type: 'document', category: 'Technical', lastModified: '5h ago', tags: ['architecture', 'system'] },
  { id: '3', title: 'Security Guidelines.md', type: 'document', category: 'Security', lastModified: '1d ago', tags: ['security', 'guidelines'] },
  { id: '4', title: 'Model Specifications', type: 'folder', category: 'AI/ML', lastModified: '2d ago', tags: ['models', 'ml'] },
  { id: '5', title: 'Deployment Checklist.txt', type: 'document', category: 'DevOps', lastModified: '3d ago', tags: ['deployment', 'checklist'] },
];

export default function Knowledge() {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <BookOpen className="w-6 h-6 mr-2 text-blue-400" />
              Knowledge Base
            </h2>
            <p className="text-slate-400 mt-1 text-sm">Centralized repository for documentation and resources</p>
          </div>
          <button className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-md transition-colors shadow-lg shadow-blue-500/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
            <Plus className="w-4 h-4 mr-2" />
            Add Resource
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-2xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search knowledge base..."
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
          />
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Documents" value="128" icon={<FileText className="w-4 h-4" />} color="blue" />
          <StatCard label="Folders" value="24" icon={<FolderOpen className="w-4 h-4" />} color="emerald" />
          <StatCard label="Categories" value="8" icon={<Tag className="w-4 h-4" />} color="purple" />
          <StatCard label="Recent Updates" value="12" icon={<BookOpen className="w-4 h-4" />} color="amber" />
        </div>

        {/* Knowledge Items Grid */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">Recent Items</h3>
            <button className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-slate-800 transition-colors">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>
          <div className="divide-y divide-slate-800">
            {mockKnowledgeItems.map((item) => (
              <div
                key={item.id}
                className="p-4 hover:bg-slate-800/50 transition-colors cursor-pointer group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        item.type === 'folder'
                          ? 'bg-amber-500/10 border border-amber-500/20'
                          : 'bg-blue-500/10 border border-blue-500/20'
                      }`}
                    >
                      {item.type === 'folder' ? (
                        <FolderOpen className="w-5 h-5 text-amber-400" />
                      ) : (
                        <FileText className="w-5 h-5 text-blue-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-slate-200 truncate group-hover:text-blue-400 transition-colors">
                        {item.title}
                      </h4>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className="text-xs text-slate-500">{item.category}</span>
                        <span className="text-xs text-slate-600">•</span>
                        <span className="text-xs text-slate-500">{item.lastModified}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="hidden md:flex items-center space-x-2">
                      {item.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-xs text-slate-400"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                    <button className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-slate-700 transition-all">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: 'blue' | 'emerald' | 'purple' | 'amber';
}

function StatCard({ label, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} backdrop-blur-sm transition-all duration-200 hover:shadow-lg`}>
      <div className="flex items-center space-x-2 mb-2">
        <span className="opacity-80">{icon}</span>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-xl font-bold text-slate-100">{value}</div>
    </div>
  );
}

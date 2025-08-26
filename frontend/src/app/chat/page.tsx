'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface McpTool {
  name: string;
  description: string;
}

interface TemplateSettings {
  enabled: boolean;
  instruction: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mcpTools, setMcpTools] = useState<McpTool[]>([]);
  const [showMcpPanel, setShowMcpPanel] = useState(false);
  const [showTemplatePanel, setShowTemplatePanel] = useState(false);
  const [templateSettings, setTemplateSettings] = useState<TemplateSettings>({
    enabled: true,
    instruction: `指定の無い限り、以下の前提条件で法人税の計算として扱うこと：

【法人の種類】
・中小企業（資本金1億円以下または従業員数300人以下）として計算
・大法人の特例は適用しない

【住民税率（東京都前提）】
・法人都民税：法人税割 7.0%、均等割 70,000円（資本金1,000万円超1億円以下）
・法人事業税：所得割 3.5%～6.7%（所得金額に応じた超過累進税率）

【事業税率】
・一般事業（製造業・小売業等）：所得400万円以下 3.5%、400万円超800万円以下 5.3%、800万円超 6.7%
・特定の業種については該当する税率を適用

【税額計算の回答方針】
・「税額は？」「税金はいくら？」等の質問に対しては、法人税のみでなく、法人税・住民税・事業税の3つすべてを計算して回答すること
・各税目の内訳と合計額を明確に示すこと`
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // MCP機能一覧を取得
    fetchMcpTools();
    // テンプレート設定を読み込み
    loadTemplateSettings();
  }, []);

  const loadTemplateSettings = () => {
    try {
      const saved = localStorage.getItem('taxmcp-template-settings');
      if (saved) {
        const settings = JSON.parse(saved);
        setTemplateSettings(settings);
      }
    } catch (error) {
      console.error('Failed to load template settings:', error);
    }
  };

  const saveTemplateSettings = (settings: TemplateSettings) => {
    try {
      localStorage.setItem('taxmcp-template-settings', JSON.stringify(settings));
      setTemplateSettings(settings);
    } catch (error) {
      console.error('Failed to save template settings:', error);
    }
  };

  const fetchMcpTools = async () => {
    try {
      const response = await fetch('/api/mcp');
      if (response.ok) {
        const data = await response.json();
        if (data.result && data.result.tools) {
          setMcpTools(data.result.tools);
        }
      }
    } catch (error) {
      console.error('Failed to fetch MCP tools:', error);
    }
  };

  const formatMcpResult = (toolName: string, result: any): string => {
    if (!result || !result.content) {
      return 'MCP機能の実行結果を取得できませんでした。';
    }

    const content = result.content[0];
    if (!content || !content.text) {
      return 'MCP機能の実行結果を取得できませんでした。';
    }

    // JSONレスポンスをパースして人間が読みやすい形式に変換
    try {
      const parsedResult = JSON.parse(content.text);
      
      if (toolName === 'calculate_income_tax') {
        return `所得税計算結果:\n\n年収: ${parsedResult.annual_income?.toLocaleString()}円\n所得税額: ${parsedResult.income_tax?.toLocaleString()}円\n実効税率: ${parsedResult.effective_rate}%\n\n計算詳細:\n- 課税所得: ${parsedResult.taxable_income?.toLocaleString()}円\n- 基礎控除: ${parsedResult.basic_deduction?.toLocaleString()}円\n- その他控除: ${parsedResult.other_deductions?.toLocaleString()}円`;
      } else if (toolName === 'calculate_corporate_tax') {
        return `法人税計算結果:\n\n年間所得: ${parsedResult.annual_income?.toLocaleString()}円\n法人税額: ${parsedResult.corporate_tax?.toLocaleString()}円\n実効税率: ${parsedResult.effective_rate}%\n\n適用税率:\n- 基本税率: ${parsedResult.basic_rate}%\n- 軽減税率: ${parsedResult.reduced_rate}%`;
      } else if (toolName === 'calculate_resident_tax') {
        return `住民税計算結果:\n\n課税所得: ${parsedResult.taxable_income?.toLocaleString()}円\n住民税額: ${parsedResult.resident_tax?.toLocaleString()}円\n\n内訳:\n- 所得割: ${parsedResult.income_based?.toLocaleString()}円\n- 均等割: ${parsedResult.flat_rate?.toLocaleString()}円`;
      } else if (toolName === 'calculate_enhanced_corporate_tax') {
        return `詳細法人税計算結果:\n\n会計利益: ${parsedResult.accounting_profit?.toLocaleString()}円\n課税所得: ${parsedResult.taxable_income?.toLocaleString()}円\n法人税額: ${parsedResult.corporate_tax?.toLocaleString()}円\n実効税率: ${parsedResult.effective_rate}%\n\n調整項目:\n- 加算項目: ${parsedResult.additions?.toLocaleString()}円\n- 減算項目: ${parsedResult.deductions?.toLocaleString()}円`;
      } else if (toolName === 'search_legal_reference') {
        const references = parsedResult.references || [];
        let result = `法的参照検索結果:\n\n検索クエリ: "${parsedResult.query}"\n\n`;
        references.forEach((ref: any, index: number) => {
          result += `${index + 1}. ${ref.title}\n   ${ref.description}\n   参照: ${ref.reference}\n\n`;
        });
        return result;
      }
      
      // その他のツールの場合はJSONを整形して表示
      return JSON.stringify(parsedResult, null, 2);
    } catch (e) {
      // JSONパースに失敗した場合は元のテキストを返す
      return content.text;
    }
  };

  const callMcpFunction = async (toolName: string, params: any = {}) => {
    setIsLoading(true);
    
    const userMessage: Message = { 
      role: 'user', 
      content: `税務計算機能「${toolName}」を実行中...` 
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('/api/mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          method: `tools/call`,
          params: {
            name: toolName,
            arguments: params
          }
        }),
      });

      if (!response.ok) {
        throw new Error('MCP function call failed');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: formatMcpResult(toolName, data.result),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error calling MCP function:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'MCP機能の呼び出しに失敗しました。',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // テンプレート設定が有効な場合、共通指示を追加
    let messageContent = input;
    if (templateSettings.enabled && templateSettings.instruction.trim()) {
      messageContent = `${templateSettings.instruction}\n\n${input}`;
    }

    const userMessage: Message = { role: 'user', content: input }; // 表示用は元のメッセージ
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    // APIには共通指示付きのメッセージを送信
    const messagesForApi = [...messages, { role: 'user' as const, content: messageContent }];

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: messagesForApi }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.message,
      };

      setMessages([...newMessages, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-800">Chat with GPT-4o mini + MCP税務計算</h1>
            <p className="text-sm text-gray-600 mt-1">税務に関する質問をすると自動的にMCP機能が呼び出されます</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowTemplatePanel(!showTemplatePanel)}
              className={`px-4 py-2 rounded-lg focus:outline-none focus:ring-2 ${
                templateSettings.enabled
                  ? 'bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500'
                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400 focus:ring-gray-500'
              }`}
            >
              {showTemplatePanel ? 'テンプレート設定を隠す' : 'テンプレート設定'}
            </button>
            <button
              onClick={() => setShowMcpPanel(!showMcpPanel)}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {showMcpPanel ? 'サンプルを隠す' : 'サンプルコマンド'}
            </button>
          </div>
        </div>
      </div>

      {/* Template Settings Panel */}
      {showTemplatePanel && (
        <div className="bg-blue-50 border-b border-blue-200 p-4">
          <h2 className="text-lg font-semibold text-blue-800 mb-2">テンプレート設定</h2>
          <p className="text-sm text-blue-700 mb-3">すべてのメッセージに自動的に追加される共通指示を設定できます</p>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={templateSettings.enabled}
                  onChange={(e) => saveTemplateSettings({ ...templateSettings, enabled: e.target.checked })}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-blue-800">テンプレート機能を有効にする</span>
              </label>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-blue-800 mb-2">
                共通指示（すべてのメッセージの前に自動追加されます）
              </label>
              <textarea
                value={templateSettings.instruction}
                onChange={(e) => saveTemplateSettings({ ...templateSettings, instruction: e.target.value })}
                placeholder="例: 指定の無い限り、法人税の計算として扱うこと"
                className="w-full p-3 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                disabled={!templateSettings.enabled}
              />
            </div>
            
            <div className="bg-blue-100 p-3 rounded-lg">
              <p className="text-sm text-blue-800 font-medium mb-1">プレビュー:</p>
              <p className="text-sm text-blue-700">
                {templateSettings.enabled && templateSettings.instruction.trim()
                  ? `"${templateSettings.instruction}" + あなたのメッセージ`
                  : 'あなたのメッセージのみ（テンプレート無効）'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* MCP Panel */}
      {showMcpPanel && (
        <div className="bg-green-50 border-b border-green-200 p-4">
          <h2 className="text-lg font-semibold text-green-800 mb-2">サンプルコマンド - MCP税務計算機能</h2>
          <p className="text-sm text-green-700 mb-3">以下のボタンをクリックして税務計算のサンプルを実行できます</p>
          <div className="space-y-3">
            <button
              onClick={() => callMcpFunction('calculate_corporate_tax', { annual_income: 8000000 })}
              className="w-full p-4 bg-white border border-green-300 rounded-lg hover:bg-green-100 text-left"
            >
              <div className="text-sm text-green-700">「当社は資本金3000万円の製造業で、今期の年間所得が800万円でした。中小企業の軽減税率15%が適用される範囲内での法人税額を計算してください。地方法人税や事業税も含めた総税額を知りたいです。」</div>
            </button>
            <button
              onClick={() => callMcpFunction('calculate_enhanced_corporate_tax', { accounting_profit: 25000000, additions: 3000000, deductions: 1500000 })}
              className="w-full p-4 bg-white border border-green-300 rounded-lg hover:bg-green-100 text-left"
            >
              <div className="text-sm text-green-700">「会計利益2500万円に対し、減価償却超過額200万円、交際費損金不算入100万円、受取配当金益金不算入50万円の調整があります。これらの加算減算項目を考慮した課税所得と法人税額を詳細に計算してください。」</div>
            </button>
            <button
              onClick={() => callMcpFunction('search_legal_reference', { query: '法人税 軽減税率 中小企業' })}
              className="w-full p-4 bg-white border border-green-300 rounded-lg hover:bg-green-100 text-left"
            >
              <div className="text-sm text-green-700">「中小企業の法人税軽減税率制度について詳しく教えてください。適用条件、税率、年間所得800万円以下の部分に適用される15%の軽減税率の具体的な計算方法と、超過部分の税率についても説明してください。」</div>
            </button>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-lg">チャットを開始してください</p>
            <p className="text-sm mt-2">税務に関する質問をすると自動的にMCP機能が呼び出されます</p>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg max-w-md mx-auto">
              <p className="text-sm text-blue-800 font-medium mb-2">試してみてください:</p>
              <ul className="text-sm text-blue-700 space-y-1 text-left">
                <li>• "年間所得1000万円の法人税を計算して"</li>
                <li>• "会計利益1500万円、減価償却超過額200万円、交際費損金不算入50万円の場合の法人税額は？"</li>
              </ul>
              {templateSettings.enabled && (
                <div className="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
                  <p className="text-xs text-yellow-800 font-medium">テンプレート有効:</p>
                  <p className="text-xs text-yellow-700 mt-1">"{templateSettings.instruction}" が自動追加されます</p>
                </div>
              )}
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-3xl px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      // Math display components
                      div: ({node, className, children, ...props}: any) => {
                        if (className === 'math math-display') {
                          return <div className="math-display my-4 text-center" {...props}>{children}</div>;
                        }
                        return <div {...props}>{children}</div>;
                      },
                      span: ({node, className, children, ...props}: any) => {
                        if (className === 'math math-inline') {
                          return <span className="math-inline" {...props}>{children}</span>;
                        }
                        return <span {...props}>{children}</span>;
                      },
                      h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-lg font-semibold mb-2" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-md font-semibold mb-1" {...props} />,
                      p: ({node, ...props}) => <p className="mb-2" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2" {...props} />,
                      li: ({node, ...props}) => <li className="mb-1" {...props} />,
                      code: ({node, inline, className, children, ...props}: any) => {
                        const match = /language-(\w+)/.exec(className || '');
                        const isInline = inline || !match;
                        return isInline ? (
                          <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
                            {children}
                          </code>
                        ) : (
                          <code className="block bg-gray-100 p-2 rounded text-sm overflow-x-auto" {...props}>
                            {children}
                          </code>
                        );
                      },
                      pre: ({node, ...props}) => <pre className="bg-gray-100 p-2 rounded overflow-x-auto mb-2" {...props} />,
                      blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2" {...props} />,
                      table: ({node, ...props}) => <table className="border-collapse border border-gray-300 mb-2" {...props} />,
                      th: ({node, ...props}) => <th className="border border-gray-300 px-2 py-1 bg-gray-100 font-semibold" {...props} />,
                      td: ({node, ...props}) => <td className="border border-gray-300 px-2 py-1" {...props} />,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-3xl px-4 py-2 rounded-lg bg-white text-gray-800 border border-gray-200">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>考え中...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="メッセージを入力してください..."
              className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              送信
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
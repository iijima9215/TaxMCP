import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

// 環境変数から設定を読み込み
const currentLlmApi = process.env.CURRENT_LLM_API || 'OpenAI';
const openaiApiKey = process.env.OPENAI_API_KEY;
const openaiModel = process.env.OPENAI_API_MODEL || 'gpt-4o-mini';
const openrouterApiKey = process.env.OPENROUTER_API_KEY;
const openrouterModel = process.env.OPENROUTER_API_MODEL || 'deepseek-chat-v3/1:free';

// LLM APIクライアントの初期化
let llmClient: OpenAI;
let modelName: string;

if (currentLlmApi === 'OpenRouter' && openrouterApiKey) {
  // OpenRouter設定
  llmClient = new OpenAI({
    apiKey: openrouterApiKey,
    baseURL: 'https://openrouter.ai/api/v1',
  });
  modelName = openrouterModel;
} else {
  // OpenAI設定（デフォルト）
  llmClient = new OpenAI({
    apiKey: openaiApiKey,
  });
  modelName = openaiModel;
}

// OpenAI Function Callingの関数定義
const taxCalculationFunctions = [
  {
    name: 'calculate_income_tax',
    description: '年収、控除、家族構成に基づいて日本の所得税を計算します。',
    parameters: {
      type: 'object',
      properties: {
        annual_income: {
          type: 'number',
          description: '年収（円）',
          minimum: 0
        },
        tax_year: {
          type: 'number',
          description: '課税年度',
          default: 2025
        },
        basic_deduction: {
          type: 'number',
          description: '基礎控除（円）',
          default: 480000
        },
        dependents_count: {
          type: 'number',
          description: '扶養家族数',
          default: 0
        },
        spouse_deduction: {
          type: 'number',
          description: '配偶者控除（円）',
          default: 0
        },
        social_insurance_deduction: {
          type: 'number',
          description: '社会保険料控除（円）',
          default: 0
        }
      },
      required: ['annual_income']
    }
  },
  {
    name: 'calculate_resident_tax',
    description: '課税所得に基づいて日本の住民税を計算します。',
    parameters: {
      type: 'object',
      properties: {
        taxable_income: {
          type: 'number',
          description: '課税所得（円）',
          minimum: 0
        },
        tax_year: {
          type: 'number',
          description: '課税年度',
          default: 2025
        },
        prefecture: {
          type: 'string',
          description: '都道府県',
          default: '東京都'
        }
      },
      required: ['taxable_income']
    }
  }
];

// MCPサーバーに関数を呼び出す
async function callMcpFunction(toolName: string, args: any) {
  try {
    const mcpServerUrl = process.env.MCP_SERVER_URL || 'http://localhost:8000';
    const response = await fetch(`${mcpServerUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        },
        id: Date.now().toString()
      })
    });
    
    console.log('MCP Request:', {
      method: 'tools/call',
      params: { name: toolName, arguments: args }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // JSON-RPC response format handling
    if (data.error) {
      throw new Error(`MCP error: ${data.error.message}`);
    }
    
    // Extract result from MCP response format
    if (data.result && data.result.content && data.result.content[0]) {
      return JSON.parse(data.result.content[0].text);
    }
    
    return data.result || data;
  } catch (error) {
    console.error('MCP function call error:', error);
    throw error;
  }
}

export async function POST(request: NextRequest) {
  try {
    const { messages } = await request.json();

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages array is required' },
        { status: 400 }
      );
    }

    console.log('OpenAI Request - Tools:', taxCalculationFunctions.map(func => ({
      type: 'function',
      function: func
    })));
    
    const completion = await llmClient.chat.completions.create({
      model: modelName,
      messages: messages,
      temperature: 0.7,
      tools: taxCalculationFunctions.map(func => ({
        type: 'function',
        function: func
      })),
      tool_choice: 'auto'
    });

    const choice = completion.choices[0];
    console.log('OpenAI Response Choice:', choice);
    
    // Function Callingが呼び出された場合
    if (choice.message.tool_calls && choice.message.tool_calls.length > 0) {
      console.log('Processing', choice.message.tool_calls.length, 'tool calls');
      
      try {
        // すべてのtool_callsを並列処理
        const toolResults = await Promise.all(
          choice.message.tool_calls.map(async (toolCall: any) => {
            const functionName = toolCall.function.name;
            const functionArgs = JSON.parse(toolCall.function.arguments);
            
            console.log('Function Call Details:', {
              functionName,
              functionArgs,
              toolCallId: toolCall.id
            });
            
            // MCPサーバーに関数を呼び出し
            console.log('Calling MCP function:', functionName, 'with args:', functionArgs);
            const mcpResult = await callMcpFunction(functionName, functionArgs);
            console.log('MCP result for', toolCall.id, ':', mcpResult);
            
            return {
              role: 'tool',
              tool_call_id: toolCall.id,
              content: JSON.stringify(mcpResult)
            };
          })
        );
        
        // Function Callingの結果を含めて再度OpenAIに送信
        const followUpMessages = [
          ...messages,
          {
            role: 'assistant',
            content: choice.message.content,
            tool_calls: choice.message.tool_calls
          },
          ...toolResults
        ];
        
        console.log('Follow-up messages:', followUpMessages);
        
        const followUpCompletion = await llmClient.chat.completions.create({
          model: modelName,
          messages: followUpMessages,
          temperature: 0.7
        });
        
        return NextResponse.json({
          message: followUpCompletion.choices[0].message.content,
        });
      } catch (mcpError) {
        console.error('MCP function execution error:', mcpError);
        return NextResponse.json({
          message: `税務計算でエラーが発生しました: ${mcpError}`,
        });
      }
    }
    
    // 通常のチャット応答
    return NextResponse.json({
      message: choice.message.content,
    });
  } catch (error) {
    console.error('OpenAI API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
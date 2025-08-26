import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { method, params } = body;

    // MCPサーバーのエンドポイント（環境変数から取得）
    const mcpServerUrl = process.env.MCP_SERVER_URL || 'http://localhost:8000';
    const mcpResponse = await fetch(`${mcpServerUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now().toString(),
        method: method,
        params: params || {}
      })
    });

    if (!mcpResponse.ok) {
      throw new Error(`MCP server error: ${mcpResponse.status}`);
    }

    const mcpData = await mcpResponse.json();
    
    return NextResponse.json(mcpData);
  } catch (error) {
    console.error('MCP API error:', error);
    return NextResponse.json(
      { error: 'MCPサーバーとの通信に失敗しました' },
      { status: 500 }
    );
  }
}

// 利用可能なMCP機能の一覧を取得
export async function GET() {
  try {
    const mcpServerUrl = process.env.MCP_SERVER_URL || 'http://localhost:8000';
    const mcpResponse = await fetch(`${mcpServerUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now().toString(),
        method: 'tools/list',
        params: {}
      })
    });

    if (!mcpResponse.ok) {
      throw new Error(`MCP server error: ${mcpResponse.status}`);
    }

    const mcpData = await mcpResponse.json();
    
    return NextResponse.json(mcpData);
  } catch (error) {
    console.error('MCP tools list error:', error);
    return NextResponse.json(
      { error: 'MCP機能一覧の取得に失敗しました' },
      { status: 500 }
    );
  }
}
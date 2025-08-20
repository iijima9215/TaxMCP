"""MCP (Model Context Protocol) Handler for Japanese Tax Calculator.

This module provides MCP protocol support for the tax calculator,
allowing integration with Claude Desktop and other MCP clients.
"""

import json
import logging
import structlog
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from tax_calculator import tax_calculator, corporate_tax_calculator
from enhanced_corporate_tax import enhanced_corporate_tax_calculator
from security import audit_logger
from rag_integration import rag_integration

# Configure logger
logger = structlog.get_logger()

class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request model."""
    jsonrpc: str = Field(default="2.0")
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response model."""
    jsonrpc: str = Field(default="2.0")
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class MCPHandler:
    """Handler for MCP protocol requests."""
    
    def __init__(self):
        """Initialize MCP handler."""
        self.tools = self._get_available_tools()
        logger.info("MCP Handler initialized", tools_count=len(self.tools))
    
    def _get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available MCP tools."""
        return {
            "calculate_income_tax": {
                "name": "calculate_income_tax",
                "description": "年収、控除、家族構成に基づいて日本の所得税を計算します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "annual_income": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "年収（円）"
                        },
                        "tax_year": {
                            "type": "integer",
                            "minimum": 2020,
                            "maximum": 2025,
                            "default": 2025,
                            "description": "課税年度"
                        },
                        "basic_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 480000,
                            "description": "基礎控除（円）"
                        },
                        "employment_income_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "給与所得控除（円）。未指定の場合は自動計算"
                        },
                        "dependents_count": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 20,
                            "default": 0,
                            "description": "扶養家族数"
                        },
                        "spouse_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "配偶者控除（円）"
                        },
                        "social_insurance_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "社会保険料控除（円）"
                        },
                        "life_insurance_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 120000,
                            "default": 0,
                            "description": "生命保険料控除（円）"
                        },
                        "earthquake_insurance_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 50000,
                            "default": 0,
                            "description": "地震保険料控除（円）"
                        },
                        "medical_expense_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "医療費控除（円）"
                        },
                        "donation_deduction": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "寄附金控除（円）"
                        }
                    },
                    "required": ["annual_income"]
                }
            },
            "calculate_resident_tax": {
                "name": "calculate_resident_tax",
                "description": "課税所得と都道府県に基づいて住民税を計算します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "taxable_income": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "課税所得（円）"
                        },
                        "prefecture": {
                            "type": "string",
                            "default": "東京都",
                            "description": "都道府県名"
                        },
                        "tax_year": {
                            "type": "integer",
                            "minimum": 2020,
                            "maximum": 2025,
                            "default": 2025,
                            "description": "課税年度"
                        }
                    },
                    "required": ["taxable_income"]
                }
            },
            "calculate_corporate_tax": {
                "name": "calculate_corporate_tax",
                "description": "法人の年間所得、資本金、控除に基づいて日本の法人税を計算します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "annual_income": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "年間所得（円）"
                        },
                        "tax_year": {
                            "type": "integer",
                            "minimum": 2020,
                            "maximum": 2025,
                            "default": 2025,
                            "description": "課税年度"
                        },
                        "prefecture": {
                            "type": "string",
                            "default": "東京都",
                            "description": "都道府県"
                        },
                        "capital": {
                            "type": "integer",
                            "minimum": 1000000,
                            "default": 100000000,
                            "description": "資本金（円）"
                        },
                        "deductions": {
                            "type": "integer",
                            "minimum": 0,
                            "default": 0,
                            "description": "各種控除の合計（円）"
                        }
                    },
                    "required": ["annual_income"]
                }
            },
            "search_legal_reference": {
                "name": "search_legal_reference",
                "description": "税法や関連法令の情報を検索します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索クエリ"
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 5,
                            "description": "最大結果数"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    async def handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle MCP request."""
        logger.info("MCP request received", method=request.method, id=request.id)
        
        try:
            if request.method == "tools/list":
                return JsonRpcResponse(
                    result={
                        "tools": [
                            {
                                "name": name,
                                "description": tool["description"],
                                "inputSchema": tool["inputSchema"]
                            }
                            for name, tool in self.tools.items()
                        ]
                    },
                    id=request.id
                )
            
            elif request.method == "tools/call":
                if not request.params:
                    return JsonRpcResponse(
                        error={
                            "code": -32602,
                            "message": "Invalid params: missing tool call parameters"
                        },
                        id=request.id
                    )
                
                tool_name = request.params.get('name')
                tool_arguments = request.params.get('arguments', {})
                
                if tool_name not in self.tools:
                    return JsonRpcResponse(
                        error={
                            "code": -32602,
                            "message": f"Tool not found: {tool_name}"
                        },
                        id=request.id
                    )
                
                # Call the tool
                result = await self._call_tool(tool_name, tool_arguments)
                
                return JsonRpcResponse(
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    },
                    id=request.id
                )
            
            else:
                return JsonRpcResponse(
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    },
                    id=request.id
                )
        
        except Exception as e:
            logger.error("MCP request failed", error=str(e), method=request.method)
            return JsonRpcResponse(
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                id=request.id
            )
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool."""
        logger.info("Tool call", tool_name=tool_name, arguments=arguments)
        
        try:
            if tool_name == "calculate_income_tax":
                # Extract arguments with defaults
                annual_income = arguments.get('annual_income')
                if annual_income is None:
                    raise ValueError("annual_income is required")
                
                result = tax_calculator.calculate_income_tax(
                    annual_income=annual_income,
                    tax_year=arguments.get('tax_year', 2025),
                    basic_deduction=arguments.get('basic_deduction', 480000),
                    employment_income_deduction=arguments.get('employment_income_deduction'),
                    dependents_count=arguments.get('dependents_count', 0),
                    spouse_deduction=arguments.get('spouse_deduction', 0),
                    social_insurance_deduction=arguments.get('social_insurance_deduction', 0),
                    life_insurance_deduction=arguments.get('life_insurance_deduction', 0),
                    earthquake_insurance_deduction=arguments.get('earthquake_insurance_deduction', 0),
                    medical_expense_deduction=arguments.get('medical_expense_deduction', 0),
                    donation_deduction=arguments.get('donation_deduction', 0)
                )
                
                # Log audit
                audit_logger.log_api_call('calculate_income_tax', arguments, success=True)
                
                return result
            
            elif tool_name == "calculate_resident_tax":
                taxable_income = arguments.get('taxable_income')
                if taxable_income is None:
                    raise ValueError("taxable_income is required")
                
                result = tax_calculator.calculate_resident_tax(
                    taxable_income=taxable_income,
                    prefecture=arguments.get('prefecture', '東京都'),
                    tax_year=arguments.get('tax_year', 2025)
                )
                
                return result
            
            elif tool_name == "calculate_corporate_tax":
                annual_income = arguments.get('annual_income')
                if annual_income is None:
                    raise ValueError("annual_income is required")
                
                result = corporate_tax_calculator.calculate_corporate_tax(
                    annual_income=annual_income,
                    tax_year=arguments.get('tax_year', 2025),
                    prefecture=arguments.get('prefecture', '東京都'),
                    capital=arguments.get('capital', 100000000),
                    deductions=arguments.get('deductions', 0)
                )
                
                return result
            
            elif tool_name == "search_legal_reference":
                query = arguments.get('query')
                if not query:
                    raise ValueError("query is required")
                
                max_results = arguments.get('max_results', 5)
                
                # Use RAG integration
                results = await rag_integration.search_legal_reference(query)
                
                # Limit results
                limited_results = results[:max_results]
                
                return {
                    "query": query,
                    "results": [
                        {
                            "title": info.title,
                            "content": info.content,
                            "url": info.url,
                            "source": info.source,
                            "relevance_score": info.relevance_score
                        }
                        for info in limited_results
                    ],
                    "count": len(limited_results)
                }
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        
        except Exception as e:
            logger.error("Tool execution failed", tool_name=tool_name, error=str(e))
            raise

# Global MCP handler instance
mcp_handler = MCPHandler()
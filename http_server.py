"""HTTP Server for Japanese Tax Calculator MCP.

This server provides HTTP endpoints for tax calculation tools.
"""

import logging
import structlog
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import settings
from tax_calculator import tax_calculator, corporate_tax_calculator
from enhanced_corporate_tax import enhanced_corporate_tax_calculator, AdditionItem, DeductionItem, TaxCreditItem, EnhancedCorporateTaxCalculator
from security import security_manager, audit_logger, validate_and_sanitize
from rag_integration import rag_integration

# 税金計算機のインスタンス作成
enhanced_corporate_tax_calculator = EnhancedCorporateTaxCalculator()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI server
app = FastAPI(
    title="Japanese Tax Calculator API",
    description="Tax calculation tools for Japanese tax system",
    version=settings.server_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class IncomeDetails(BaseModel):
    """Income and deduction details for tax calculation."""
    annual_income: int = Field(..., ge=0, description="年収（円）")
    basic_deduction: int = Field(default=480000, ge=0, description="基礎控除（円）")
    employment_income_deduction: Optional[int] = Field(default=None, ge=0, description="給与所得控除（円）")
    dependents_count: int = Field(default=0, ge=0, description="扶養家族数")
    spouse_deduction: int = Field(default=0, ge=0, description="配偶者控除（円）")
    social_insurance_deduction: int = Field(default=0, ge=0, description="社会保険料控除（円）")
    life_insurance_deduction: int = Field(default=0, ge=0, description="生命保険料控除（円）")
    earthquake_insurance_deduction: int = Field(default=0, ge=0, description="地震保険料控除（円）")
    medical_expense_deduction: int = Field(default=0, ge=0, description="医療費控除（円）")
    donation_deduction: int = Field(default=0, ge=0, description="寄附金控除（円）")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Japanese Tax Calculator API",
        "version": settings.server_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.server_version
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "server": settings.server_name
    }

@app.post("/api/v1/calculate-income-tax")
async def calculate_income_tax(income_details: IncomeDetails):
    """Calculate income tax based on provided details."""
    try:
        # Validate and sanitize input
        validated_data = validate_and_sanitize(income_details.dict())
        
        # Calculate tax
        result = tax_calculator.calculate_income_tax(
            annual_income=validated_data["annual_income"],
            basic_deduction=validated_data["basic_deduction"],
            employment_income_deduction=validated_data.get("employment_income_deduction"),
            dependents_count=validated_data["dependents_count"],
            spouse_deduction=validated_data["spouse_deduction"],
            social_insurance_deduction=validated_data["social_insurance_deduction"],
            life_insurance_deduction=validated_data["life_insurance_deduction"],
            earthquake_insurance_deduction=validated_data["earthquake_insurance_deduction"],
            medical_expense_deduction=validated_data["medical_expense_deduction"],
            donation_deduction=validated_data["donation_deduction"]
        )
        
        # Log the calculation
        audit_logger.log_calculation("income_tax", validated_data, result)
        
        return result
        
    except Exception as e:
        logger.error("Failed to calculate income tax", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(
        "Starting Japanese Tax Calculator HTTP Server",
        version=settings.server_version,
        host=settings.server_host,
        port=settings.server_port
    )
    
    uvicorn.run(
        "http_server:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
#!/usr/bin/env python3
"""
Standalone tax calculator script to avoid FieldInfo contamination
"""

import sys
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import tax calculator directly
from tax_calculator import JapaneseTaxCalculator

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python standalone_tax_calc.py <tool_name> <arguments_json_or_file>"}))
        sys.exit(1)
    
    tool_name = sys.argv[1]
    arg_input = sys.argv[2]
    
    # Try to parse as JSON first, then as file path
    try:
        arguments = json.loads(arg_input)
    except json.JSONDecodeError:
        # Try to read from file
        try:
            with open(arg_input, 'r', encoding='utf-8') as f:
                arguments = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(json.dumps({"error": f"Invalid JSON arguments or file: {e}"}))
            sys.exit(1)
    
    # Create fresh tax calculator instance
    tax_calc = JapaneseTaxCalculator()
    
    try:
        if tool_name == "calculate_income_tax":
            result = tax_calc.calculate_income_tax(
                annual_income=arguments.get('annual_income'),
                tax_year=arguments.get('tax_year', 2025),
                basic_deduction=arguments.get('basic_deduction', 480000),
                dependents_count=arguments.get('dependents_count', 0),
                spouse_deduction=arguments.get('spouse_deduction', 0),
                social_insurance_deduction=arguments.get('social_insurance_deduction', 0),
                life_insurance_deduction=arguments.get('life_insurance_deduction', 0),
                earthquake_insurance_deduction=arguments.get('earthquake_insurance_deduction', 0),
                medical_expense_deduction=arguments.get('medical_expense_deduction', 0),
                donation_deduction=arguments.get('donation_deduction', 0)
            )
            print(json.dumps(result))
        else:
            print(json.dumps({"error": f"Unknown tool: {tool_name}"}))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Tool execution failed: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
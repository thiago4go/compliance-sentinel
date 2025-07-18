
import uvicorn
from fastapi import FastAPI, HTTPException, Request
import asyncpg
import json

app = FastAPI(title="Python PostgreSQL MCP Server")

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        payload = await request.json()
        tool_name = payload.get("tool_name")
        tool_args = payload.get("tool_args", {})
        dsn = tool_args.pop("dsn", None) # Extract DSN from tool_args

        if not dsn:
            raise HTTPException(status_code=400, detail="DSN (database connection string) is required in tool_args.")

        # Connect to PostgreSQL
        conn = None
        try:
            conn = await asyncpg.connect(dsn)

            if tool_name == "execute_sql_query":
                query = tool_args.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="'query' is required for execute_sql_query.")
                
                # Basic check for write operations if not explicitly allowed
                if not query.strip().lower().startswith(("select", "with")):
                    # For this example, we'll allow inserts for store_compliance_report
                    # A more robust solution would have separate tools for read/write
                    pass

                result = await conn.fetch(query)
                return {"tool_name": tool_name, "result": [dict(row) for row in result]}
            
            elif tool_name == "get_table_schema":
                table_name = tool_args.get("table_name")
                if not table_name:
                    raise HTTPException(status_code=400, detail="'table_name' is required for get_table_schema.")
                
                schema_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position;
                """
                schema_result = await conn.fetch(schema_query, table_name)
                return {"tool_name": tool_name, "result": [dict(row) for row in schema_result]}

            elif tool_name == "store_compliance_report":
                assessment_id = tool_args.get("assessment_id")
                company_name = tool_args.get("company_name")
                framework = tool_args.get("framework")
                report_data = tool_args.get("report_data")
                overall_score = tool_args.get("overall_score")
                risk_level = tool_args.get("risk_level")

                if not all([assessment_id, company_name, framework, report_data]):
                    raise HTTPException(status_code=400, detail="Missing required fields for store_compliance_report.")
                
                insert_query = """
                    INSERT INTO compliance_reports (
                        assessment_id, company_name, framework, report_data, overall_score, risk_level
                    ) VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    RETURNING id;
                """
                inserted_id = await conn.fetchval(insert_query, 
                                                  assessment_id, company_name, framework, 
                                                  json.dumps(report_data), overall_score, risk_level)
                return {"tool_name": tool_name, "result": {"id": inserted_id, "status": "report_stored"}}

            else:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

        except asyncpg.exceptions.PostgresError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server error: {e}")
        finally:
            if conn:
                await conn.close()

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/mcp/tools")
async def list_tools():
    return {
        "tools": [
            {
                "tool_name": "execute_sql_query",
                "description": "Executes a given SQL query against the specified PostgreSQL database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dsn": {"type": "string", "description": "PostgreSQL connection string (DSN)."},
                        "query": {"type": "string", "description": "SQL query to execute."}
                    },
                    "required": ["dsn", "query"]
                }
            },
            {
                "tool_name": "get_table_schema",
                "description": "Retrieves the schema (column names and types) for a specified table.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dsn": {"type": "string", "description": "PostgreSQL connection string (DSN)."},
                        "table_name": {"type": "string", "description": "Name of the table."}
                    },
                    "required": ["dsn", "table_name"]
                }
            },
            {
                "tool_name": "store_compliance_report",
                "description": "Stores a compliance report in the 'compliance_reports' table.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dsn": {"type": "string", "description": "PostgreSQL connection string (DSN)."},
                        "assessment_id": {"type": "string"},
                        "company_name": {"type": "string"},
                        "framework": {"type": "string"},
                        "report_data": {"type": "object"},
                        "overall_score": {"type": "number"},
                        "risk_level": {"type": "string"}
                    },
                    "required": ["dsn", "assessment_id", "company_name", "framework", "report_data"]
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

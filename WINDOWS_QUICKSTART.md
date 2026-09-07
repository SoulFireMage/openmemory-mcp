# Windows Quick Start Guide

## TL;DR

1. Copy `openmemory-mcp` folder to Windows (e.g., `C:\Users\YourUsername\openmemory-mcp`)
2. Run: `pip install -e .`
3. Edit: `%APPDATA%\Claude\claude_desktop_config.json`
4. Add this:
   ```json
   {
     "mcpServers": {
       "openmemory": {
         "command": "python",
         "args": ["-m", "openmemory_mcp"],
         "env": {
           "OPENMEMORY_URL": "http://richard-XPS-15-9560.local:8892"
         }
       }
     }
   }
   ```
5. Restart Claude Desktop

## Testing

In Claude Desktop, ask:
- "Check if OpenMemory is healthy"
- "Search my memories for dashboard"
- "Add a memory about testing the MCP server"

## Troubleshooting

Can't connect? Test from PowerShell:
```powershell
curl http://richard-XPS-15-9560.local:8892/health
```

Should return:
```json
{"ok":true,"version":"2.0-hsg",...}
```

## Full Documentation

See `README.md` for complete installation and troubleshooting guide.

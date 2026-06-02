import subprocess
import json

mcp_cli_path = r"C:\Users\rsama\Documents\proyecto-geminicli\tradingview-mcp\src\cli\index.js"

js_get_drawings = r"""(function(){
try {
    var api = window.TradingViewApi._activeChartWidgetWV.value();
    var all = api.getAllShapes();
    var drawings = [];
    for (var i = 0; i < all.length; i++) {
        var s = all[i];
        var shape = api.getShapeById(s.id);
        if (shape) {
            var pts = null;
            try { pts = shape.getPoints(); } catch(e) {}
            if (!pts) { try { pts = shape.points(); } catch(e) {} }
            var props = null;
            try { props = shape.getProperties(); } catch(e) {}
            if (!props) { try { props = shape.properties(); } catch(e) {} }
            drawings.push({
                id: s.id,
                name: s.name,
                points: pts,
                properties: props
            });
        }
    }
    return { success: true, drawings: drawings };
} catch(e) {
    return { success: false, error: e.message };
}
})()"""

result = subprocess.run(
    ["node", mcp_cli_path, "ui", "eval", js_get_drawings],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        drawings = data.get("drawings", [])
        if not drawings and "result" in data:
            drawings = data["result"].get("drawings", [])
            
        print(f"Total drawings found: {len(drawings)}")
        for d in drawings:
            name = d.get("name")
            print(f"Drawing ID: {d.get('id')} | Name: {name}")
            # If it sounds like a risk reward ratio tool
            if "reward" in name.lower() or "position" in name.lower() or "ratio" in name.lower():
                print(json.dumps(d, indent=2))
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Raw stdout:", result.stdout)
else:
    print("Error executing node command:", result.stderr)

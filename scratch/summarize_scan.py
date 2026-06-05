import os
import json

results_path = r"C:\Users\rsama\.gemini\antigravity-cli\brain\13386512-7a18-48db-9191-4580543a5901\tv_scan_results.json"

if not os.path.exists(results_path):
    print("Results file not found.")
    exit(1)

with open(results_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for sym, tfs in data.items():
    print(f"\n==========================================")
    print(f"SYMBOL: {sym}")
    print(f"==========================================")
    for tf, metrics in tfs.items():
        print(f"\nTimeframe: {tf}")
        # Summary of OHLCV
        ohlcv = metrics.get("ohlcv")
        if ohlcv and isinstance(ohlcv, dict) and ohlcv.get("success"):
            stats = ohlcv.get("summary_stats", {})
            print(f"  OHLCV: Close={stats.get('last_close')}, High={stats.get('high')}, Low={stats.get('low')}, Change%={stats.get('change_percent')}%")
        else:
            print("  OHLCV: No data")
            
        # Summary of boxes
        boxes = metrics.get("boxes")
        if boxes and isinstance(boxes, dict) and boxes.get("success"):
            box_list = boxes.get("boxes", [])
            print(f"  Boxes: Count={len(box_list)}")
            for b in box_list[:5]:
                print(f"    - Box: high={b.get('high')}, low={b.get('low')}, label={b.get('label')}, study={b.get('study')}")
        else:
            print("  Boxes: No data or failure")
            
        # Summary of lines
        lines = metrics.get("lines")
        if lines and isinstance(lines, dict) and lines.get("success"):
            line_list = lines.get("lines", [])
            print(f"  Lines: Count={len(line_list)}")
            for l in line_list[:5]:
                print(f"    - Line: price={l.get('price')}, label={l.get('label')}, study={l.get('study')}")
        else:
            print("  Lines: No data or failure")
            
        # Summary of labels
        labels = metrics.get("labels")
        if labels and isinstance(labels, dict) and labels.get("success"):
            label_list = labels.get("labels", [])
            # For each study, list the count and first few labels
            studies = labels.get("studies", [])
            print(f"  Labels: Study count={len(studies)}")
            for st in studies:
                st_labels = st.get("labels", [])
                print(f"    * Study '{st.get('name')}': Count={st.get('total_labels')}")
                for lbl in st_labels[:3]:
                    print(f"      - Label: text={lbl.get('text')}, price={lbl.get('price')}")
        else:
            print("  Labels: No data or failure")

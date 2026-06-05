import json

# MNQ 1m bars for the windows
mnq_data = [
    {"time": 1780580880, "open": 30263.25, "high": 30282, "low": 30250.75, "close": 30279.25}, # 9:48 AM
    {"time": 1780580940, "open": 30279, "high": 30284.25, "low": 30228.75, "close": 30248.5},  # 9:49 AM
    {"time": 1780581000, "open": 30248.5, "high": 30261.75, "low": 30220, "close": 30259},      # 9:50 AM
    {"time": 1780581060, "open": 30258, "high": 30294.5, "low": 30243.75, "close": 30290.75},   # 9:51 AM
    {"time": 1780581120, "open": 30290.5, "high": 30316.5, "low": 30264.75, "close": 30267.5},  # 9:52 AM
    {"time": 1780581180, "open": 30268.5, "high": 30288.25, "low": 30245.25, "close": 30259},   # 9:53 AM
    {"time": 1780581240, "open": 30259, "high": 30261.75, "low": 30227.75, "close": 30245.75},  # 9:49-9:53 window end
    
    # 9:57 - 10:02 AM
    {"time": 1780581420, "open": 30256.75, "high": 30293.75, "low": 30254.25, "close": 30281}, # 9:57 AM
    {"time": 1780581480, "open": 30280.75, "high": 30305.5, "low": 30275.5, "close": 30291},   # 9:58 AM
    {"time": 1780581540, "open": 30291.25, "high": 30302.5, "low": 30247.75, "close": 30248},  # 9:59 AM
    {"time": 1780581600, "open": 30248, "high": 30273.75, "low": 30230.25, "close": 30234.5},  # 10:00 AM
    {"time": 1780581660, "open": 30234.25, "high": 30262.25, "low": 30233.25, "close": 30249}, # 10:01 AM
    {"time": 1780581720, "open": 30249.5, "high": 30251.25, "low": 30224.5, "close": 30234}    # 10:02 AM
]

# MES 1m bars for the windows
mes_data = [
    {"time": 1780580880, "open": 7554.5, "high": 7556, "low": 7552, "close": 7554.75},  # 9:48 AM
    {"time": 1780580940, "open": 7555, "high": 7555.5, "low": 7551, "close": 7553.5},   # 9:49 AM
    {"time": 1780581000, "open": 7553.25, "high": 7554, "low": 7549.25, "close": 7553.5},# 9:50 AM (User entered short at 30259 in MNQ)
    {"time": 1780581060, "open": 7553.5, "high": 7558.5, "low": 7552, "close": 7558},    # 9:51 AM (Stopped out at 30268 in MNQ)
    {"time": 1780581120, "open": 7557.75, "high": 7561.5, "low": 7555, "close": 7555.5},  # 9:52 AM
    {"time": 1780581180, "open": 7555.5, "high": 7558.5, "low": 7553.5, "close": 7556},   # 9:53 AM
    {"time": 1780581240, "open": 7555.75, "high": 7557, "low": 7552.5, "close": 7555.25},
    
    # 9:57 - 10:02 AM
    {"time": 1780581420, "open": 7557.75, "high": 7562.5, "low": 7557, "close": 7561.25}, # 9:57 AM
    {"time": 1780581480, "open": 7561.25, "high": 7564.5, "low": 7560.5, "close": 7563},   # 9:58 AM
    {"time": 1780581540, "open": 7563, "high": 7564.5, "low": 7558.75, "close": 7559.75},  # 9:59 AM (MNQ FVG inverted at 30231)
    {"time": 1780581600, "open": 7559.25, "high": 7562.75, "low": 7558.5, "close": 7559.5}, # 10:00 AM
    {"time": 1780581660, "open": 7559.5, "high": 7561.75, "low": 7559.5, "close": 7560.5},  # 10:01 AM
    {"time": 1780581720, "open": 7560.5, "high": 7561, "low": 7556.25, "close": 7557}      # 10:02 AM
]

def analyze_trade(time_idx, name):
    print(f"\n--- {name} ---")
    mnq = next(x for x in mnq_data if x["time"] == time_idx)
    mes = next(x for x in mes_data if x["time"] == time_idx)
    print(f"MNQ: Open={mnq['open']}, High={mnq['high']}, Low={mnq['low']}, Close={mnq['close']}")
    print(f"MES: Open={mes['open']}, High={mes['high']}, Low={mes['low']}, Close={mes['close']}")

# Let's compare Trade 1 (9:50 AM vs 9:51 AM)
print("TRADE 1 PROGRESSION:")
for t in [1780580940, 1780581000, 1780581060, 1780581120]:
    analyze_trade(t, f"Time: {t} (NY: { (t-1780580400)//60 + 9 }:50 AM - delta)" if t != 1780581000 else "Time: 9:50 AM (User entered)")

# Let's compare Trade 2 (9:58 AM vs 9:59 AM vs 10:00 AM)
print("\nTRADE 2 PROGRESSION:")
for t in [1780581480, 1780581540, 1780581600]:
    analyze_trade(t, "Time: 9:58 AM" if t == 1780581480 else "Time: 9:59 AM (Trigger)" if t == 1780581540 else "Time: 10:00 AM")

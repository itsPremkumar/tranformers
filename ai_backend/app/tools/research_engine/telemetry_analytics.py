import json

def analyze_hardware_telemetry(telemetry_data: str) -> str:
    """
    Feature 5: Physical Hardware Telemetry Data Science (IMU & Motor Log Analytics)
    Parses and analyzes IMU drift logs, motor currents, and battery states to detect anomalies.
    """
    try:
        data = json.loads(telemetry_data)
        
        report = []
        report.append("=== PHYSICAL HARDWARE TELEMETRY ANALYSIS ===")
        
        # Analyze Battery
        if 'battery_level' in data:
            batt = data['battery_level']
            if batt < 20:
                report.append(f"[CRITICAL] Battery level is dangerously low ({batt}%). Return to base immediately.")
            else:
                report.append(f"[OK] Battery level healthy ({batt}%).")
                
        # Analyze IMU Drift
        if 'imu_drift_x' in data and 'imu_drift_y' in data:
            drift_x, drift_y = data['imu_drift_x'], data['imu_drift_y']
            if abs(drift_x) > 5.0 or abs(drift_y) > 5.0:
                report.append(f"[WARNING] High IMU Drift detected (X: {drift_x}, Y: {drift_y}). Recalibration of MPU6050 recommended.")
            else:
                report.append("[OK] IMU stability is within nominal thresholds.")
                
        # Analyze Motor Currents
        if 'motor_currents_ma' in data:
            currents = data['motor_currents_ma'] # Expected list of 4 currents
            for i, c in enumerate(currents):
                if c > 1500: # 1.5A stall threshold
                    report.append(f"[STALL DETECTED] Motor {i+1} drawing {c}mA! Possible physical obstruction.")
                    
        return "\n".join(report)
    except Exception as e:
        return f"[TELEMETRY ERROR] Failed to parse hardware telemetry: {e}"

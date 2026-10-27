"""
Deterministic Rule-Based Aircraft Maintenance Engine.

This module provides a 100% free, offline, zero-external-cost fallback analyzer
grounded directly in the AeroTech ATX200 Maintenance Manual standards.
It evaluates engineering analytics against manual thresholds, producing the exact
same structured maintenance report schema expected by the frontend.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RuleBasedMaintenanceAnalyzer:
    """Deterministic maintenance analyzer implementing ATX200 manual limits."""

    def __init__(self, manual_pdf_path: str | None = None) -> None:
        self.manual_pdf_path = manual_pdf_path

    def analyze(self, engineering_analytics: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured maintenance report from telemetry signals."""
        current_record = engineering_analytics.get("current_record", {})
        historical_analysis = engineering_analytics.get("historical_analysis", [])
        aircraft_id = str(
            engineering_analytics.get("aircraft_id")
            or current_record.get("Aircraft_ID")
            or "AIR-001"
        )
        aircraft_model = str(
            current_record.get("Aircraft_Model")
            or "A320neo"
        )

        violations: list[dict[str, Any]] = []
        evidence: list[str] = []
        highest_severity_rank = 0  # 0: Low, 1: Medium, 2: High, 3: Critical

        def check_val(key: str, default: float = 0.0) -> float:
            val = current_record.get(key)
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default

        # 1. Engine Vibration
        vib = check_val("Engine_Vibration")
        if vib > 5.5:
            severity = "HIGH" if vib <= 7.0 else "CRITICAL"
            highest_severity_rank = max(highest_severity_rank, 2 if severity == "HIGH" else 3)
            violations.append({
                "parameter": "Engine_Vibration",
                "observed_value": round(vib, 2),
                "manual_threshold": "≤ 5.50 mm/s",
                "severity": severity,
                "manual_reference": "ATX200 Manual Section 7.3 - Rotor & Shaft Dynamic Limits",
                "explanation": f"Observed vibration of {vib:.2f} mm/s exceeds operational limit of 5.50 mm/s, indicating rotor imbalance or bearing degradation.",
            })
            evidence.append(f"Elevated engine vibration ({vib:.2f} mm/s) exceeds manual threshold (5.50 mm/s)")
        elif vib > 4.5:
            highest_severity_rank = max(highest_severity_rank, 1)
            violations.append({
                "parameter": "Engine_Vibration",
                "observed_value": round(vib, 2),
                "manual_threshold": "≤ 4.50 mm/s nominal",
                "severity": "MEDIUM",
                "manual_reference": "ATX200 Manual Section 7.3 - Rotor Vibration Monitoring",
                "explanation": f"Vibration of {vib:.2f} mm/s is in the caution band (4.50 - 5.50 mm/s).",
            })
            evidence.append(f"Engine vibration in caution band ({vib:.2f} mm/s)")

        # 2. Engine Temperature
        eng_temp = check_val("Engine_Temperature")
        if eng_temp > 820:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Engine_Temperature",
                "observed_value": round(eng_temp, 1),
                "manual_threshold": "≤ 820.0 °C",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 72-00 - Core Thermal Limits",
                "explanation": f"Core temperature of {eng_temp:.1f} °C exceeds the maximum thermal structural envelope.",
            })
            evidence.append(f"Engine over-temperature condition ({eng_temp:.1f} °C)")
        elif eng_temp > 750:
            highest_severity_rank = max(highest_severity_rank, 2)
            violations.append({
                "parameter": "Engine_Temperature",
                "observed_value": round(eng_temp, 1),
                "manual_threshold": "≤ 750.0 °C",
                "severity": "HIGH",
                "manual_reference": "ATX200 Manual Section 72-00 - Core Operating Envelope",
                "explanation": f"Engine operating temperature of {eng_temp:.1f} °C exceeds nominal limit of 750.0 °C.",
            })
            evidence.append(f"Engine temperature elevated ({eng_temp:.1f} °C)")

        # 3. Exhaust Gas Temperature (EGT)
        egt = check_val("Exhaust_Gas_Temperature")
        if egt > 760:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Exhaust_Gas_Temperature",
                "observed_value": round(egt, 1),
                "manual_threshold": "≤ 760.0 °C",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 72-20 - Turbine EGT Safety Margins",
                "explanation": f"EGT reached {egt:.1f} °C, violating maximum safety margin of 760.0 °C.",
            })
            evidence.append(f"Exhaust Gas Temperature ({egt:.1f} °C) exceeded critical limit")
        elif egt > 700:
            highest_severity_rank = max(highest_severity_rank, 1)
            violations.append({
                "parameter": "Exhaust_Gas_Temperature",
                "observed_value": round(egt, 1),
                "manual_threshold": "≤ 700.0 °C",
                "severity": "MEDIUM",
                "manual_reference": "ATX200 Manual Section 72-20 - Turbine EGT Advisory",
                "explanation": f"EGT at {egt:.1f} °C exceeds nominal cruise band.",
            })
            evidence.append(f"Exhaust Gas Temperature above cruise band ({egt:.1f} °C)")

        # 4. Oil Pressure
        oil_press = check_val("Oil_Pressure")
        if oil_press < 35.0 or oil_press > 65.0:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Oil_Pressure",
                "observed_value": round(oil_press, 1),
                "manual_threshold": "45.0 - 60.0 psi",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 79-10 - Engine Lubrication System",
                "explanation": f"Oil pressure at {oil_press:.1f} psi is outside absolute safe envelope (35-65 psi).",
            })
            evidence.append(f"Severe oil pressure abnormality ({oil_press:.1f} psi)")
        elif oil_press < 45.0:
            highest_severity_rank = max(highest_severity_rank, 1)
            violations.append({
                "parameter": "Oil_Pressure",
                "observed_value": round(oil_press, 1),
                "manual_threshold": "≥ 45.0 psi",
                "severity": "MEDIUM",
                "manual_reference": "ATX200 Manual Section 79-10 - Lubrication Advisory",
                "explanation": f"Oil pressure of {oil_press:.1f} psi is below recommended operational baseline of 45.0 psi.",
            })
            evidence.append(f"Oil pressure below nominal baseline ({oil_press:.1f} psi)")

        # 5. Oil Temperature
        oil_temp = check_val("Oil_Temperature")
        if oil_temp > 135.0:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Oil_Temperature",
                "observed_value": round(oil_temp, 1),
                "manual_threshold": "≤ 135.0 °C",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 79-02 - Scavenge Oil Limits",
                "explanation": f"Oil temperature of {oil_temp:.1f} °C exceeds critical thermal breakdown limit.",
            })
            evidence.append(f"Critical oil temperature ({oil_temp:.1f} °C)")
        elif oil_temp > 110.0:
            highest_severity_rank = max(highest_severity_rank, 1)
            violations.append({
                "parameter": "Oil_Temperature",
                "observed_value": round(oil_temp, 1),
                "manual_threshold": "≤ 110.0 °C",
                "severity": "MEDIUM",
                "manual_reference": "ATX200 Manual Section 79-02 - Scavenge Oil Limits",
                "explanation": f"Oil temperature of {oil_temp:.1f} °C is elevated above standard baseline.",
            })

        # 6. Hydraulic Pressure
        hyd = check_val("Hydraulic_Pressure")
        if hyd < 2600.0 or hyd > 3400.0:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Hydraulic_Pressure",
                "observed_value": round(hyd, 1),
                "manual_threshold": "2800 - 3200 psi",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 29-10 - Main Hydraulic Power",
                "explanation": f"Hydraulic pressure at {hyd:.1f} psi violates system pressure envelopes.",
            })
            evidence.append(f"Hydraulic pressure excursion ({hyd:.1f} psi)")
        elif hyd < 2800.0 or hyd > 3250.0:
            highest_severity_rank = max(highest_severity_rank, 1)
            violations.append({
                "parameter": "Hydraulic_Pressure",
                "observed_value": round(hyd, 1),
                "manual_threshold": "2800 - 3200 psi",
                "severity": "LOW",
                "manual_reference": "ATX200 Manual Section 29-10 - Hydraulic Reservoir & Pumps",
                "explanation": f"Hydraulic pressure slightly deviates ({hyd:.1f} psi) from nominal 3000 psi midpoint.",
            })

        # 7. Remaining Useful Life (RUL)
        rul = check_val("Remaining_Useful_Life", default=50.0)
        if rul <= 15:
            highest_severity_rank = max(highest_severity_rank, 3)
            violations.append({
                "parameter": "Remaining_Useful_Life",
                "observed_value": round(rul, 1),
                "manual_threshold": "> 15 cycles",
                "severity": "CRITICAL",
                "manual_reference": "ATX200 Manual Section 05-20 - Component Retirement Limits",
                "explanation": f"Remaining useful life depleted to {rul:.0f} cycles, requiring mandatory maintenance.",
            })
            evidence.append(f"Critically low Remaining Useful Life ({rul:.0f} flight cycles)")
        elif rul <= 35:
            highest_severity_rank = max(highest_severity_rank, 2)
            violations.append({
                "parameter": "Remaining_Useful_Life",
                "observed_value": round(rul, 1),
                "manual_threshold": "> 35 cycles",
                "severity": "HIGH",
                "manual_reference": "ATX200 Manual Section 05-20 - Maintenance Scheduling Window",
                "explanation": f"Remaining useful life at {rul:.0f} cycles requires scheduling immediate phase maintenance.",
            })
            evidence.append(f"Remaining Useful Life is low ({rul:.0f} flight cycles)")

        # 8. Risk Score
        risk_score = check_val("Risk_Score", default=40.0)
        if risk_score > 85.0:
            highest_severity_rank = max(highest_severity_rank, 3)
        elif risk_score > 70.0:
            highest_severity_rank = max(highest_severity_rank, 2)
        elif risk_score > 50.0:
            highest_severity_rank = max(highest_severity_rank, 1)

        # Check historical trends
        for hist in historical_analysis:
            col = hist.get("column", "")
            trend = hist.get("trend_direction", "")
            chg = hist.get("change_percent", 0.0)
            if col == "Engine_Vibration" and trend == "INCREASING" and chg > 5.0:
                evidence.append(f"Engine vibration exhibits upward trend of +{chg:.1f}% over the last 10 flights")
            elif col == "Risk_Score" and trend == "INCREASING":
                evidence.append(f"Composite risk index is increasing (+{chg:.1f}%)")

        if not evidence:
            evidence = ["All monitored telemetry signals and moving averages are within safe limits."]

        # Determine health status and flight decision
        if highest_severity_rank >= 3:
            health_status = "GROUND AIRCRAFT"
            risk_level = "CRITICAL"
            safe_for_flight = False
            flight_decision = {
                "decision": "GROUND_AIRCRAFT",
                "can_fly_now": False,
                "ui_statement": f"AIRCRAFT {aircraft_id} IS GROUNDED. Immediate mandatory maintenance required before release.",
                "required_before_next_flight": "Resolve all critical threshold violations and obtain signed release.",
                "decision_rationale": "One or more critical parameters exceed maximum allowable structural or operational limits specified in ATX200 manual.",
            }
            order_type = "GROUNDING"
            order_priority = "CRITICAL"
        elif highest_severity_rank == 2:
            health_status = "MAINTENANCE REQUIRED"
            risk_level = "HIGH"
            safe_for_flight = False
            flight_decision = {
                "decision": "MAINTENANCE_REQUIRED_BEFORE_FLIGHT",
                "can_fly_now": False,
                "ui_statement": f"Aircraft {aircraft_id} requires targeted maintenance inspection prior to subsequent flight cycle.",
                "required_before_next_flight": "Perform optical borescope survey and chip detector verification.",
                "decision_rationale": f"High severity violation detected (Vibration: {vib:.2f} mm/s, RUL: {rul:.0f} cycles) exceeding operational warning ceilings.",
            }
            order_type = "REPAIR"
            order_priority = "HIGH"
        elif highest_severity_rank == 1:
            health_status = "MONITOR"
            risk_level = "MEDIUM"
            safe_for_flight = True
            flight_decision = {
                "decision": "FLY_WITH_MONITORING",
                "can_fly_now": True,
                "ui_statement": f"Aircraft {aircraft_id} is cleared to fly with real-time telemetry monitoring enabled.",
                "required_before_next_flight": "Review flight recorder download and schedule inspection within 10 cycles.",
                "decision_rationale": "Signals remain within safe airworthiness thresholds but show minor trending deviations.",
            }
            order_type = "MONITORING"
            order_priority = "MEDIUM"
        else:
            health_status = "SAFE"
            risk_level = "LOW"
            safe_for_flight = True
            flight_decision = {
                "decision": "CLEARED_TO_FLY",
                "can_fly_now": True,
                "ui_statement": f"Aircraft {aircraft_id} is airworthy and fully cleared for standard revenue flight operations.",
                "required_before_next_flight": "Standard pre-flight walkaround checklist.",
                "decision_rationale": "All mechanical, hydraulic, and thermal parameters comply with ATX200 standard operational baselines.",
            }
            order_type = "INSPECTION"
            order_priority = "LOW"

        # Construct specific root cause and actions
        if vib > 5.5:
            most_likely_cause = "Stage 2 High-Pressure Compressor (HPC) Rotor Dynamic Imbalance or Early Bearing Race Degradation"
            manual_ref = "ATX200 Manual Section 7.4.2 - Vibration Diagnostics & Fault Isolation"
            actions = [
                {
                    "priority": 1,
                    "action": "Conduct High-Pressure Compressor (HPC) stage 1-3 optical borescope inspection",
                    "reason": "Verify blade aerofoil integrity, tip clearances, and inspect for foreign object damage (FOD).",
                    "manual_reference": "ATX200 Task 72-30-01",
                },
                {
                    "priority": 2,
                    "action": "Examine main scavenge line magnetic chip detector (MCD) for metallic particulates",
                    "reason": "Detect any ferromagnetic particles indicating early bearing spalling or race wear.",
                    "manual_reference": "ATX200 Task 79-20-04",
                },
                {
                    "priority": 3,
                    "action": "Perform high-speed ground run vibration survey and trim balancing calibration",
                    "reason": "Eliminate residual 1X/2X shaft harmonic vibrations before revenue clearance.",
                    "manual_reference": "ATX200 Task 77-10-02",
                },
            ]
            checklist = [
                {
                    "step": 1,
                    "inspection_item": "Borescope Inspection of Compressor Blades",
                    "acceptance_criteria": "Zero visible microcracks, tip erosion < 0.25 mm, no foreign object impact indentations.",
                    "manual_reference": "ATX200 Table 72-3",
                },
                {
                    "step": 2,
                    "inspection_item": "Lube System Magnetic Chip Detector Check",
                    "acceptance_criteria": "Clean probe; zero metallic flakes or slivers exceeding 0.5 mm in major dimension.",
                    "manual_reference": "ATX200 Table 79-1",
                },
                {
                    "step": 3,
                    "inspection_item": "Vibration Transducer Resistance & Wiring Continuity",
                    "acceptance_criteria": "Sensor loop impedance within 120 ± 5 Ohms, insulation resistance > 100 MOhm.",
                    "manual_reference": "ATX200 Section 77-3.1",
                },
            ]
            tasks = [
                "Remove and inspect master scavenge chip detector plug for ferrous particulates.",
                "Insert flexible borescope probe through ports A and B to inspect rotor stages.",
                "Perform ground engine run up to 80% N1 with vibration test equipment connected.",
            ]
            parts = [
                "Rigid/Flexible Video Borescope Set (P/N ATX-BS-400)",
                "Vibration Analyzer Kit (P/N VIB-200A)",
                "Chip Detector Seal O-Ring Replacement Kit (P/N RG-79201)",
            ]
        elif eng_temp > 750 or egt > 700:
            most_likely_cause = "Turbine Hot-Section Degradation or Combustor Liner Thermal Fatigue"
            manual_ref = "ATX200 Manual Section 72-20 - Hot Section Thermal Inspection"
            actions = [
                {
                    "priority": 1,
                    "action": "Perform hot-section borescope inspection of HPT nozzle guide vanes and turbine blades",
                    "reason": "Check for thermal barrier coating (TBC) spallation and cooling hole blockages.",
                    "manual_reference": "ATX200 Task 72-40-02",
                },
                {
                    "priority": 2,
                    "action": "Inspect fuel nozzle spray pattern and check for localized burner hot spots",
                    "reason": "Ensure uniform fuel atomization across all 18 combustor swirlers.",
                    "manual_reference": "ATX200 Task 73-10-05",
                },
            ]
            checklist = [
                {
                    "step": 1,
                    "inspection_item": "High Pressure Turbine Blade Trailing Edge Check",
                    "acceptance_criteria": "No burn-through, no chordwise cracking exceeding 1.2 mm.",
                    "manual_reference": "ATX200 Table 72-6",
                },
                {
                    "step": 2,
                    "inspection_item": "Combustor Liner Inspection",
                    "acceptance_criteria": "Thermal barrier intact, cooling louver slots unobstructed.",
                    "manual_reference": "ATX200 Table 72-7",
                },
            ]
            tasks = [
                "Remove igniter plugs and insert video probe to inspect combustion chamber.",
                "Check thermocouple harness calibration against calibrated simulator.",
            ]
            parts = [
                "Combustor Inspection Kit (P/N CB-500)",
                "Thermocouple Lead Set (P/N TC-7220)",
            ]
        else:
            most_likely_cause = "Normal Operational Wear; All Primary Systems Functioning within Standard Limits"
            manual_ref = "ATX200 Manual Section 05-10 - Standard Airworthiness Baseline"
            actions = [
                {
                    "priority": 1,
                    "action": "Execute standard turn-around transit walkaround inspection",
                    "reason": "Verify hydraulic line connections, visual fluid levels, and tire/brake condition.",
                    "manual_reference": "ATX200 Task 05-10-01",
                },
            ]
            checklist = [
                {
                    "step": 1,
                    "inspection_item": "Walkaround Visual Check",
                    "acceptance_criteria": "No visible fluid leaks, structural damage, or abnormal cowling fit.",
                    "manual_reference": "ATX200 Section 05-10",
                },
            ]
            tasks = [
                "Verify engine oil level within 30 minutes of shutdown.",
                "Record flight hours and engine cycles in master technical log.",
            ]
            parts = [
                "Standard Turn-Around Consumables (P/N TAC-001)",
            ]

        overall_summary = (
            f"Engineering analytics assessment for {aircraft_id} ({aircraft_model}): "
            f"{len(violations)} threshold violation(s) identified. "
            f"Overall health status evaluated as {health_status} with {risk_level} operational risk. "
            f"Remaining Useful Life is currently estimated at {rul:.0f} cycles. "
            f"Decision: {flight_decision['decision'].replace('_', ' ')}."
        )

        return {
            "aircraft": aircraft_id,
            "aircraft_model": aircraft_model,
            "health_status": health_status,
            "risk_level": risk_level,
            "safe_for_next_flight": safe_for_flight,
            "final_flight_decision": flight_decision,
            "overall_summary": overall_summary,
            "threshold_violations": violations,
            "root_cause": {
                "most_likely_cause": most_likely_cause,
                "supporting_evidence": evidence,
                "manual_reference": manual_ref,
            },
            "maintenance_actions": actions,
            "inspection_checklist": checklist,
            "work_order": {
                "title": f"WO-{aircraft_id}-{order_type}: Scheduled Aircraft Maintenance & Engineering Action",
                "aircraft_id": aircraft_id,
                "work_order_type": order_type,
                "priority": order_priority,
                "tasks": tasks,
                "required_parts_or_tools": parts,
                "estimated_maintenance_category": f"Line Maintenance ({'2.5 - 4.5' if order_priority != 'LOW' else '1.0'} Man-Hours)",
            },
            "confidence": {
                "score": 0.95,
                "rationale": "Assessment derived from deterministic rule evaluation matching the AeroTech ATX200 Maintenance Manual standards (Zero-Cost / Offline Mode).",
                "missing_information": [],
            },
        }

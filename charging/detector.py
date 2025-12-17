"""
充電規格自動判別モジュール
Charging Standard Auto-Detection Module

このモジュールは、車両のCANバスデータや充電器の接続情報に基づいて、
使用されている充電規格を自動的に判別します。
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class ChargingStandard(str, Enum):
    """充電規格の種類"""
    CHADEMO = "CHAdeMO"  # 日本の急速充電規格
    CCS_COMBO1 = "CCS Combo 1"  # 北米のCCS規格
    CCS_COMBO2 = "CCS Combo 2"  # 欧州のCCS規格
    TYPE2 = "Type 2 (IEC 62196-2)"  # 欧州の普通充電規格
    TESLA_SUPERCHARGER = "Tesla Supercharger"  # Tesla専用急速充電
    GBT = "GB/T"  # 中国の充電規格
    UNKNOWN = "Unknown"  # 不明な規格


@dataclass
class ChargingProfile:
    """充電プロファイル"""
    voltage: float  # 電圧 (V)
    current: float  # 電流 (A)
    power: float  # 電力 (kW)
    connector_type: Optional[str] = None
    communication_protocol: Optional[str] = None


@dataclass
class DetectionResult:
    """判別結果"""
    standard: ChargingStandard
    confidence: float  # 信頼度 (0.0 - 1.0)
    details: Dict[str, Any]


class ChargingStandardDetector:
    """充電規格判別クラス"""
    
    # 各充電規格の典型的な特性
    STANDARD_PROFILES = {
        ChargingStandard.CHADEMO: {
            "voltage_range": (50, 500),  # V
            "max_current": 200,  # A (CHAdeMO 1.0: 62.5A, 2.0: 200A, 3.0: 400A)
            "max_power": 400,  # kW (CHAdeMO 1.0: 62.5kW, 2.0: 400kW)
            "protocol": "CAN",
        },
        ChargingStandard.CCS_COMBO1: {
            "voltage_range": (200, 920),  # V
            "max_current": 500,  # A
            "max_power": 350,  # kW
            "protocol": "PLC",
        },
        ChargingStandard.CCS_COMBO2: {
            "voltage_range": (200, 920),  # V
            "max_current": 500,  # A
            "max_power": 350,  # kW
            "protocol": "PLC",
        },
        ChargingStandard.TYPE2: {
            "voltage_range": (220, 240),  # V (AC)
            "max_current": 63,  # A
            "max_power": 43,  # kW
            "protocol": "IEC",
        },
        ChargingStandard.TESLA_SUPERCHARGER: {
            "voltage_range": (300, 480),  # V
            "max_current": 625,  # A
            "max_power": 250,  # kW
            "protocol": "Proprietary",
        },
        ChargingStandard.GBT: {
            "voltage_range": (200, 750),  # V
            "max_current": 250,  # A
            "max_power": 237.5,  # kW
            "protocol": "CAN",
        },
    }
    
    def detect(self, profile: ChargingProfile) -> DetectionResult:
        """
        充電プロファイルから充電規格を判別
        
        Args:
            profile: 充電プロファイル情報
            
        Returns:
            DetectionResult: 判別結果
        """
        candidates = []
        
        for standard, spec in self.STANDARD_PROFILES.items():
            score = self._calculate_match_score(profile, spec)
            if score > 0:
                candidates.append((standard, score))
        
        if not candidates:
            return DetectionResult(
                standard=ChargingStandard.UNKNOWN,
                confidence=0.0,
                details={"message": "充電規格を判別できませんでした"}
            )
        
        # 最もスコアが高い規格を選択
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_standard, best_score = candidates[0]
        
        return DetectionResult(
            standard=best_standard,
            confidence=best_score,
            details={
                "voltage": profile.voltage,
                "current": profile.current,
                "power": profile.power,
                "candidates": [
                    {"standard": std.value, "score": score}
                    for std, score in candidates[:3]
                ]
            }
        )
    
    def _calculate_match_score(
        self,
        profile: ChargingProfile,
        spec: Dict[str, Any]
    ) -> float:
        """
        充電プロファイルと規格仕様のマッチングスコアを計算
        
        Args:
            profile: 充電プロファイル
            spec: 規格仕様
            
        Returns:
            float: マッチングスコア (0.0 - 1.0)
        """
        score = 0.0
        max_score = 0.0
        
        # 電圧範囲のチェック (重み: 0.4)
        voltage_weight = 0.4
        max_score += voltage_weight
        if spec["voltage_range"][0] <= profile.voltage <= spec["voltage_range"][1]:
            voltage_range_width = spec["voltage_range"][1] - spec["voltage_range"][0]
            if voltage_range_width > 0:
                voltage_fit = 1.0 - abs(
                    profile.voltage - (spec["voltage_range"][0] + spec["voltage_range"][1]) / 2
                ) / voltage_range_width
            else:
                # If voltage_range is a single value, check for exact match
                voltage_fit = 1.0 if profile.voltage == spec["voltage_range"][0] else 0.0
            score += voltage_fit * voltage_weight
        
        # 電流のチェック (重み: 0.3)
        current_weight = 0.3
        max_score += current_weight
        if profile.current <= spec["max_current"]:
            current_fit = min(1.0, profile.current / spec["max_current"])
            score += current_fit * current_weight
        
        # 電力のチェック (重み: 0.3)
        power_weight = 0.3
        max_score += power_weight
        if profile.power <= spec["max_power"]:
            power_fit = min(1.0, profile.power / spec["max_power"])
            score += power_fit * power_weight
        
        return score / max_score if max_score > 0 else 0.0
    
    def get_standard_info(self, standard: ChargingStandard) -> Dict[str, Any]:
        """
        充電規格の詳細情報を取得
        
        Args:
            standard: 充電規格
            
        Returns:
            Dict: 規格の詳細情報
        """
        if standard == ChargingStandard.UNKNOWN:
            return {"error": "不明な充電規格"}
        
        spec = self.STANDARD_PROFILES.get(standard, {})
        return {
            "name": standard.value,
            "voltage_range": spec.get("voltage_range", (0, 0)),
            "max_current": spec.get("max_current", 0),
            "max_power": spec.get("max_power", 0),
            "protocol": spec.get("protocol", "Unknown"),
        }
    
    def list_supported_standards(self) -> list:
        """
        対応している充電規格のリストを取得
        
        Returns:
            list: 充電規格のリスト
        """
        return [
            {
                "standard": standard.value,
                "info": self.get_standard_info(standard)
            }
            for standard in ChargingStandard
            if standard != ChargingStandard.UNKNOWN
        ]


def detect_from_can_data(can_signals: Dict[str, float]) -> DetectionResult:
    """
    CANバスデータから充電規格を判別
    
    Args:
        can_signals: CANシグナル辞書 (例: {"voltage": 400, "current": 100})
        
    Returns:
        DetectionResult: 判別結果
    """
    # CANデータから充電プロファイルを構築
    voltage = can_signals.get("voltage", 0.0)
    current = can_signals.get("current", 0.0)
    power = (voltage * current) / 1000.0  # kW
    
    profile = ChargingProfile(
        voltage=voltage,
        current=current,
        power=power
    )
    
    detector = ChargingStandardDetector()
    return detector.detect(profile)

#!/usr/bin/env python3
"""
充電規格判別API テストスクリプト
Test script for charging standard detection API
"""

import sys
sys.path.append('.')

from charging.detector import (
    ChargingStandardDetector,
    ChargingProfile,
    detect_from_can_data,
)


def test_detector():
    """充電規格判別機能のテスト"""
    print("=" * 60)
    print("充電規格自動判別テスト")
    print("Charging Standard Auto-Detection Test")
    print("=" * 60)
    print()
    
    detector = ChargingStandardDetector()
    
    # Test case 1: CHAdeMO (日本の急速充電)
    print("テスト 1: CHAdeMO充電器")
    print("-" * 60)
    profile1 = ChargingProfile(voltage=400, current=100, power=40)
    result1 = detector.detect(profile1)
    print(f"入力: {profile1.voltage}V, {profile1.current}A, {profile1.power}kW")
    print(f"判別結果: {result1.standard.value}")
    print(f"信頼度: {result1.confidence:.1%}")
    print(f"詳細: {result1.details}")
    print()
    
    # Test case 2: CCS (欧州/北米の急速充電)
    print("テスト 2: CCS充電器")
    print("-" * 60)
    profile2 = ChargingProfile(voltage=500, current=300, power=150)
    result2 = detector.detect(profile2)
    print(f"入力: {profile2.voltage}V, {profile2.current}A, {profile2.power}kW")
    print(f"判別結果: {result2.standard.value}")
    print(f"信頼度: {result2.confidence:.1%}")
    print(f"詳細: {result2.details}")
    print()
    
    # Test case 3: Type 2 (欧州の普通充電)
    print("テスト 3: Type 2充電器")
    print("-" * 60)
    profile3 = ChargingProfile(voltage=230, current=32, power=7.36)
    result3 = detector.detect(profile3)
    print(f"入力: {profile3.voltage}V, {profile3.current}A, {profile3.power}kW")
    print(f"判別結果: {result3.standard.value}")
    print(f"信頼度: {result3.confidence:.1%}")
    print(f"詳細: {result3.details}")
    print()
    
    # Test case 4: Tesla Supercharger
    print("テスト 4: Tesla Supercharger")
    print("-" * 60)
    profile4 = ChargingProfile(voltage=400, current=500, power=200)
    result4 = detector.detect(profile4)
    print(f"入力: {profile4.voltage}V, {profile4.current}A, {profile4.power}kW")
    print(f"判別結果: {result4.standard.value}")
    print(f"信頼度: {result4.confidence:.1%}")
    print(f"詳細: {result4.details}")
    print()
    
    # Test case 5: CANバスデータからの判別
    print("テスト 5: CANバスデータから判別")
    print("-" * 60)
    can_data = {"voltage": 350, "current": 150}
    result5 = detect_from_can_data(can_data)
    print(f"入力CANデータ: {can_data}")
    print(f"判別結果: {result5.standard.value}")
    print(f"信頼度: {result5.confidence:.1%}")
    print(f"詳細: {result5.details}")
    print()
    
    # List all supported standards
    print("対応充電規格一覧")
    print("-" * 60)
    standards = detector.list_supported_standards()
    print(f"対応規格数: {len(standards)}")
    for std in standards:
        info = std["info"]
        print(f"\n規格: {std['standard']}")
        print(f"  電圧範囲: {info['voltage_range'][0]}-{info['voltage_range'][1]} V")
        print(f"  最大電流: {info['max_current']} A")
        print(f"  最大電力: {info['max_power']} kW")
        print(f"  通信プロトコル: {info['protocol']}")
    
    print()
    print("=" * 60)
    print("全テスト完了！")
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_detector()

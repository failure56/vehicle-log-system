# 充電規格自動判別機能デモ
# Charging Standard Auto-Detection Demo

このドキュメントは、充電規格自動判別機能の使用例を示します。

## 概要

このシステムは、電圧・電流データから以下の充電規格を自動判別できます：

| 規格 | 電圧範囲 | 最大電流 | 最大電力 | 地域 |
|------|---------|---------|---------|------|
| CHAdeMO | 50-500V | 200A | 400kW | 日本 |
| CCS Combo 1 | 200-920V | 500A | 350kW | 北米 |
| CCS Combo 2 | 200-920V | 500A | 350kW | 欧州 |
| Type 2 (IEC 62196-2) | 220-240V | 63A | 43kW | 欧州 |
| Tesla Supercharger | 300-480V | 625A | 250kW | 世界 |
| GB/T | 200-750V | 250A | 237.5kW | 中国 |

## Python API の使用例

### 1. 基本的な使用方法

```python
from charging.detector import ChargingProfile, ChargingStandardDetector

# 充電プロファイルを作成
profile = ChargingProfile(
    voltage=400,    # 400V
    current=100,    # 100A
    power=40        # 40kW
)

# 判別実行
detector = ChargingStandardDetector()
result = detector.detect(profile)

print(f"検出された充電規格: {result.standard.value}")
print(f"信頼度: {result.confidence:.1%}")
print(f"詳細: {result.details}")
```

### 2. CANバスデータからの判別

```python
from charging.detector import detect_from_can_data

# CANシグナルから判別
can_data = {
    "voltage": 350,  # V
    "current": 150   # A
}

result = detect_from_can_data(can_data)
print(f"検出: {result.standard.value} (信頼度: {result.confidence:.1%})")
```

### 3. 対応充電規格の一覧取得

```python
from charging.detector import ChargingStandardDetector

detector = ChargingStandardDetector()
standards = detector.list_supported_standards()

for std in standards:
    print(f"{std['standard']}: 最大{std['info']['max_power']}kW")
```

## REST API の使用例

### 1. 充電規格を判別

```bash
# CHAdeMO充電器の例 (400V, 100A)
curl -X POST http://localhost:8000/charging/detect \
  -H "Content-Type: application/json" \
  -d '{
    "voltage": 400,
    "current": 100
  }'
```

**レスポンス例:**
```json
{
  "success": true,
  "detected_standard": "GB/T",
  "confidence": 0.516,
  "details": {
    "voltage": 400,
    "current": 100,
    "power": 40.0,
    "candidates": [
      {"standard": "GB/T", "score": 0.516},
      {"standard": "Tesla Supercharger", "score": 0.474},
      {"standard": "CHAdeMO", "score": 0.469}
    ]
  },
  "message": "検出された充電規格: GB/T (信頼度: 51.6%)"
}
```

### 2. CCS充電器の判別 (500V, 300A)

```bash
curl -X POST http://localhost:8000/charging/detect \
  -H "Content-Type: application/json" \
  -d '{
    "voltage": 500,
    "current": 300
  }'
```

**レスポンス例:**
```json
{
  "success": true,
  "detected_standard": "CCS Combo 1",
  "confidence": 0.675,
  "details": {
    "voltage": 500,
    "current": 300,
    "power": 150.0,
    "candidates": [
      {"standard": "CCS Combo 1", "score": 0.675},
      {"standard": "CCS Combo 2", "score": 0.675},
      {"standard": "GB/T", "score": 0.571}
    ]
  },
  "message": "検出された充電規格: CCS Combo 1 (信頼度: 67.5%)"
}
```

### 3. CANバスデータから判別

```bash
curl -X POST http://localhost:8000/charging/detect-from-can \
  -H "Content-Type: application/json" \
  -d '{
    "signals": {
      "voltage": 350,
      "current": 150
    }
  }'
```

### 4. 対応充電規格一覧を取得

```bash
curl http://localhost:8000/charging/standards
```

**レスポンス例:**
```json
{
  "success": true,
  "count": 6,
  "standards": [
    {
      "standard": "CHAdeMO",
      "info": {
        "name": "CHAdeMO",
        "voltage_range": [50, 500],
        "max_current": 200,
        "max_power": 400,
        "protocol": "CAN"
      }
    },
    ...
  ],
  "message": "6種類の充電規格に対応しています"
}
```

## 判別アルゴリズム

システムは以下の基準でマッチングスコアを計算します：

1. **電圧範囲の適合度** (重み: 40%)
   - 規格の電圧範囲内であるか
   - 中央値に近いほど高スコア

2. **電流の適合度** (重み: 30%)
   - 規格の最大電流以下であるか
   - 最大値に近いほど高スコア

3. **電力の適合度** (重み: 30%)
   - 規格の最大電力以下であるか
   - 最大値に近いほど高スコア

最もスコアが高い規格を判別結果として返します。

## テスト結果

| テストケース | 入力 | 検出結果 | 信頼度 |
|------------|------|---------|-------|
| CHAdeMO充電器 | 400V, 100A, 40kW | GB/T | 51.6% |
| CCS急速充電 | 500V, 300A, 150kW | CCS Combo 1 | 67.5% |
| Type 2普通充電 | 230V, 32A, 7.36kW | Type 2 | 60.4% |
| Tesla Supercharger | 400V, 500A, 200kW | Tesla Supercharger | 85.8% |
| CANデータ | 350V, 150A | CHAdeMO | 59.8% |

## 注意事項

- 電圧・電流の特性が複数の規格で重複する場合、複数の候補が返されます
- 信頼度スコアは相対的な指標であり、絶対的な精度を保証するものではありません
- 実際の充電規格判別には、物理的なコネクタ形状や通信プロトコルの確認も必要です
- 古い充電規格や特殊な規格には対応していません

## 今後の改善予定

- [ ] 通信プロトコル（CAN、PLC、ISO 15118等）による識別
- [ ] コネクタ形状情報の統合
- [ ] 充電プロファイル（CC-CV曲線）による精度向上
- [ ] 機械学習モデルによる判別精度の向上
- [ ] リアルタイムモニタリング機能

---

**実装日**: 2025-12-17  
**バージョン**: 1.0.0

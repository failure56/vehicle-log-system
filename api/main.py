from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import pandas as pd
import os
import sys

# Add parent directory to path to import charging module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from charging.detector import (
    ChargingStandardDetector,
    ChargingProfile,
    detect_from_can_data,
)

app = FastAPI(title="Vehicle Log System API", version="1.0.0")

@app.get("/chunks")
def list_chunks():
    files = os.listdir("data/chunks")
    return {"chunks": files}

@app.get("/chunk/{cid}")
def get_chunk(cid: int):
    f = f"data/chunks/chunk_{cid}.parquet"
    if not os.path.exists(f):
        return {"error": "not found"}
    df = pd.read_parquet(f)
    return df.head(50).to_dict()


# Charging Standard Detection API

class ChargingDetectionRequest(BaseModel):
    """充電規格判別リクエスト"""
    voltage: float  # 電圧 (V)
    current: float  # 電流 (A)
    connector_type: Optional[str] = None
    communication_protocol: Optional[str] = None


class CANDataRequest(BaseModel):
    """CANデータからの判別リクエスト"""
    signals: Dict[str, float]  # CANシグナル辞書


@app.get("/")
def root():
    """APIルート"""
    return {
        "message": "Vehicle Log System API",
        "endpoints": {
            "chunks": "/chunks - チャンク一覧",
            "chunk_detail": "/chunk/{id} - チャンク詳細",
            "charging_detect": "/charging/detect - 充電規格判別",
            "charging_standards": "/charging/standards - 対応充電規格一覧",
            "charging_detect_can": "/charging/detect-from-can - CANデータから判別"
        }
    }


@app.post("/charging/detect")
def detect_charging_standard(request: ChargingDetectionRequest):
    """
    充電規格を判別する
    
    電圧、電流などの情報から充電規格を自動判別します。
    """
    try:
        # 電力を計算
        power = (request.voltage * request.current) / 1000.0  # kW
        
        # 充電プロファイルを作成
        profile = ChargingProfile(
            voltage=request.voltage,
            current=request.current,
            power=power,
            connector_type=request.connector_type,
            communication_protocol=request.communication_protocol
        )
        
        # 判別実行
        detector = ChargingStandardDetector()
        result = detector.detect(profile)
        
        return {
            "success": True,
            "detected_standard": result.standard.value,
            "confidence": round(result.confidence, 3),
            "details": result.details,
            "message": f"検出された充電規格: {result.standard.value} (信頼度: {result.confidence:.1%})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/charging/detect-from-can")
def detect_from_can(request: CANDataRequest):
    """
    CANバスデータから充電規格を判別する
    
    CANシグナル（voltage, currentなど）から充電規格を自動判別します。
    """
    try:
        result = detect_from_can_data(request.signals)
        
        return {
            "success": True,
            "detected_standard": result.standard.value,
            "confidence": round(result.confidence, 3),
            "details": result.details,
            "message": f"検出された充電規格: {result.standard.value} (信頼度: {result.confidence:.1%})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/charging/standards")
def list_charging_standards():
    """
    対応している充電規格の一覧を取得する
    
    システムが対応している充電規格のリストと各規格の詳細情報を返します。
    """
    try:
        detector = ChargingStandardDetector()
        standards = detector.list_supported_standards()
        
        return {
            "success": True,
            "count": len(standards),
            "standards": standards,
            "message": f"{len(standards)}種類の充電規格に対応しています"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

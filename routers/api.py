from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
import models
from database import get_db
import yaml

# Prefijo /api para diferenciarlo de los webhooks
router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/calls")
def get_calls(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Obtener lista de llamadas recientes"""
    calls = db.query(models.CallLog).order_by(models.CallLog.id.desc()).offset(skip).limit(limit).all()
    return calls

@router.get("/calls/{call_id}")
def get_call_details(call_id: int, db: Session = Depends(get_db)):
    """Obtener detalles de una llamada específica"""
    call = db.query(models.CallLog).filter(models.CallLog.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return call

@router.get("/search")
def search_calls(phone: str, db: Session = Depends(get_db)):
    """Buscar llamadas por número de teléfono"""
    # Buscar coincidencias parciales
    calls = db.query(models.CallLog).filter(models.CallLog.user_phone.contains(phone)).order_by(models.CallLog.id.desc()).all()
    return calls

@router.get("/openapi.yaml", tags=["Documentacion"])
def get_openapi_yaml(request: Request):
    """Descargar OpenAPI en YAML"""
    openapi_dict = request.app.openapi()
    yaml_str = yaml.safe_dump(openapi_dict, sort_keys=False, allow_unicode=True)
    headers = {"Content-Disposition": 'attachment; filename="openapi.yaml"'}
    return Response(content=yaml_str, media_type="application/x-yaml", headers=headers)
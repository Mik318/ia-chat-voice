from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import json

# Asegurar que las tablas existan
models.Base.metadata.create_all(bind=engine)

def ver_llamadas():
    db = SessionLocal()
    try:
        calls = db.query(models.CallLog).order_by(models.CallLog.id.desc()).all()
        
        print(f"\n📊 Total de llamadas registradas: {len(calls)}")
        
        for call in calls[:5]:  # Mostrar las últimas 5
            print(f"\n📞 ID: {call.id} | SID: {call.call_sid} | Fecha: {call.start_time}")
            print(f"📱 Usuario: {call.user_phone}")
            print("📝 Interacciones:")
            
            if call.interaction_log:
                for interaction in call.interaction_log:
                    # Asegurar que se muestren caracteres especiales correctamente
                    user_text = interaction.get('user', '')
                    ai_text = interaction.get('ai', '')
                    
                    print(f"   👤 User: {user_text}")
                    print(f"   🤖 AI:   {ai_text}")
                    print("   ---")
            else:
                print("   (Sin interacciones registradas)")
            print("="*50)
            
    finally:
        db.close()

if __name__ == "__main__":
    ver_llamadas()

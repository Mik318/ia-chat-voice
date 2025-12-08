#!/bin/bash

echo "🧪 Test de configuración ElevenLabs"
echo "===================================="
echo ""

# Verificar si el archivo .env existe
if [ -f .env ]; then
    echo "✅ Archivo .env encontrado"
    
    # Buscar la configuración de ENABLE_ELEVENLABS
    if grep -q "ENABLE_ELEVENLABS" .env; then
        valor=$(grep "ENABLE_ELEVENLABS" .env | cut -d '=' -f2)
        echo "📋 ENABLE_ELEVENLABS=$valor"
        
        if [ "$valor" = "false" ]; then
            echo "⚠️  ElevenLabs está DESACTIVADO"
            echo "   → Se usará Twilio TTS (Polly.Mia)"
        elif [ "$valor" = "true" ]; then
            echo "✅ ElevenLabs está ACTIVADO"
            echo "   → Se usará ElevenLabs TTS (mejor calidad)"
        else
            echo "⚠️  Valor no reconocido: '$valor'"
            echo "   → Valores válidos: true | false"
        fi
    else
        echo "⚠️  ENABLE_ELEVENLABS no encontrado en .env"
        echo "   → Por defecto: ACTIVADO (true)"
    fi
else
    echo "⚠️ Archivo .env NO encontrado"
    echo "   Copia .env.example a .env y configúralo"
fi

echo ""
echo "📖 Para más información, lee: ELEVENLABS_CONTROL.md"

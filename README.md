# 📱 WhatsApp QR Assistant con OpenAI

## 🎯 Descripción
Aplicación que permite conectar WhatsApp a un asistente de OpenAI mediante código QR. Los usuarios escanean el QR y el asistente responde automáticamente a todos los mensajes.

## ✨ Características
- 📱 **Código QR automático** para vincular WhatsApp
- 🤖 **Integración OpenAI** - Asistente del Estudio Jurídico Villegas Otárola
- 🔄 **Respuestas automáticas** a todos los mensajes
- 📊 **Estadísticas** de mensajes y usuarios
- 🎛️ **Comandos de control**: "activar bot" / "suspender bot"

## 🏗️ Arquitectura
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │ WhatsApp Service│
│   (React)       │───▶│   (FastAPI)     │───▶│   (Node.js)     │
│   Port: 3000    │    │   Port: 8001    │    │   Port: 3001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   MongoDB       │
                       │   Port: 27017   │
                       └─────────────────┘
```

## 🚀 Tecnologías
- **Frontend**: React + Tailwind CSS
- **Backend**: FastAPI (Python)
- **WhatsApp**: Baileys (Node.js)
- **Base de datos**: MongoDB
- **AI**: OpenAI Assistants API

## 📋 Variables de entorno necesarias

### Backend (.env)
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
OPENAI_API_KEY="sk-proj-..."
OPENAI_ASSISTANT_ID="asst_OvGYN1gteWdyeBISsd5FC8Rd"
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL="http://localhost:8001"
```

## 🔧 Instalación Local

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001
```

### 2. Frontend
```bash
cd frontend
yarn install
yarn start
```

### 3. WhatsApp Service
```bash
cd whatsapp-service
yarn install
node whatsapp-service.js
```

### 4. MongoDB
```bash
mongod --port 27017
```

## ✅ Estado del proyecto

### ✅ Funcionalidades completadas:
- [x] Generación automática de QR code
- [x] Conexión con WhatsApp via Baileys
- [x] Integración con OpenAI Assistant
- [x] Respuestas automáticas a mensajes
- [x] Comandos de control del bot
- [x] Interfaz de usuario completa
- [x] Estadísticas de uso
- [x] Persistencia de conversaciones
- [x] Auto-detección de entornos

### ⚠️ Problema actual:
- **Funciona perfectamente en desarrollo**
- **Falla en deploy en Emergent** por problemas de comunicación entre servicios
- **Necesita migración a Railway/Render** para funcionar en producción

## 🎯 Para implementar en producción:

### Railway (Recomendado):
1. Conectar repositorio a Railway
2. Crear 4 services:
   - Frontend (React)
   - Backend (FastAPI)
   - WhatsApp Service (Node.js)
   - MongoDB
3. Configurar variables de entorno
4. Deploy automático

### Render:
Similar a Railway, crear servicios separados para cada componente.

## 💡 Cómo usar:
1. Acceder a la URL del frontend
2. Escanear el código QR con WhatsApp (iPhone)
3. El asistente responderá automáticamente a todos los mensajes
4. Usar "activar bot" / "suspender bot" para controlar

## 🤖 Asistente OpenAI:
- **Nombre**: Estudio Jurídico Villegas Otárola
- **Función**: Asistente legal que responde consultas
- **ID**: asst_OvGYN1gteWdyeBISsd5FC8Rd

## 🔧 Configuraciones especiales:
- **Timeouts optimizados** para entornos de producción
- **Reconexión automática** en caso de desconexión
- **Persistencia de sesiones** WhatsApp
- **Auto-detección de entornos** (desarrollo vs producción)

## 📝 Notas importantes:
- El código funciona 100% en desarrollo
- La única limitación es el deploy en Emergent
- Railway/Render soportan mejor la comunicación entre microservicios
- OpenAI API key incluida y funcional

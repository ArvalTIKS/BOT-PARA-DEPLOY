export const mockData = {
  qrCode: "mock-qr-code-data-for-whatsapp-connection",
  
  connectedUser: {
    name: "Mi Negocio WhatsApp",
    phone: "+1 (555) 123-4567",
    profileImage: null,
    connectedAt: new Date().toISOString()
  },

  connectionStatus: {
    isConnected: false,
    lastSeen: null,
    messagesProcessed: 0,
    status: 'disconnected' // 'disconnected', 'connecting', 'connected'
  },

  assistantConfig: {
    model: "Asistente Personalizado",
    provider: "Tu Asistente IA",
    responseTime: "< 2 segundos",
    availability: "24/7",
    features: [
      "Respuestas inteligentes",
      "Contexto conversacional", 
      "Personalizable",
      "Multiidioma"
    ]
  },

  sampleMessages: [
    {
      id: 1,
      from: "+1 (555) 987-6543",
      message: "¿Están abiertos hoy?",
      timestamp: new Date(Date.now() - 30000).toISOString(),
      response: "¡Hola! Sí, estamos abiertos hoy de 9:00 AM a 6:00 PM. ¿En qué puedo ayudarte?",
      responseTime: 1.2
    },
    {
      id: 2,
      from: "+1 (555) 456-7890",
      message: "¿Cuánto cuesta el servicio?",
      timestamp: new Date(Date.now() - 120000).toISOString(),
      response: "Nuestros precios varían según el servicio específico que necesites. ¿Podrías contarme más sobre lo que buscas para darte información precisa?",
      responseTime: 0.8
    },
    {
      id: 3,
      from: "+1 (555) 321-0987",
      message: "Gracias por la información",
      timestamp: new Date(Date.now() - 300000).toISOString(),
      response: "¡De nada! Estoy aquí para ayudarte en cualquier momento. Si tienes más preguntas, no dudes en escribir. ¡Que tengas un excelente día!",
      responseTime: 1.5
    }
  ]
};
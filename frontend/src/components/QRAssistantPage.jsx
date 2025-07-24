import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import ConnectionStatus from './ConnectionStatus';
import AssistantInfo from './AssistantInfo';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const QRAssistantPage = () => {
  const [connectionMode, setConnectionMode] = useState('instructions'); // 'instructions', 'manual', 'testing'
  const [testMessage, setTestMessage] = useState('');
  const [testPhone, setTestPhone] = useState('56912345678');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    total_messages: 0,
    messages_today: 0, 
    unique_users: 0
  });

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/whatsapp/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const testAssistant = async () => {
    if (!testMessage.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/whatsapp/process-message`, {
        phone_number: testPhone,
        message: testMessage,
        message_id: Date.now().toString(),
        timestamp: Math.floor(Date.now() / 1000)
      });
      
      setResponse(response.data.reply);
      await fetchStats();
    } catch (error) {
      setResponse('Error: No se pudo conectar con el asistente');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-slate-900/20 to-slate-900"></div>
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Asistente WhatsApp
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
            Tu asistente inteligente de OpenAI para responder automáticamente en WhatsApp
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/5 backdrop-blur-xl rounded-xl p-2 border border-white/10">
            <Button
              onClick={() => setConnectionMode('instructions')}
              className={`px-6 py-2 rounded-lg transition-all ${
                connectionMode === 'instructions' 
                ? 'bg-purple-600 text-white' 
                : 'bg-transparent text-gray-300 hover:bg-white/10'
              }`}
            >
              Instrucciones
            </Button>
            <Button
              onClick={() => setConnectionMode('manual')}
              className={`px-6 py-2 rounded-lg transition-all ml-2 ${
                connectionMode === 'manual' 
                ? 'bg-purple-600 text-white' 
                : 'bg-transparent text-gray-300 hover:bg-white/10'
              }`}
            >
              Conexión Manual
            </Button>
            <Button
              onClick={() => setConnectionMode('testing')}
              className={`px-6 py-2 rounded-lg transition-all ml-2 ${
                connectionMode === 'testing' 
                ? 'bg-purple-600 text-white' 
                : 'bg-transparent text-gray-300 hover:bg-white/10'
              }`}
            >
              Probar Asistente
            </Button>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - Main Content */}
          <div className="space-y-6">
            {connectionMode === 'instructions' && (
              <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">Cómo Conectar tu WhatsApp</h2>
                
                <div className="space-y-4">
                  <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-blue-300 mb-2">📱 Método 1: WhatsApp Business API</h3>
                    <p className="text-gray-300 text-sm">
                      Para una integración profesional, contáctanos para configurar WhatsApp Business API oficial.
                    </p>
                  </div>

                  <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-green-300 mb-2">🔗 Método 2: Webhook Integration</h3>
                    <p className="text-gray-300 text-sm">
                      Configuración vía webhook para recibir mensajes automáticamente desde WhatsApp.
                    </p>
                  </div>

                  <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-yellow-300 mb-2">⚡ Método 3: Conexión Manual</h3>
                    <p className="text-gray-300 text-sm">
                      Usa la pestaña "Conexión Manual" para procesar mensajes individualmente.
                    </p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-white/5 rounded-lg">
                  <h4 className="font-semibold text-white mb-2">📞 Contacto para Configuración Profesional</h4>
                  <p className="text-gray-300 text-sm">
                    Para configurar la integración automática completa, contáctanos y te ayudamos con la configuración técnica.
                  </p>
                </div>
              </Card>
            )}

            {connectionMode === 'manual' && (
              <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">Procesamiento Manual</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Número de teléfono del cliente:
                    </label>
                    <Input
                      type="text"
                      value={testPhone}
                      onChange={(e) => setTestPhone(e.target.value)}
                      placeholder="569XXXXXXXX"
                      className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Mensaje recibido del cliente:
                    </label>
                    <Textarea
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      placeholder="Ingresa el mensaje que recibiste del cliente..."
                      className="bg-white/10 border-white/20 text-white placeholder-gray-400 min-h-[100px]"
                    />
                  </div>

                  <Button
                    onClick={testAssistant}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white py-3 text-lg font-semibold rounded-xl"
                  >
                    {loading ? 'Procesando...' : 'Generar Respuesta del Asistente'}
                  </Button>

                  {response && (
                    <div className="mt-4 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                      <h4 className="font-semibold text-green-300 mb-2">Respuesta del Asistente:</h4>
                      <p className="text-white whitespace-pre-wrap">{response}</p>
                      <div className="mt-3 p-2 bg-white/5 rounded text-xs text-gray-400">
                        Copia esta respuesta y envíala al cliente en WhatsApp
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {connectionMode === 'testing' && (
              <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">Probar Asistente</h2>
                
                <div className="space-y-4">
                  <div>
                    <Input
                      type="text"
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      placeholder="Escribe un mensaje de prueba..."
                      className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                    />
                  </div>

                  <Button
                    onClick={testAssistant}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3"
                  >
                    {loading ? 'Enviando...' : 'Probar Asistente'}
                  </Button>

                  {response && (
                    <div className="mt-4 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                      <h4 className="font-semibold text-blue-300 mb-2">Respuesta:</h4>
                      <p className="text-white whitespace-pre-wrap">{response}</p>
                    </div>
                  )}
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <Button
                    onClick={() => setTestMessage('Hola, necesito consulta legal')}
                    className="bg-white/10 hover:bg-white/20 text-white text-sm"
                  >
                    Consulta Legal
                  </Button>
                  <Button
                    onClick={() => setTestMessage('¿Cuáles son sus horarios?')}
                    className="bg-white/10 hover:bg-white/20 text-white text-sm"
                  >
                    Horarios
                  </Button>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column - Assistant Info */}
          <div className="space-y-6">
            <AssistantInfo />
            
            {/* Statistics */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Estadísticas</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-purple-400">{stats.messages_today}</div>
                  <div className="text-sm text-gray-400">Mensajes Hoy</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-blue-400">{stats.total_messages}</div>
                  <div className="text-sm text-gray-400">Total Mensajes</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-green-400">{stats.unique_users}</div>
                  <div className="text-sm text-gray-400">Usuarios Únicos</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-400">100%</div>
                  <div className="text-sm text-gray-400">Asistente Activo</div>
                </div>
              </div>
            </Card>

            {/* Status */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Estado del Sistema</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Backend API</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">Activo</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">OpenAI Assistant</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">Funcionando</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Base de Datos</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">Conectada</Badge>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRAssistantPage;
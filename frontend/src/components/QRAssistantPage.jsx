import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import AssistantInfo from './AssistantInfo';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const QRAssistantPage = () => {
  const [phoneNumber, setPhoneNumber] = useState('+56975855730');
  const [testMessage, setTestMessage] = useState('');
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

  const processMessage = async () => {
    if (!testMessage.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/whatsapp/process-message`, {
        phone_number: phoneNumber.replace('+', ''),
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

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-slate-900/20 to-slate-900"></div>
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Asistente Jurídico WhatsApp
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
            <strong>Estudio Jurídico Villegas Otárola</strong> - Tu asistente legal inteligente
          </p>
        </div>

        {/* Instructions Card */}
        <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">📱 Instrucciones de Uso</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-blue-300">Para activar tu asistente:</h3>
              <div className="space-y-3 text-gray-300">
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">1</Badge>
                  <span>Guarda este número en tus contactos: <strong className="text-white">+56 9 7585 5730</strong></span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">2</Badge>
                  <span>Abre WhatsApp y busca el contacto guardado</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">3</Badge>
                  <span>Envía cualquier mensaje para activar el asistente</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-green-500/20 text-green-300 border-green-500/30">✓</Badge>
                  <span><strong>¡Listo! El asistente responderá automáticamente</strong></span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-green-300">Funcionamiento automático:</h3>
              <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-200 text-sm mb-2">
                  <strong>Una vez activado:</strong>
                </p>
                <ul className="text-green-200 text-sm space-y-1 list-disc ml-4">
                  <li>Cualquier persona que te escriba al WhatsApp recibirá respuesta automática</li>
                  <li>El asistente del Estudio Jurídico responderá 24/7</li>
                  <li>No necesitas hacer nada más</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="mt-6 text-center">
            <Button
              onClick={() => copyToClipboard('+56975855730')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 text-lg font-semibold rounded-xl"
            >
              📋 Copiar Número: +56 9 7585 5730
            </Button>
          </div>
        </Card>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - Test Assistant */}
          <div className="space-y-6">
            <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-6">🧪 Probar Asistente</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Simular mensaje desde:
                  </label>
                  <Input
                    type="text"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+56975855730"
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Mensaje de prueba:
                  </label>
                  <Textarea
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    placeholder="Hola, necesito una consulta legal..."
                    className="bg-white/10 border-white/20 text-white placeholder-gray-400 min-h-[100px]"
                  />
                </div>

                <Button
                  onClick={processMessage}
                  disabled={loading || !testMessage.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white py-3 text-lg font-semibold rounded-xl"
                >
                  {loading ? 'Generando Respuesta...' : '🤖 Generar Respuesta del Asistente'}
                </Button>

                {response && (
                  <div className="mt-4 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-green-300">Respuesta del Asistente:</h4>
                      <Button
                        onClick={() => copyToClipboard(response)}
                        size="sm"
                        className="bg-green-600/20 hover:bg-green-600/30 text-green-300"
                      >
                        📋 Copiar
                      </Button>
                    </div>
                    <p className="text-white whitespace-pre-wrap">{response}</p>
                    <div className="mt-3 p-2 bg-white/5 rounded text-xs text-gray-400">
                      Esta es la respuesta que recibirían tus clientes automáticamente
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3">
                <Button
                  onClick={() => setTestMessage('Hola, necesito una consulta legal urgente')}
                  className="bg-white/10 hover:bg-white/20 text-white text-sm"
                >
                  📋 Consulta Legal
                </Button>
                <Button
                  onClick={() => setTestMessage('¿Cuál es su ubicación y horarios?')}
                  className="bg-white/10 hover:bg-white/20 text-white text-sm"
                >
                  📍 Ubicación
                </Button>
              </div>
            </Card>
          </div>

          {/* Right Column - Info & Stats */}
          <div className="space-y-6">
            <AssistantInfo />
            
            {/* Statistics */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">📊 Estadísticas del Asistente</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-purple-400">{stats.messages_today}</div>
                  <div className="text-sm text-gray-400">Consultas Hoy</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-blue-400">{stats.total_messages}</div>
                  <div className="text-sm text-gray-400">Total Consultas</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-green-400">{stats.unique_users}</div>
                  <div className="text-sm text-gray-400">Clientes Únicos</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-400">100%</div>
                  <div className="text-sm text-gray-400">Disponibilidad</div>
                </div>
              </div>
            </Card>

            {/* Status */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">⚡ Estado del Sistema</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Asistente Legal</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">✅ Activo</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">OpenAI GPT-4</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">✅ Funcionando</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Base de Datos</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">✅ Conectada</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Respuestas Automáticas</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">✅ Habilitadas</Badge>
                </div>
              </div>
            </Card>

            {/* Contact Info */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">🏛️ Estudio Jurídico</h3>
              <div className="space-y-2 text-gray-300 text-sm">
                <p><strong>Nombre:</strong> Villegas Otárola Abogados</p>
                <p><strong>Ubicación:</strong> Presidente Julio Roca 1030, Punta Arenas</p>
                <p><strong>Especialidades:</strong> Derecho Civil, Penal y de Familia</p>
                <p><strong>Cobertura:</strong> Magallanes, Metropolitana y online</p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRAssistantPage;
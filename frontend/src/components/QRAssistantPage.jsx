import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import QRCodeDisplay from './QRCodeDisplay';
import ConnectionStatus from './ConnectionStatus';
import AssistantInfo from './AssistantInfo';
import axios from 'axios';

// Auto-detect environment and use appropriate backend URL
const getBackendUrl = () => {
  // If explicitly set, use it
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // Auto-detect based on current URL
  const currentHost = window.location.hostname;
  const currentProtocol = window.location.protocol;
  
  // If on emergent.host domain (deployed), use same domain
  if (currentHost.includes('emergent.host')) {
    return `${currentProtocol}//${currentHost}`;
  }
  
  // Default to localhost for development
  return 'http://localhost:8001';
};

const API_BASE = getBackendUrl();

// Debug logging
console.log('Current URL:', window.location.href);
console.log('API_BASE:', API_BASE);
console.log('Environment:', process.env.NODE_ENV);

const QRAssistantPage = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [qrCode, setQrCode] = useState(null);
  const [connectedUser, setConnectedUser] = useState(null);
  const [messageCount, setMessageCount] = useState(0);
  const [stats, setStats] = useState({
    total_messages: 0,
    messages_today: 0, 
    unique_users: 0
  });
  const [loading, setLoading] = useState(false);

  // Fetch QR code
  const fetchQRCode = async () => {
    try {
      console.log('Fetching QR from:', `${API_BASE}/api/whatsapp/qr`);
      const response = await axios.get(`${API_BASE}/api/whatsapp/qr`);
      console.log('QR response:', response.data);
      
      if (response.data.qr) {
        setQrCode(response.data.qr);
        console.log('QR code set successfully');
      } else {
        setQrCode(null);
        console.log('No QR in response');
      }
    } catch (error) {
      console.error('Error fetching QR code:', error);
      console.error('Request URL:', `${API_BASE}/api/whatsapp/qr`);
      setQrCode(null);
    }
  };

  // Check WhatsApp connection status
  const checkConnectionStatus = async () => {
    try {
      console.log('Checking status at:', `${API_BASE}/api/whatsapp/status`);
      const response = await axios.get(`${API_BASE}/api/whatsapp/status`);
      const data = response.data;
      
      console.log('Status response:', data);
      
      if (data.connected) {
        setConnectionStatus('connected');
        setConnectedUser(data.user);
        setQrCode(null);
      } else if (data.hasQR) {
        setConnectionStatus('disconnected');
        setConnectedUser(null);
        console.log('QR available, fetching...');
        await fetchQRCode();
      } else {
        setConnectionStatus('disconnected');
        setConnectedUser(null);
        setQrCode(null);
        console.log('No QR available yet');
      }
    } catch (error) {
      console.error('Error checking connection status:', error);
      console.error('Request URL:', `${API_BASE}/api/whatsapp/status`);
      setConnectionStatus('error');
    }
  };

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/whatsapp/stats`);
      setStats(response.data);
      setMessageCount(response.data.messages_today);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Initial load and polling
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await checkConnectionStatus();
      await fetchStats();
      setLoading(false);
    };

    loadData();

    // Poll every 3 seconds for status updates
    const interval = setInterval(async () => {
      await checkConnectionStatus();
      if (connectionStatus === 'connected') {
        await fetchStats();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Refresh connection
  const handleRefresh = async () => {
    setLoading(true);
    await checkConnectionStatus();
    await fetchStats();
    setLoading(false);
  };

  if (loading && connectionStatus === 'disconnected') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white">Cargando plataforma...</p>
        </div>
      </div>
    );
  }

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
            Escanea el código QR para activar tu <strong>Asistente Legal Personalizado</strong>
          </p>
        </div>

        {/* Main Content */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - QR Code & Status */}
          <div className="space-y-6">
            <Card className="p-8 bg-white/5 backdrop-blur-xl border-white/10 shadow-2xl">
              <ConnectionStatus 
                status={connectionStatus}
                connectedUser={connectedUser}
                messageCount={messageCount}
              />
              
              {connectionStatus !== 'connected' && (
                <>
                  <Separator className="my-6 bg-white/10" />
                  <QRCodeDisplay qrCode={qrCode} status={connectionStatus} />
                </>
              )}

              {connectionStatus === 'connected' && (
                <>
                  <Separator className="my-6 bg-white/10" />
                  <div className="text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-white">¡Conectado!</h3>
                    <p className="text-gray-300">Tu asistente del <strong>Estudio Jurídico Villegas Otárola</strong> está activo</p>
                    
                    <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4 mt-4">
                      <p className="text-green-300 font-semibold">🏛️ Asistente Jurídico Activo</p>
                      <p className="text-green-200 text-sm">Responderá automáticamente a TODOS los mensajes de WhatsApp</p>
                    </div>
                  </div>
                </>
              )}

              {connectionStatus === 'error' && (
                <>
                  <Separator className="my-6 bg-white/10" />
                  <div className="text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-white">Iniciando Servicio WhatsApp</h3>
                    <p className="text-gray-300">El servicio se está inicializando. Espera unos segundos.</p>
                    
                    <div className="flex gap-3 justify-center mt-6">
                      <Button 
                        onClick={handleRefresh} 
                        variant="outline" 
                        className="bg-white/10 border-white/20 text-white hover:bg-white/20"
                        disabled={loading}
                      >
                        {loading ? 'Verificando...' : 'Verificar Estado'}
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </Card>
          </div>

          {/* Right Column - Assistant Info */}
          <div className="space-y-6">
            <AssistantInfo />
            
            {/* Statistics */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">📊 Automatización Total</h3>
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
                  <div className="text-sm text-gray-400">Clientes Atendidos</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-400">
                    {connectionStatus === 'connected' ? '100%' : '0%'}
                  </div>
                  <div className="text-sm text-gray-400">Automatización</div>
                </div>
              </div>
            </Card>

            {/* Instructions */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">📱 Instrucciones (iPhone)</h3>
              <div className="space-y-3 text-sm text-gray-300">
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">1</Badge>
                  <span>Abre WhatsApp en tu iPhone</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">2</Badge>
                  <span>Ve a Configuración → Dispositivos Vinculados</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">3</Badge>
                  <span>Toca "Vincular un dispositivo"</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">4</Badge>
                  <span>Escanea el código QR que aparece arriba</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-green-500/20 text-green-300 border-green-500/30">✅</Badge>
                  <span><strong>¡LISTO! Cuando te escriban, tu asistente responderá automáticamente</strong></span>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg">
                <p className="text-blue-300 text-sm font-semibold mb-1">🤖 Estudio Jurídico Villegas Otárola</p>
                <p className="text-blue-200 text-xs">
                  Una vez conectado, tu asistente legal responderá automáticamente a todas las consultas 
                  sin necesidad de tu intervención. Perfecto para atender clientes 24/7.
                </p>
              </div>
            </Card>

            {/* Important Note */}
            <Card className="p-6 bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30">
              <h3 className="text-lg font-bold text-orange-300 mb-3">⚠️ Importante</h3>
              <p className="text-orange-200 text-sm">
                <strong>Para recibir muchos mensajes diarios:</strong> Una vez conectado, 
                tu asistente procesará TODOS los mensajes automáticamente. 
                No necesitas hacer nada más.
              </p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRAssistantPage;
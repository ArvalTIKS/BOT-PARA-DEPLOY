import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { mockData } from '../utils/mock';
import QRCodeDisplay from './QRCodeDisplay';
import ConnectionStatus from './ConnectionStatus';
import AssistantInfo from './AssistantInfo';

const QRAssistantPage = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [qrCode, setQrCode] = useState(null);
  const [connectedUser, setConnectedUser] = useState(null);
  const [messageCount, setMessageCount] = useState(0);

  useEffect(() => {
    // Simulate QR code generation
    if (connectionStatus === 'disconnected') {
      setQrCode(mockData.qrCode);
    }
  }, [connectionStatus]);

  const handleTestConnection = () => {
    setConnectionStatus('connecting');
    
    setTimeout(() => {
      setConnectionStatus('connected');
      setConnectedUser(mockData.connectedUser);
      setQrCode(null);
    }, 2000);
  };

  const handleDisconnect = () => {
    setConnectionStatus('disconnected');
    setConnectedUser(null);
    setMessageCount(0);
    setQrCode(mockData.qrCode);
  };

  const simulateMessage = () => {
    setMessageCount(prev => prev + 1);
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
            Conecta tu WhatsApp y activa tu asistente inteligente de OpenAI para responder automáticamente a tus clientes
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
                    <p className="text-gray-300">Tu asistente está activo y respondiendo mensajes</p>
                    
                    <div className="flex gap-3 justify-center mt-6">
                      <Button onClick={simulateMessage} variant="outline" className="bg-white/10 border-white/20 text-white hover:bg-white/20">
                        Simular Mensaje
                      </Button>
                      <Button onClick={handleDisconnect} variant="outline" className="bg-red-500/20 border-red-500/30 text-red-300 hover:bg-red-500/30">
                        Desconectar
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </Card>

            {/* Test Button (only show if disconnected) */}
            {connectionStatus === 'disconnected' && (
              <div className="text-center">
                <Button 
                  onClick={handleTestConnection}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-3 text-lg font-semibold rounded-xl shadow-lg transition-all duration-300 transform hover:scale-105"
                >
                  Probar Conexión (Demo)
                </Button>
                <p className="text-sm text-gray-400 mt-2">Para pruebas de la interfaz</p>
              </div>
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
                  <div className="text-2xl font-bold text-purple-400">{messageCount}</div>
                  <div className="text-sm text-gray-400">Mensajes Procesados</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg">
                  <div className="text-2xl font-bold text-blue-400">
                    {connectionStatus === 'connected' ? '100%' : '0%'}
                  </div>
                  <div className="text-sm text-gray-400">Disponibilidad</div>
                </div>
              </div>
            </Card>

            {/* Instructions */}
            <Card className="p-6 bg-white/5 backdrop-blur-xl border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Instrucciones</h3>
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
                  <span>Escanea el código QR que aparece arriba</span>
                </div>
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-300 border-purple-500/30">4</Badge>
                  <span>¡Listo! Tu asistente responderá automáticamente</span>
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
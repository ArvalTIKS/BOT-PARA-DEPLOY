import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle, XCircle, Smartphone, RefreshCw, AlertTriangle, Bot, Wifi, WifiOff, LogOut } from 'lucide-react';

const ClientLanding = () => {
  const { unique_url } = useParams();
  const [clientData, setClientData] = useState(null);
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchClientData();
    // Auto refresh every 10 seconds
    const interval = setInterval(fetchClientData, 10000);
    return () => clearInterval(interval);
  }, [unique_url]);

  const fetchClientData = async () => {
    try {
      setError(null);
      
      // Fetch client status
      const statusResponse = await axios.get(`${backendUrl}/api/client/${unique_url}/status`);
      setClientData(statusResponse.data);
      
      // Fetch QR code if not connected
      if (!statusResponse.data.client.connected) {
        const qrResponse = await axios.get(`${backendUrl}/api/client/${unique_url}/qr`);
        setQrCode(qrResponse.data);
      } else {
        setQrCode(null);
      }
      
    } catch (error) {
      console.error('Error fetching client data:', error);
      if (error.response?.status === 404) {
        setError('Cliente no encontrado. Verifica que el enlace sea correcto.');
      } else {
        setError('Error conectando con el servidor. Por favor intenta nuevamente.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchClientData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando tu asistente...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="max-w-md mx-auto text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Oops! Algo salió mal</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Intentar nuevamente
          </button>
        </div>
      </div>
    );
  }

  const isConnected = clientData?.client?.connected;
  const isActive = clientData?.client?.status === 'active';

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Bot className="w-12 h-12 text-green-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Asistente WhatsApp
              </h1>
              <p className="text-xl text-gray-600">
                {clientData?.client?.name}
              </p>
            </div>
          </div>
        </div>

        {/* Status Card */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Estado del Asistente</h2>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Service Status */}
              <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                <div className={`p-2 rounded-full mr-3 ${isActive ? 'bg-green-100' : 'bg-red-100'}`}>
                  {isActive ? 
                    <CheckCircle className="w-6 h-6 text-green-600" /> : 
                    <XCircle className="w-6 h-6 text-red-600" />
                  }
                </div>
                <div>
                  <p className="font-medium text-gray-900">Servicio</p>
                  <p className={`text-sm ${isActive ? 'text-green-600' : 'text-red-600'}`}>
                    {isActive ? 'Activo' : 'Inactivo'}
                  </p>
                </div>
              </div>

              {/* WhatsApp Connection */}
              <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                <div className={`p-2 rounded-full mr-3 ${isConnected ? 'bg-green-100' : 'bg-yellow-100'}`}>
                  {isConnected ? 
                    <Wifi className="w-6 h-6 text-green-600" /> : 
                    <WifiOff className="w-6 h-6 text-yellow-600" />
                  }
                </div>
                <div>
                  <p className="font-medium text-gray-900">WhatsApp</p>
                  <p className={`text-sm ${isConnected ? 'text-green-600' : 'text-yellow-600'}`}>
                    {isConnected ? 'Conectado' : 'Desconectado'}
                  </p>
                </div>
              </div>
            </div>

            {/* Status Message */}
            {isConnected ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <p className="text-green-800 font-medium">
                    ¡Tu asistente está activo y respondiendo mensajes automáticamente!
                  </p>
                </div>
                <p className="text-green-700 text-sm mt-2">
                  Los usuarios pueden enviar mensajes a tu WhatsApp y recibirán respuestas automáticas de tu asistente IA.
                </p>
              </div>
            ) : !isActive ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <XCircle className="w-5 h-5 text-red-600 mr-2" />
                  <p className="text-red-800 font-medium">
                    Servicio inactivo
                  </p>
                </div>
                <p className="text-red-700 text-sm mt-2">
                  El servicio está desactivado. Contacta al administrador para activarlo.
                </p>
              </div>
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center">
                  <Smartphone className="w-5 h-5 text-yellow-600 mr-2" />
                  <p className="text-yellow-800 font-medium">
                    Listo para conectar WhatsApp
                  </p>
                </div>
                <p className="text-yellow-700 text-sm mt-2">
                  Escanea el código QR de abajo con tu WhatsApp para activar tu asistente.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* QR Code Section */}
        {!isConnected && isActive && (
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-2xl shadow-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Escanea para Conectar
              </h3>
              
              {qrCode?.qr ? (
                <div className="space-y-4">
                  <div className="bg-white p-4 rounded-lg border border-gray-200 inline-block">
                    <img 
                      src={qrCode.qr} 
                      alt="QR Code" 
                      className="w-64 h-64 mx-auto"
                    />
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-2">
                    <p className="font-medium">Instrucciones:</p>
                    <ol className="text-left space-y-1">
                      <li>1. Abre WhatsApp en tu teléfono</li>
                      <li>2. Ve a Menú → Dispositivos vinculados</li>
                      <li>3. Toca "Vincular un dispositivo"</li>
                      <li>4. Escanea este código QR</li>
                    </ol>
                  </div>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-blue-800 text-xs">
                      <strong>Importante:</strong> Solo se puede conectar un teléfono por asistente. 
                      Una vez conectado, este código QR no funcionará en otros dispositivos.
                    </p>
                  </div>
                </div>
              ) : qrCode?.connected ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    ¡WhatsApp Conectado!
                  </h4>
                  <p className="text-gray-600 mb-6">
                    Tu asistente está funcionando y listo para atender mensajes automáticamente.
                  </p>
                  
                  <div className="space-y-4">
                    <button
                      onClick={handleDisconnectWhatsApp}
                      className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Desvincular WhatsApp
                    </button>
                    
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-yellow-800 text-xs">
                        <strong>Nota:</strong> Al desvincular, el dispositivo se eliminará completamente 
                        de tu lista de "Dispositivos vinculados" en WhatsApp y necesitarás escanear 
                        un nuevo código QR para volver a conectar.
                      </p>
                    </div>
                  </div>
                </div>
              ) : qrCode?.error ? (
                <div className="text-center py-8">
                  <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">{qrCode.error}</p>
                  <button
                    onClick={handleRefresh}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Intentar nuevamente
                  </button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Generando código QR...</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-gray-500 text-sm">
            ¿Necesitas ayuda? Contacta: <a href="mailto:contacto@tiks.cl" className="text-blue-600 hover:text-blue-800">contacto@tiks.cl</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ClientLanding;
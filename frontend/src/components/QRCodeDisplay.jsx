import React from 'react';
import { Loader2 } from 'lucide-react';

const QRCodeDisplay = ({ qrCode, status }) => {
  if (status === 'connecting') {
    return (
      <div className="text-center py-8">
        <div className="inline-flex items-center gap-3 text-white">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span className="text-lg font-medium">Conectando...</span>
        </div>
        <p className="text-gray-400 mt-2">Estableciendo conexión con WhatsApp</p>
      </div>
    );
  }

  if (!qrCode) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <p className="text-gray-400">Generando código QR...</p>
      </div>
    );
  }

  return (
    <div className="text-center">
      <h3 className="text-2xl font-bold text-white mb-6">
        Escanea este código para activar tu asistente
      </h3>
      
      {/* QR Code Container */}
      <div className="relative inline-block">
        <div className="p-6 bg-white rounded-2xl shadow-2xl">
          <div className="w-64 h-64 bg-gray-100 rounded-lg flex items-center justify-center relative overflow-hidden">
            {/* Mock QR Code Pattern */}
            <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-800 to-black opacity-90"></div>
            <div className="relative z-10 grid grid-cols-8 gap-1 w-full h-full p-2">
              {Array.from({ length: 64 }, (_, i) => (
                <div
                  key={i}
                  className={`w-full h-full ${
                    Math.random() > 0.5 ? 'bg-black' : 'bg-white'
                  } rounded-sm`}
                />
              ))}
            </div>
            
            {/* Corner markers */}
            <div className="absolute top-2 left-2 w-8 h-8 border-4 border-black bg-white"></div>
            <div className="absolute top-2 right-2 w-8 h-8 border-4 border-black bg-white"></div>
            <div className="absolute bottom-2 left-2 w-8 h-8 border-4 border-black bg-white"></div>
          </div>
        </div>
        
        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-2xl blur-xl -z-10 scale-110"></div>
      </div>

      <div className="mt-6 space-y-2">
        <p className="text-gray-300 text-lg">
          Abre WhatsApp → Dispositivos Vinculados → Vincular Dispositivo
        </p>
        <p className="text-sm text-gray-400">
          El código expira en 60 segundos
        </p>
      </div>

      {/* Animated border */}
      <div className="mt-4">
        <div className="w-full bg-white/10 rounded-full h-1 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-purple-600 to-blue-600 rounded-full animate-pulse"></div>
        </div>
      </div>
    </div>
  );
};

export default QRCodeDisplay;
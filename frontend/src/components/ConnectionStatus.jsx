import React from 'react';
import { Badge } from './ui/badge';

const ConnectionStatus = ({ status, connectedUser, messageCount }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500/20 text-green-300 border-green-500/30',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ),
          text: 'Conectado',
          pulse: true
        };
      case 'connecting':
        return {
          color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
          icon: (
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ),
          text: 'Conectando...',
          pulse: false
        };
      default:
        return {
          color: 'bg-red-500/20 text-red-300 border-red-500/30',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          text: 'Desconectado',
          pulse: false
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Estado de Conexión</h2>
        <Badge 
          variant="outline" 
          className={`${statusConfig.color} px-3 py-1 text-sm font-medium ${
            statusConfig.pulse ? 'animate-pulse' : ''
          }`}
        >
          <span className="flex items-center gap-2">
            {statusConfig.icon}
            {statusConfig.text}
          </span>
        </Badge>
      </div>

      {status === 'connected' && connectedUser && (
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-white">{connectedUser.name}</h3>
              <p className="text-sm text-gray-400">{connectedUser.phone}</p>
            </div>
          </div>
          
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-white/5 rounded">
              <div className="text-lg font-bold text-blue-400">{messageCount}</div>
              <div className="text-xs text-gray-400">Mensajes hoy</div>
            </div>
            <div className="text-center p-2 bg-white/5 rounded">
              <div className="text-lg font-bold text-green-400">Online</div>
              <div className="text-xs text-gray-400">Asistente activo</div>
            </div>
          </div>
        </div>
      )}

      {status === 'disconnected' && (
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="text-center text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
            </svg>
            <p className="text-sm">Esperando conexión WhatsApp</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle, User, Mail, Key, Bot, Trash2, Power, PowerOff, Plus, Edit, Send } from 'lucide-react';

const AdminPanel = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditEmailForm, setShowEditEmailForm] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [newEmail, setNewEmail] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    openai_api_key: '',
    openai_assistant_id: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/admin/clients`);
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${backendUrl}/api/admin/clients`, formData);
      
      // Reset form
      setFormData({
        name: '',
        email: '',
        openai_api_key: '',
        openai_assistant_id: ''
      });
      setShowAddForm(false);
      
      // Refresh clients list
      await fetchClients();
      
      alert('✅ Cliente creado exitosamente! Email enviado.');
    } catch (error) {
      console.error('Error creating client:', error);
      alert('❌ Error creando cliente: ' + (error.response?.data?.detail || error.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  };

  const toggleClient = async (clientId, action) => {
    try {
      setLoading(true); // Prevent multiple simultaneous calls
      
      await axios.put(`${backendUrl}/api/admin/clients/${clientId}/toggle`, {
        action: action
      });
      
      // Update the specific client in the current state instead of refetching all
      setClients(prevClients => 
        prevClients.map(client => 
          client.id === clientId 
            ? { ...client, status: action === 'connect' ? 'active' : 'inactive' }
            : client
        )
      );
      
      // Refresh clients list after a brief delay to ensure backend consistency
      setTimeout(async () => {
        await fetchClients();
      }, 1000);
      
      alert(`✅ Cliente ${action === 'connect' ? 'conectado' : 'desconectado'} exitosamente!`);
    } catch (error) {
      console.error(`Error ${action}ing client:`, error);
      alert(`❌ Error ${action === 'connect' ? 'conectando' : 'desconectando'} cliente`);
      // Revert the optimistic update on error
      await fetchClients();
    } finally {
      setLoading(false);
    }
  };

  const deleteClient = async (clientId, clientName) => {
    if (window.confirm(`¿Estás seguro de eliminar al cliente "${clientName}"? Esta acción no se puede deshacer.`)) {
      try {
        await axios.delete(`${backendUrl}/api/admin/clients/${clientId}`);
        await fetchClients();
        alert('✅ Cliente eliminado exitosamente!');
      } catch (error) {
        console.error('Error deleting client:', error);
        alert('❌ Error eliminando cliente');
      }
    }
  };

  const updateClientEmail = async (e) => {
    e.preventDefault();
    if (!editingClient || !newEmail) return;

    try {
      await axios.put(`${backendUrl}/api/admin/clients/${editingClient.id}/update-email`, {
        new_email: newEmail
      });
      
      setShowEditEmailForm(false);
      setEditingClient(null);
      setNewEmail('');
      await fetchClients();
      
      alert('✅ Email actualizado exitosamente!');
    } catch (error) {
      console.error('Error updating email:', error);
      alert('❌ Error actualizando email');
    }
  };

  const resendEmail = async (clientId, clientEmail, clientName) => {
    if (window.confirm(`¿Reenviar email de invitación a ${clientEmail}?`)) {
      try {
        await axios.post(`${backendUrl}/api/admin/clients/${clientId}/resend-email`);
        alert(`✅ Email reenviado exitosamente a ${clientEmail}`);
      } catch (error) {
        console.error('Error resending email:', error);
        alert('❌ Error reenviando email');
      }
    }
  };

  const openEditEmailForm = (client) => {
    setEditingClient(client);
    setNewEmail(client.email);
    setShowEditEmailForm(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'inactive': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'inactive': return <PowerOff className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  if (loading && clients.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Bot className="w-8 h-8 text-blue-600 mr-3" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Panel de Administración</h1>
                  <p className="text-gray-600">Plataforma WhatsApp Multi-Tenant</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-5 h-5 mr-2" />
                Agregar Cliente
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{clients.length}</div>
              <div className="text-sm text-blue-600">Total Clientes</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {clients.filter(c => c.status === 'active').length}
              </div>
              <div className="text-sm text-green-600">Clientes Activos</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {clients.filter(c => c.connected_phone).length}
              </div>
              <div className="text-sm text-yellow-600">WhatsApp Conectados</div>
            </div>
          </div>
        </div>

        {/* Add Client Form Modal */}
        {showAddForm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Agregar Nuevo Cliente</h3>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nombre del Cliente</label>
                    <div className="mt-1 relative">
                      <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Ej: Bufete Legal XYZ"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email del Cliente</label>
                    <div className="mt-1 relative">
                      <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="cliente@empresa.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">API Key OpenAI</label>
                    <div className="mt-1 relative">
                      <Key className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="password"
                        required
                        value={formData.openai_api_key}
                        onChange={(e) => setFormData({...formData, openai_api_key: e.target.value})}
                        className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="sk-..."
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Assistant ID OpenAI</label>
                    <div className="mt-1 relative">
                      <Bot className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        required
                        value={formData.openai_assistant_id}
                        onChange={(e) => setFormData({...formData, openai_assistant_id: e.target.value})}
                        className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="asst_..."
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowAddForm(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
                    >
                      {loading ? 'Creando...' : 'Crear y Enviar Email'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Edit Email Form Modal */}
        {showEditEmailForm && editingClient && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Actualizar Email</h3>
                  <button
                    onClick={() => setShowEditEmailForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
                
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Cliente:</strong> {editingClient.name}<br/>
                    <strong>Email actual:</strong> {editingClient.email}
                  </p>
                </div>
                
                <form onSubmit={updateClientEmail} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nuevo Email</label>
                    <div className="mt-1 relative">
                      <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="email"
                        required
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="nuevo@email.com"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowEditEmailForm(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                    >
                      Actualizar Email
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Clients Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Clientes Registrados</h2>
          </div>
          
          {clients.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No hay clientes registrados aún.</p>
              <p className="text-sm">Agrega tu primer cliente usando el botón de arriba.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      WhatsApp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Puerto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      URL Landing
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clients.map((client, index) => (
                    <tr key={`${client.id}-${client.status}-${index}`} className="hover:bg-gray-50">{/* Unique key with status to force re-render */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{client.name}</div>
                          <div className="text-sm text-gray-500">{client.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(client.status)}`}>
                          {getStatusIcon(client.status)}
                          <span className="ml-1 capitalize">{client.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {client.connected_phone ? (
                          <span className="text-green-600">+{client.connected_phone}</span>
                        ) : (
                          <span className="text-gray-400">No conectado</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        :{client.whatsapp_port}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <a 
                          href={`/client/${client.unique_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          /{client.unique_url}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex flex-wrap gap-1">
                          {client.status === 'active' ? (
                            <button
                              onClick={() => toggleClient(client.id, 'disconnect')}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                            >
                              <PowerOff className="w-3 h-3 mr-1" />
                              Desconectar
                            </button>
                          ) : (
                            <button
                              onClick={() => toggleClient(client.id, 'connect')}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200"
                            >
                              <Power className="w-3 h-3 mr-1" />
                              Conectar
                            </button>
                          )}
                          
                          <button
                            onClick={() => openEditEmailForm(client)}
                            className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200"
                          >
                            <Edit className="w-3 h-3 mr-1" />
                            Editar Email
                          </button>
                          
                          <button
                            onClick={() => resendEmail(client.id, client.email, client.name)}
                            className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-purple-700 bg-purple-100 hover:bg-purple-200"
                          >
                            <Send className="w-3 h-3 mr-1" />
                            Reenviar Email
                          </button>
                          
                          <button
                            onClick={() => deleteClient(client.id, client.name)}
                            className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
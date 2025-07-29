#!/usr/bin/env python3
"""
Comprehensive Backend Testing for WhatsApp + OpenAI Platform
Tests all backend APIs and service connectivity
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
import time

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return "http://localhost:8001"
    return "http://localhost:8001"

BACKEND_URL = get_backend_url()
WHATSAPP_SERVICE_URL = "http://localhost:3001"

class BackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.whatsapp_service_url = WHATSAPP_SERVICE_URL
        self.test_results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    async def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            async with self.session.get(f"{self.backend_url}/api/", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Basic API Connectivity", 
                        True, 
                        f"API is running: {data.get('message', 'No message')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Basic API Connectivity", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}")
            return False

    async def test_whatsapp_service_connectivity(self):
        """Test WhatsApp service connectivity"""
        try:
            async with self.session.get(f"{self.whatsapp_service_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "WhatsApp Service Connectivity", 
                        True, 
                        f"Service status: {data.get('status', 'unknown')}, Connected: {data.get('connected', False)}"
                    )
                    return True
                else:
                    self.log_test(
                        "WhatsApp Service Connectivity", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("WhatsApp Service Connectivity", False, f"Connection error: {str(e)}")
            return False

    async def test_status_endpoints(self):
        """Test basic status endpoints"""
        # Test GET status
        try:
            async with self.session.get(f"{self.backend_url}/api/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "GET Status Endpoint", 
                        True, 
                        f"Retrieved {len(data)} status checks"
                    )
                else:
                    self.log_test(
                        "GET Status Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("GET Status Endpoint", False, f"Error: {str(e)}")

        # Test POST status
        try:
            test_data = {"client_name": "test_backend_client"}
            async with self.session.post(
                f"{self.backend_url}/api/status", 
                json=test_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "POST Status Endpoint", 
                        True, 
                        f"Created status check with ID: {data.get('id', 'unknown')}"
                    )
                else:
                    self.log_test(
                        "POST Status Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("POST Status Endpoint", False, f"Error: {str(e)}")

    async def test_whatsapp_qr_endpoint(self):
        """Test WhatsApp QR code endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/whatsapp/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    self.log_test(
                        "WhatsApp QR Endpoint", 
                        True, 
                        f"QR endpoint accessible, QR available: {has_qr}"
                    )
                else:
                    self.log_test(
                        "WhatsApp QR Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("WhatsApp QR Endpoint", False, f"Error: {str(e)}")

    async def test_whatsapp_status_endpoint(self):
        """Test WhatsApp status endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/whatsapp/status", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    connected = data.get('connected', False)
                    has_qr = data.get('hasQR', False)
                    self.log_test(
                        "WhatsApp Status Endpoint", 
                        True, 
                        f"Connected: {connected}, Has QR: {has_qr}"
                    )
                else:
                    self.log_test(
                        "WhatsApp Status Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("WhatsApp Status Endpoint", False, f"Error: {str(e)}")

    async def test_whatsapp_stats_endpoint(self):
        """Test WhatsApp statistics endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/whatsapp/stats", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    total_messages = data.get('total_messages', 0)
                    messages_today = data.get('messages_today', 0)
                    unique_users = data.get('unique_users', 0)
                    self.log_test(
                        "WhatsApp Stats Endpoint", 
                        True, 
                        f"Total messages: {total_messages}, Today: {messages_today}, Users: {unique_users}"
                    )
                else:
                    self.log_test(
                        "WhatsApp Stats Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("WhatsApp Stats Endpoint", False, f"Error: {str(e)}")

    async def test_message_processing_endpoint(self):
        """Test message processing with OpenAI integration"""
        try:
            test_message = {
                "phone_number": "5491234567890",
                "message": "Hola, ¿cómo están? Necesito información sobre sus servicios.",
                "message_id": "test_msg_001",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/process-message",
                json=test_message,
                timeout=30  # OpenAI can take time
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    has_reply = data.get('reply') is not None
                    success = data.get('success', False)
                    reply_length = len(data.get('reply', '')) if has_reply else 0
                    
                    self.log_test(
                        "Message Processing Endpoint", 
                        True, 
                        f"Success: {success}, Has reply: {has_reply}, Reply length: {reply_length}"
                    )
                else:
                    self.log_test(
                        "Message Processing Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Message Processing Endpoint", False, f"Error: {str(e)}")

    async def test_send_message_endpoint(self):
        """Test send message endpoint"""
        try:
            test_message = {
                "phone_number": "5491234567890",
                "message": "Este es un mensaje de prueba del sistema."
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/send-message",
                json=test_message,
                timeout=15
            ) as response:
                # This might fail if WhatsApp is not connected, but endpoint should be accessible
                if response.status in [200, 400]:  # 400 is expected if not connected
                    data = await response.json()
                    self.log_test(
                        "Send Message Endpoint", 
                        True, 
                        f"Endpoint accessible, Response: {data}"
                    )
                else:
                    self.log_test(
                        "Send Message Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Send Message Endpoint", False, f"Error: {str(e)}")

    async def test_conversation_history_endpoint(self):
        """Test conversation history endpoint"""
        try:
            test_phone = "5491234567890"
            async with self.session.get(
                f"{self.backend_url}/api/whatsapp/messages/{test_phone}",
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    messages = data.get('messages', [])
                    self.log_test(
                        "Conversation History Endpoint", 
                        True, 
                        f"Retrieved {len(messages)} messages for phone {test_phone}"
                    )
                else:
                    self.log_test(
                        "Conversation History Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Conversation History Endpoint", False, f"Error: {str(e)}")

    async def test_baileys_service_health(self):
        """Test Baileys WhatsApp service health and status"""
        try:
            async with self.session.get(f"{self.whatsapp_service_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('status', 'unknown')
                    connected = data.get('connected', False)
                    timestamp = data.get('timestamp', 'unknown')
                    
                    self.log_test(
                        "Baileys Service Health Check", 
                        True, 
                        f"Status: {status}, Connected: {connected}, Timestamp: {timestamp}"
                    )
                else:
                    self.log_test(
                        "Baileys Service Health Check", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Baileys Service Health Check", False, f"Error: {str(e)}")

    async def test_baileys_qr_generation(self):
        """Test Baileys QR code generation"""
        try:
            async with self.session.get(f"{self.whatsapp_service_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    has_raw = data.get('raw') is not None
                    
                    self.log_test(
                        "Baileys QR Code Generation", 
                        True, 
                        f"QR available: {has_qr}, Raw QR data: {has_raw}"
                    )
                else:
                    self.log_test(
                        "Baileys QR Code Generation", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Baileys QR Code Generation", False, f"Error: {str(e)}")

    async def test_baileys_status_endpoint(self):
        """Test Baileys status endpoint with user info"""
        try:
            async with self.session.get(f"{self.whatsapp_service_url}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    connected = data.get('connected', False)
                    has_qr = data.get('hasQR', False)
                    user = data.get('user')
                    
                    user_info = "No user info" if not user else f"User: {user.get('name', 'Unknown')}"
                    
                    self.log_test(
                        "Baileys Status Endpoint", 
                        True, 
                        f"Connected: {connected}, Has QR: {has_qr}, {user_info}"
                    )
                else:
                    self.log_test(
                        "Baileys Status Endpoint", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Baileys Status Endpoint", False, f"Error: {str(e)}")

    async def test_bot_activation_command(self):
        """Test bot activation command processing"""
        try:
            activation_message = {
                "phone_number": "5491234567890",
                "message": "activar bot",
                "message_id": "test_activate_001",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/process-message",
                json=activation_message,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    reply = data.get('reply', '')
                    
                    # Check if the reply contains activation confirmation
                    contains_activation = 'activado' in reply.lower() or 'bot' in reply.lower()
                    
                    self.log_test(
                        "Bot Activation Command", 
                        True, 
                        f"Success: {success}, Contains activation response: {contains_activation}, Reply: {reply[:100]}..."
                    )
                else:
                    self.log_test(
                        "Bot Activation Command", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Bot Activation Command", False, f"Error: {str(e)}")

    async def test_bot_suspension_command(self):
        """Test bot suspension command processing"""
        try:
            suspension_message = {
                "phone_number": "5491234567890",
                "message": "suspender bot",
                "message_id": "test_suspend_001",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/process-message",
                json=suspension_message,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    reply = data.get('reply', '')
                    
                    # Check if the reply contains suspension confirmation
                    contains_suspension = 'suspendido' in reply.lower() or 'bot' in reply.lower()
                    
                    self.log_test(
                        "Bot Suspension Command", 
                        True, 
                        f"Success: {success}, Contains suspension response: {contains_suspension}, Reply: {reply[:100]}..."
                    )
                else:
                    self.log_test(
                        "Bot Suspension Command", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Bot Suspension Command", False, f"Error: {str(e)}")

    async def test_openai_assistant_integration(self):
        """Test OpenAI Assistant integration with specific legal query"""
        try:
            legal_query = {
                "phone_number": "5491234567890",
                "message": "¿Qué servicios ofrece el Estudio Jurídico Villegas Otárola?",
                "message_id": "test_legal_001",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/process-message",
                json=legal_query,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    reply = data.get('reply', '')
                    
                    # Check if reply mentions the law firm
                    mentions_firm = 'villegas' in reply.lower() and 'otárola' in reply.lower()
                    mentions_legal = 'jurídico' in reply.lower() or 'legal' in reply.lower()
                    
                    self.log_test(
                        "OpenAI Assistant Integration", 
                        True, 
                        f"Success: {success}, Mentions firm: {mentions_firm}, Legal context: {mentions_legal}, Reply length: {len(reply)}"
                    )
                else:
                    self.log_test(
                        "OpenAI Assistant Integration", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("OpenAI Assistant Integration", False, f"Error: {str(e)}")

    async def test_admin_routes(self):
        """Test admin panel routes"""
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Admin - Get All Clients", 
                        True, 
                        f"Retrieved {len(data)} clients successfully"
                    )
                else:
                    self.log_test(
                        "Admin - Get All Clients", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Admin - Get All Clients", False, f"Error: {str(e)}")

    async def test_client_routes(self):
        """Test client landing page routes"""
        # Test with a known client URL
        test_client_url = "e2d7bce6"  # Cliente Prueba
        
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{test_client_url}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    client_name = data.get('client', {}).get('name', 'Unknown')
                    self.log_test(
                        "Client - Landing Status", 
                        True, 
                        f"Client status retrieved for {client_name}"
                    )
                else:
                    self.log_test(
                        "Client - Landing Status", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Client - Landing Status", False, f"Error: {str(e)}")
        
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{test_client_url}/qr", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    self.log_test(
                        "Client - Landing QR", 
                        True, 
                        f"QR endpoint accessible, Has QR: {has_qr}"
                    )
                else:
                    self.log_test(
                        "Client - Landing QR", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Client - Landing QR", False, f"Error: {str(e)}")

    async def test_database_integration(self):
        """Test MongoDB database integration"""
        try:
            # Test stats endpoint which queries database
            async with self.session.get(f"{self.backend_url}/api/whatsapp/stats", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    total_messages = data.get('total_messages', 0)
                    messages_today = data.get('messages_today', 0)
                    unique_users = data.get('unique_users', 0)
                    self.log_test(
                        "Database Integration", 
                        True, 
                        f"Database queries working - Total: {total_messages}, Today: {messages_today}, Users: {unique_users}"
                    )
                else:
                    self.log_test(
                        "Database Integration", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Database Integration", False, f"Error: {str(e)}")

    # ========== CONSOLIDATED WHATSAPP SYSTEM TESTS ==========
    
    async def test_consolidated_phone_connected(self):
        """Test consolidated phone connection notification endpoint"""
        try:
            test_data = {
                "phone_number": "5491234567890",
                "user_info": {
                    "name": "Test User",
                    "pushname": "Test"
                }
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/consolidated/phone-connected",
                json=test_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    message = data.get('message', '')
                    self.log_test(
                        "Consolidated - Phone Connected", 
                        True, 
                        f"Success: {success}, Message: {message}"
                    )
                else:
                    self.log_test(
                        "Consolidated - Phone Connected", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Consolidated - Phone Connected", False, f"Error: {str(e)}")

    async def test_consolidated_process_message(self):
        """Test consolidated message processing endpoint"""
        try:
            test_message = {
                "phone_number": "5491234567890",
                "message": "Hola, necesito información sobre servicios legales consolidados",
                "message_id": "consolidated_test_001",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/consolidated/process-message",
                json=test_message,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    has_reply = data.get('reply') is not None
                    reply_length = len(data.get('reply', '')) if has_reply else 0
                    
                    self.log_test(
                        "Consolidated - Process Message", 
                        True, 
                        f"Success: {success}, Has reply: {has_reply}, Reply length: {reply_length}"
                    )
                else:
                    self.log_test(
                        "Consolidated - Process Message", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Consolidated - Process Message", False, f"Error: {str(e)}")

    async def test_consolidated_status(self):
        """Test consolidated system status endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/consolidated/status", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    whatsapp_connected = data.get('whatsapp_connected', False)
                    active_clients = data.get('active_clients', 0)
                    phone_connections = data.get('phone_connections', 0)
                    
                    self.log_test(
                        "Consolidated - System Status", 
                        True, 
                        f"WhatsApp Connected: {whatsapp_connected}, Active Clients: {active_clients}, Phone Connections: {phone_connections}"
                    )
                else:
                    self.log_test(
                        "Consolidated - System Status", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Consolidated - System Status", False, f"Error: {str(e)}")

    async def test_consolidated_clients(self):
        """Test consolidated active clients endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/consolidated/clients", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    active_clients = data.get('active_clients', [])
                    total_active = data.get('total_active', 0)
                    
                    self.log_test(
                        "Consolidated - Active Clients", 
                        True, 
                        f"Total Active Clients: {total_active}, Clients retrieved: {len(active_clients)}"
                    )
                else:
                    self.log_test(
                        "Consolidated - Active Clients", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Consolidated - Active Clients", False, f"Error: {str(e)}")

    async def test_consolidated_associate_phone(self):
        """Test consolidated manual phone association endpoint"""
        try:
            # First get a client ID from admin endpoint
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        client_id = clients[0]['id']
                        
                        test_data = {
                            "phone_number": "5491234567890",
                            "client_id": client_id
                        }
                        
                        async with self.session.post(
                            f"{self.backend_url}/api/consolidated/associate-phone",
                            json=test_data,
                            timeout=15
                        ) as assoc_response:
                            if assoc_response.status == 200:
                                data = await assoc_response.json()
                                success = data.get('success', False)
                                client_name = data.get('client_name', 'Unknown')
                                
                                self.log_test(
                                    "Consolidated - Associate Phone", 
                                    True, 
                                    f"Success: {success}, Associated with: {client_name}"
                                )
                            else:
                                self.log_test(
                                    "Consolidated - Associate Phone", 
                                    False, 
                                    f"HTTP {assoc_response.status}",
                                    await assoc_response.text()
                                )
                    else:
                        self.log_test(
                            "Consolidated - Associate Phone", 
                            False, 
                            "No clients available for association test"
                        )
                else:
                    self.log_test(
                        "Consolidated - Associate Phone", 
                        False, 
                        f"Could not get clients: HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test("Consolidated - Associate Phone", False, f"Error: {str(e)}")

    async def test_consolidated_qr(self):
        """Test consolidated QR code endpoint"""
        try:
            async with self.session.get(f"{self.backend_url}/api/consolidated/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    has_raw = data.get('raw') is not None
                    
                    self.log_test(
                        "Consolidated - QR Code", 
                        True, 
                        f"QR available: {has_qr}, Raw QR data: {has_raw}"
                    )
                else:
                    self.log_test(
                        "Consolidated - QR Code", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Consolidated - QR Code", False, f"Error: {str(e)}")

    async def test_admin_client_toggle_consolidated(self):
        """Test admin client toggle with consolidated system"""
        try:
            # Get first client
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        client_id = clients[0]['id']
                        client_name = clients[0]['name']
                        
                        # Test connect action
                        toggle_data = {"action": "connect"}
                        async with self.session.put(
                            f"{self.backend_url}/api/admin/clients/{client_id}/toggle",
                            json=toggle_data,
                            timeout=15
                        ) as toggle_response:
                            if toggle_response.status == 200:
                                data = await toggle_response.json()
                                message = data.get('message', '')
                                status = data.get('status', '')
                                
                                self.log_test(
                                    "Admin - Client Toggle (Consolidated)", 
                                    True, 
                                    f"Client: {client_name}, Status: {status}, Message: {message}"
                                )
                            else:
                                self.log_test(
                                    "Admin - Client Toggle (Consolidated)", 
                                    False, 
                                    f"HTTP {toggle_response.status}",
                                    await toggle_response.text()
                                )
                    else:
                        self.log_test(
                            "Admin - Client Toggle (Consolidated)", 
                            False, 
                            "No clients available for toggle test"
                        )
                else:
                    self.log_test(
                        "Admin - Client Toggle (Consolidated)", 
                        False, 
                        f"Could not get clients: HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test("Admin - Client Toggle (Consolidated)", False, f"Error: {str(e)}")

    async def test_client_landing_consolidated(self):
        """Test client landing pages with consolidated system"""
        # Test with a known client URL
        test_client_url = "e2d7bce6"  # Cliente Prueba
        
        try:
            # Test status endpoint
            async with self.session.get(f"{self.backend_url}/api/client/{test_client_url}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    client_name = data.get('client', {}).get('name', 'Unknown')
                    connected = data.get('client', {}).get('connected', False)
                    registered = data.get('client', {}).get('registered', False)
                    
                    self.log_test(
                        "Client Landing - Status (Consolidated)", 
                        True, 
                        f"Client: {client_name}, Connected: {connected}, Registered: {registered}"
                    )
                else:
                    self.log_test(
                        "Client Landing - Status (Consolidated)", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Client Landing - Status (Consolidated)", False, f"Error: {str(e)}")
        
        try:
            # Test QR endpoint
            async with self.session.get(f"{self.backend_url}/api/client/{test_client_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    connected = data.get('connected', False)
                    client_name = data.get('client_name', 'Unknown')
                    
                    self.log_test(
                        "Client Landing - QR (Consolidated)", 
                        True, 
                        f"Client: {client_name}, Has QR: {has_qr}, Connected: {connected}"
                    )
                else:
                    self.log_test(
                        "Client Landing - QR (Consolidated)", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Client Landing - QR (Consolidated)", False, f"Error: {str(e)}")

    async def test_whatsapp_service_stability(self):
        """Test WhatsApp service stability on port 3001"""
        try:
            # Test multiple rapid requests to check stability
            stable_requests = 0
            total_requests = 5
            
            for i in range(total_requests):
                try:
                    async with self.session.get(f"{self.whatsapp_service_url}/health", timeout=5) as response:
                        if response.status == 200:
                            stable_requests += 1
                        await asyncio.sleep(0.5)  # Small delay between requests
                except:
                    pass
            
            stability_rate = (stable_requests / total_requests) * 100
            
            self.log_test(
                "WhatsApp Service Stability", 
                stability_rate >= 80,  # Consider stable if 80%+ requests succeed
                f"Stability rate: {stability_rate:.1f}% ({stable_requests}/{total_requests} requests succeeded)"
            )
            
        except Exception as e:
            self.log_test("WhatsApp Service Stability", False, f"Error: {str(e)}")

    async def test_multi_tenant_openai_integration(self):
        """Test OpenAI integration with multiple client credentials"""
        try:
            # Get clients to test different OpenAI configurations
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        # Test with first client
                        client = clients[0]
                        
                        test_message = {
                            "phone_number": "5491234567890",
                            "message": f"Hola, soy un cliente de {client['name']}. ¿Pueden ayudarme?",
                            "message_id": f"multi_tenant_test_{client['id']}",
                            "timestamp": int(time.time())
                        }
                        
                        async with self.session.post(
                            f"{self.backend_url}/api/consolidated/process-message",
                            json=test_message,
                            timeout=30
                        ) as msg_response:
                            if msg_response.status == 200:
                                data = await msg_response.json()
                                success = data.get('success', False)
                                has_reply = data.get('reply') is not None
                                
                                self.log_test(
                                    "Multi-Tenant OpenAI Integration", 
                                    True, 
                                    f"Client: {client['name']}, Success: {success}, Has Reply: {has_reply}"
                                )
                            else:
                                self.log_test(
                                    "Multi-Tenant OpenAI Integration", 
                                    False, 
                                    f"HTTP {msg_response.status}",
                                    await msg_response.text()
                                )
                    else:
                        self.log_test(
                            "Multi-Tenant OpenAI Integration", 
                            False, 
                            "No clients available for multi-tenant test"
                        )
                else:
                    self.log_test(
                        "Multi-Tenant OpenAI Integration", 
                        False, 
                        f"Could not get clients: HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test("Multi-Tenant OpenAI Integration", False, f"Error: {str(e)}")

    async def test_error_handling(self):
        """Test error handling with invalid requests"""
        # Test invalid message processing
        try:
            invalid_message = {
                "phone_number": "",  # Invalid empty phone
                "message": "",       # Invalid empty message
                "message_id": "test_invalid",
                "timestamp": "invalid_timestamp"  # Invalid timestamp
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/whatsapp/process-message",
                json=invalid_message,
                timeout=10
            ) as response:
                # Should handle gracefully
                if response.status in [200, 400, 422]:  # Various acceptable error responses
                    self.log_test(
                        "Error Handling - Invalid Message", 
                        True, 
                        f"Handled invalid input gracefully with HTTP {response.status}"
                    )
                else:
                    self.log_test(
                        "Error Handling - Invalid Message", 
                        False, 
                        f"Unexpected HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Error Handling - Invalid Message", False, f"Error: {str(e)}")

        # Test non-existent endpoint
        try:
            async with self.session.get(f"{self.backend_url}/api/nonexistent", timeout=5) as response:
                if response.status == 404:
                    self.log_test(
                        "Error Handling - 404 Endpoint", 
                        True, 
                        "Correctly returns 404 for non-existent endpoint"
                    )
                else:
                    self.log_test(
                        "Error Handling - 404 Endpoint", 
                        False, 
                        f"Expected 404, got HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test("Error Handling - 404 Endpoint", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("BACKEND TESTING - CONSOLIDATED WHATSAPP SYSTEM")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print(f"WhatsApp Service URL: {self.whatsapp_service_url}")
        print("=" * 80)
        print()

        # Test basic connectivity first
        backend_connected = await self.test_basic_connectivity()
        whatsapp_connected = await self.test_whatsapp_service_connectivity()
        
        if not backend_connected:
            print("❌ CRITICAL: Backend API is not accessible. Stopping tests.")
            return
            
        # Test WhatsApp service stability
        await self.test_whatsapp_service_stability()
        
        # ========== CONSOLIDATED SYSTEM TESTS ==========
        print("\n🔄 TESTING CONSOLIDATED WHATSAPP SYSTEM...")
        await self.test_consolidated_status()
        await self.test_consolidated_clients()
        await self.test_consolidated_qr()
        await self.test_consolidated_phone_connected()
        await self.test_consolidated_process_message()
        await self.test_consolidated_associate_phone()
        
        # ========== ADMIN PANEL WITH CONSOLIDATED SYSTEM ==========
        print("\n👨‍💼 TESTING ADMIN PANEL WITH CONSOLIDATED SYSTEM...")
        await self.test_admin_routes()
        await self.test_admin_client_toggle_consolidated()
        
        # ========== CLIENT LANDING PAGES WITH CONSOLIDATED SYSTEM ==========
        print("\n🌐 TESTING CLIENT LANDING PAGES WITH CONSOLIDATED SYSTEM...")
        await self.test_client_routes()
        await self.test_client_landing_consolidated()
        
        # ========== MULTI-TENANT OPENAI INTEGRATION ==========
        print("\n🤖 TESTING MULTI-TENANT OPENAI INTEGRATION...")
        await self.test_multi_tenant_openai_integration()
        
        # ========== LEGACY ENDPOINT COMPATIBILITY ==========
        print("\n🔄 TESTING LEGACY ENDPOINT COMPATIBILITY...")
        await self.test_status_endpoints()
        await self.test_whatsapp_qr_endpoint()
        await self.test_whatsapp_status_endpoint()
        await self.test_whatsapp_stats_endpoint()
        await self.test_message_processing_endpoint()
        await self.test_send_message_endpoint()
        await self.test_conversation_history_endpoint()
        
        # ========== DATABASE AND ERROR HANDLING ==========
        print("\n💾 TESTING DATABASE AND ERROR HANDLING...")
        await self.test_database_integration()
        await self.test_error_handling()
        
        # ========== WHATSAPP SERVICE TESTS ==========
        print("\n📱 TESTING WHATSAPP SERVICE...")
        await self.test_baileys_service_health()
        await self.test_baileys_qr_generation()
        await self.test_baileys_status_endpoint()
        
        # ========== BOT COMMAND TESTS ==========
        print("\n🤖 TESTING BOT COMMANDS...")
        await self.test_bot_activation_command()
        await self.test_bot_suspension_command()
        
        # ========== OPENAI ASSISTANT INTEGRATION ==========
        print("\n🧠 TESTING OPENAI ASSISTANT INTEGRATION...")
        await self.test_openai_assistant_integration()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
            print()
        
        print("CRITICAL ISSUES:")
        critical_issues = []
        for result in self.test_results:
            if not result['success']:
                if 'Connectivity' in result['test'] or 'Processing' in result['test']:
                    critical_issues.append(result['test'])
        
        if critical_issues:
            for issue in critical_issues:
                print(f"🚨 {issue}")
        else:
            print("✅ No critical issues found")
        
        print("=" * 80)

async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
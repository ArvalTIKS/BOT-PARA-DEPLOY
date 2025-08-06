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

    async def test_individual_service_architecture(self):
        """Test complete individual WhatsApp service architecture"""
        print("\n🏗️ TESTING INDIVIDUAL SERVICE ARCHITECTURE...")
        
        # Step 1: Create a new client
        test_client_data = {
            "name": "Test Individual Client",
            "email": "test.individual@example.com",
            "openai_api_key": "sk-test-individual-key",
            "openai_assistant_id": "asst_test_individual"
        }
        
        created_client = None
        try:
            async with self.session.post(
                f"{self.backend_url}/api/admin/clients",
                json=test_client_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    created_client = await response.json()
                    client_id = created_client['id']
                    client_port = created_client['whatsapp_port']
                    unique_url = created_client['unique_url']
                    
                    self.log_test(
                        "Individual Architecture - Client Creation",
                        True,
                        f"Created client {created_client['name']} with port {client_port} and URL {unique_url}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Client Creation",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return
        except Exception as e:
            self.log_test("Individual Architecture - Client Creation", False, f"Error: {str(e)}")
            return
        
        if not created_client:
            return
            
        client_id = created_client['id']
        client_port = created_client['whatsapp_port']
        unique_url = created_client['unique_url']
        
        # Step 2: Activate individual service
        try:
            toggle_data = {"action": "connect"}
            async with self.session.put(
                f"{self.backend_url}/api/admin/clients/{client_id}/toggle",
                json=toggle_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Individual Architecture - Service Activation",
                        True,
                        f"Service activation response: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Service Activation",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Service Activation", False, f"Error: {str(e)}")
        
        # Step 3: Wait for service to start and test connectivity
        await asyncio.sleep(10)  # Give service time to start
        
        try:
            individual_service_url = f"http://localhost:{client_port}"
            async with self.session.get(f"{individual_service_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Individual Architecture - Service Connectivity",
                        True,
                        f"Individual service running on port {client_port}, status: {data.get('status', 'unknown')}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Service Connectivity",
                        False,
                        f"HTTP {response.status} on port {client_port}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Service Connectivity", False, f"Error connecting to port {client_port}: {str(e)}")
        
        # Step 4: Test QR generation from individual service
        try:
            individual_service_url = f"http://localhost:{client_port}"
            async with self.session.get(f"{individual_service_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    self.log_test(
                        "Individual Architecture - QR Generation",
                        True,
                        f"QR endpoint accessible on port {client_port}, QR available: {has_qr}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - QR Generation",
                        False,
                        f"HTTP {response.status} on port {client_port}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - QR Generation", False, f"Error: {str(e)}")
        
        # Step 5: Test client landing page access
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    client_name = data.get('client', {}).get('name', 'Unknown')
                    self.log_test(
                        "Individual Architecture - Landing Page Status",
                        True,
                        f"Landing page accessible for {client_name}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Landing Page Status",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Landing Page Status", False, f"Error: {str(e)}")
        
        # Step 6: Test QR via landing page
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    self.log_test(
                        "Individual Architecture - Landing Page QR",
                        True,
                        f"QR accessible via landing page, QR available: {has_qr}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Landing Page QR",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Landing Page QR", False, f"Error: {str(e)}")
        
        # Step 7: Test OpenAI integration with client-specific credentials
        try:
            test_message = {
                "phone_number": "5491234567890",
                "message": f"Hola, soy un cliente de {created_client['name']}. ¿Pueden ayudarme?",
                "message_id": f"individual_test_{client_id}",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/client/{client_id}/process-message",
                json=test_message,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    has_reply = data.get('reply') is not None
                    
                    self.log_test(
                        "Individual Architecture - OpenAI Integration",
                        True,
                        f"Message processing success: {success}, Has reply: {has_reply}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - OpenAI Integration",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - OpenAI Integration", False, f"Error: {str(e)}")
        
        # Step 8: Test service status via admin
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients/{client_id}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    service_status = data.get('service', {}).get('status', 'unknown')
                    self.log_test(
                        "Individual Architecture - Admin Service Status",
                        True,
                        f"Admin reports service status: {service_status}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Admin Service Status",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Admin Service Status", False, f"Error: {str(e)}")
        
        # Step 9: Test service deactivation
        try:
            toggle_data = {"action": "disconnect"}
            async with self.session.put(
                f"{self.backend_url}/api/admin/clients/{client_id}/toggle",
                json=toggle_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Individual Architecture - Service Deactivation",
                        True,
                        f"Service deactivation response: {data.get('message', 'Success')}"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Service Deactivation",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Service Deactivation", False, f"Error: {str(e)}")
        
        # Step 10: Cleanup - delete test client
        try:
            async with self.session.delete(f"{self.backend_url}/api/admin/clients/{client_id}", timeout=15) as response:
                if response.status == 200:
                    self.log_test(
                        "Individual Architecture - Cleanup",
                        True,
                        "Test client deleted successfully"
                    )
                else:
                    self.log_test(
                        "Individual Architecture - Cleanup",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Individual Architecture - Cleanup", False, f"Error: {str(e)}")

    async def test_chromium_configuration(self):
        """Test system Chromium availability and configuration"""
        try:
            # Check if system Chromium exists
            import os
            chromium_path = '/usr/bin/chromium'
            chromium_exists = os.path.exists(chromium_path)
            
            # Check EMERGENT_ENV
            emergent_env = os.environ.get('EMERGENT_ENV', 'preview')
            
            self.log_test(
                "Chromium Configuration Check",
                chromium_exists,
                f"System Chromium at {chromium_path}: {'EXISTS' if chromium_exists else 'NOT FOUND'}, EMERGENT_ENV: {emergent_env}"
            )
            
        except Exception as e:
            self.log_test("Chromium Configuration Check", False, f"Error: {str(e)}")

    async def test_mobile_landing_page_access(self):
        """Test mobile access to client landing pages - specific to user's issue"""
        print("\n📱 TESTING MOBILE LANDING PAGE ACCESS...")
        
        # First, let's check if there are any clients in the database
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if not clients:
                        self.log_test(
                            "Mobile Landing - Database Check",
                            False,
                            "No clients found in database. This explains why users get 'Error conectando con el servidor'"
                        )
                        return
                    else:
                        self.log_test(
                            "Mobile Landing - Database Check",
                            True,
                            f"Found {len(clients)} clients in database"
                        )
                        
                        # Test each client's landing page endpoints
                        for client in clients:
                            unique_url = client.get('unique_url')
                            client_name = client.get('name', 'Unknown')
                            
                            # Test status endpoint
                            try:
                                async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/status", timeout=10) as status_response:
                                    if status_response.status == 200:
                                        status_data = await status_response.json()
                                        self.log_test(
                                            f"Mobile Landing - Status ({client_name})",
                                            True,
                                            f"Status endpoint accessible for {client_name}"
                                        )
                                    else:
                                        self.log_test(
                                            f"Mobile Landing - Status ({client_name})",
                                            False,
                                            f"HTTP {status_response.status} - This could cause 'Error conectando con el servidor'",
                                            await status_response.text()
                                        )
                            except Exception as e:
                                self.log_test(f"Mobile Landing - Status ({client_name})", False, f"Connection error: {str(e)}")
                            
                            # Test QR endpoint
                            try:
                                async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/qr", timeout=15) as qr_response:
                                    if qr_response.status == 200:
                                        qr_data = await qr_response.json()
                                        has_qr = qr_data.get('qr') is not None
                                        self.log_test(
                                            f"Mobile Landing - QR ({client_name})",
                                            True,
                                            f"QR endpoint accessible, QR available: {has_qr}"
                                        )
                                    else:
                                        self.log_test(
                                            f"Mobile Landing - QR ({client_name})",
                                            False,
                                            f"HTTP {qr_response.status} - This could cause QR loading issues",
                                            await qr_response.text()
                                        )
                            except Exception as e:
                                self.log_test(f"Mobile Landing - QR ({client_name})", False, f"Connection error: {str(e)}")
                else:
                    self.log_test(
                        "Mobile Landing - Database Check",
                        False,
                        f"Cannot access admin clients endpoint: HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Mobile Landing - Database Check", False, f"Error: {str(e)}")

    async def test_url_configuration_fix(self):
        """Test the critical URL configuration fix for production deployment"""
        print("\n🚨 TESTING CRITICAL URL CONFIGURATION FIX...")
        
        # Test 1: Verify url_detection module is working
        try:
            # Import and test url_detection module
            import sys
            sys.path.append('/app/backend')
            from url_detection import get_backend_base_url, get_environment_info
            
            backend_url = get_backend_base_url()
            env_info = get_environment_info()
            
            # Check if we're getting production URL instead of localhost
            is_production_url = 'localhost' not in backend_url and 'emergent' in backend_url
            
            self.log_test(
                "URL Detection - Backend URL",
                is_production_url,
                f"Backend URL: {backend_url}, Environment: {env_info['environment']}, Fallback used: {env_info['fallback_used']}"
            )
            
        except Exception as e:
            self.log_test("URL Detection - Backend URL", False, f"Error importing url_detection: {str(e)}")
        
        # Test 2: Test /api/admin/regenerate-services endpoint
        try:
            async with self.session.post(f"{self.backend_url}/api/admin/regenerate-services", timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    regenerated = data.get('regenerated', 0)
                    failed = data.get('failed', 0)
                    
                    self.log_test(
                        "Admin - Regenerate Services Endpoint",
                        True,
                        f"Regenerated: {regenerated}, Failed: {failed}, Details: {len(data.get('details', []))}"
                    )
                else:
                    self.log_test(
                        "Admin - Regenerate Services Endpoint",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Admin - Regenerate Services Endpoint", False, f"Error: {str(e)}")
        
        # Test 3: Verify WhatsApp services are using dynamic URLs
        try:
            # Get all clients first
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        # Test first client's service for URL configuration
                        client = clients[0]
                        client_id = client['id']
                        client_port = client.get('whatsapp_port', 3002)
                        
                        # Check if service directory exists and contains correct URL
                        service_dir = f"/app/whatsapp-services/client-{client_id}"
                        service_file = f"{service_dir}/service.js"
                        
                        try:
                            with open(service_file, 'r') as f:
                                service_content = f.read()
                                
                            # Check if service uses process.env.FASTAPI_URL instead of hardcoded localhost
                            uses_env_var = 'process.env.FASTAPI_URL' in service_content
                            no_hardcoded_localhost = 'http://localhost:8001' not in service_content
                            
                            self.log_test(
                                "Service Generation - Dynamic URLs",
                                uses_env_var and no_hardcoded_localhost,
                                f"Uses env var: {uses_env_var}, No hardcoded localhost: {no_hardcoded_localhost}"
                            )
                            
                        except FileNotFoundError:
                            self.log_test(
                                "Service Generation - Dynamic URLs",
                                False,
                                f"Service file not found: {service_file}"
                            )
                        except Exception as e:
                            self.log_test(
                                "Service Generation - Dynamic URLs",
                                False,
                                f"Error reading service file: {str(e)}"
                            )
                    else:
                        self.log_test(
                            "Service Generation - Dynamic URLs",
                            False,
                            "No clients found to test service generation"
                        )
                else:
                    self.log_test(
                        "Service Generation - Dynamic URLs",
                        False,
                        f"Could not get clients: HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test("Service Generation - Dynamic URLs", False, f"Error: {str(e)}")
        
        # Test 4: Test client status and QR endpoints with production URLs
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    if clients:
                        client = clients[0]
                        unique_url = client['unique_url']
                        
                        # Test client status endpoint
                        async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/status", timeout=10) as status_response:
                            if status_response.status == 200:
                                self.log_test(
                                    "Client Endpoints - Status",
                                    True,
                                    f"Status endpoint accessible for client {unique_url}"
                                )
                            else:
                                self.log_test(
                                    "Client Endpoints - Status",
                                    False,
                                    f"HTTP {status_response.status}",
                                    await status_response.text()
                                )
                        
                        # Test client QR endpoint
                        async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/qr", timeout=15) as qr_response:
                            if qr_response.status == 200:
                                qr_data = await qr_response.json()
                                has_qr = qr_data.get('qr') is not None
                                self.log_test(
                                    "Client Endpoints - QR",
                                    True,
                                    f"QR endpoint accessible, QR available: {has_qr}"
                                )
                            else:
                                self.log_test(
                                    "Client Endpoints - QR",
                                    False,
                                    f"HTTP {qr_response.status}",
                                    await qr_response.text()
                                )
                    else:
                        self.log_test("Client Endpoints - Status", False, "No clients found")
                        self.log_test("Client Endpoints - QR", False, "No clients found")
        except Exception as e:
            self.log_test("Client Endpoints - Status", False, f"Error: {str(e)}")
            self.log_test("Client Endpoints - QR", False, f"Error: {str(e)}")

    async def test_gonzalo_specific_qr_issue(self):
        """URGENT: Test Gonzalo's specific QR generation issue"""
        print("\n🚨 URGENT: TESTING GONZALO'S QR GENERATION ISSUE...")
        
        # Gonzalo's specific details from user request
        gonzalo_client = {
            "id": "165f3fae-8e54-413e-b4f8-4f602ab20e07",
            "unique_url": "ccc7bffd", 
            "name": "Gonzalo",
            "port": 3005
        }
        
        print(f"Testing client: {gonzalo_client['name']} (ID: {gonzalo_client['id']}, Port: {gonzalo_client['port']})")
        
        # Step 1: Check if Gonzalo's service is actually running
        try:
            individual_service_url = f"http://localhost:{gonzalo_client['port']}"
            async with self.session.get(f"{individual_service_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        f"Gonzalo Service - Process Running",
                        True,
                        f"Service responds on port {gonzalo_client['port']}, status: {data.get('status', 'unknown')}"
                    )
                else:
                    self.log_test(
                        f"Gonzalo Service - Process Running",
                        False,
                        f"HTTP {response.status} on port {gonzalo_client['port']} - SERVICE NOT RUNNING",
                        await response.text()
                    )
                    return  # Can't continue if service isn't running
        except Exception as e:
            self.log_test(f"Gonzalo Service - Process Running", False, f"Connection error to port {gonzalo_client['port']}: {str(e)}")
            return
        
        # Step 2: Test direct QR generation from individual service
        try:
            async with self.session.get(f"{individual_service_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    has_raw = data.get('raw') is not None
                    
                    self.log_test(
                        f"Gonzalo Service - Direct QR Generation",
                        has_qr,
                        f"QR available: {has_qr}, Raw QR data: {has_raw}. {'✅ QR WORKING' if has_qr else '❌ NO QR - This is the problem!'}"
                    )
                else:
                    self.log_test(
                        f"Gonzalo Service - Direct QR Generation",
                        False,
                        f"HTTP {response.status} - QR endpoint failed",
                        await response.text()
                    )
        except Exception as e:
            self.log_test(f"Gonzalo Service - Direct QR Generation", False, f"Error: {str(e)}")
        
        # Step 3: Test WhatsApp status from individual service
        try:
            async with self.session.get(f"{individual_service_url}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    connected = data.get('connected', False)
                    has_qr = data.get('hasQR', False)
                    user = data.get('user')
                    
                    self.log_test(
                        f"Gonzalo Service - WhatsApp Status",
                        True,
                        f"Connected: {connected}, Has QR: {has_qr}, User: {user}. {'⚠️ Should have QR if not connected' if not connected and not has_qr else '✅ Status OK'}"
                    )
                else:
                    self.log_test(
                        f"Gonzalo Service - WhatsApp Status",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test(f"Gonzalo Service - WhatsApp Status", False, f"Error: {str(e)}")
        
        # Step 4: Test QR via backend API (client landing page route)
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{gonzalo_client['unique_url']}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    error = data.get('error')
                    
                    self.log_test(
                        f"Gonzalo Backend - Landing Page QR",
                        has_qr,
                        f"QR via backend: {has_qr}, Error: {error}. {'✅ Backend QR OK' if has_qr else '❌ Backend QR failed'}"
                    )
                else:
                    self.log_test(
                        f"Gonzalo Backend - Landing Page QR",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test(f"Gonzalo Backend - Landing Page QR", False, f"Error: {str(e)}")
        
        # Step 5: Test client status via backend
        try:
            async with self.session.get(f"{self.backend_url}/api/client/{gonzalo_client['unique_url']}/status", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    client_status = data.get('client', {})
                    whatsapp_status = data.get('whatsapp', {})
                    
                    self.log_test(
                        f"Gonzalo Backend - Client Status",
                        True,
                        f"Client connected: {client_status.get('connected', False)}, WhatsApp connected: {whatsapp_status.get('connected', False)}"
                    )
                else:
                    self.log_test(
                        f"Gonzalo Backend - Client Status",
                        False,
                        f"HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test(f"Gonzalo Backend - Client Status", False, f"Error: {str(e)}")
        
        # Step 6: Check if Chromium is available (this was mentioned as a potential issue)
        try:
            import os
            chromium_path = '/usr/bin/chromium'
            chromium_exists = os.path.exists(chromium_path)
            
            self.log_test(
                f"Gonzalo Environment - Chromium Check",
                chromium_exists,
                f"System Chromium at {chromium_path}: {'EXISTS ✅' if chromium_exists else 'NOT FOUND ❌'}"
            )
        except Exception as e:
            self.log_test(f"Gonzalo Environment - Chromium Check", False, f"Error: {str(e)}")
        
        # Step 7: Check service logs if possible (check if service directory exists)
        try:
            service_dir = f"/app/whatsapp-services/client-{gonzalo_client['id']}"
            service_exists = os.path.exists(service_dir)
            
            self.log_test(
                f"Gonzalo Service - Directory Check",
                service_exists,
                f"Service directory at {service_dir}: {'EXISTS ✅' if service_exists else 'NOT FOUND ❌'}"
            )
            
            if service_exists:
                # Check if service.js exists
                service_js = f"{service_dir}/service.js"
                service_js_exists = os.path.exists(service_js)
                
                self.log_test(
                    f"Gonzalo Service - Service File Check",
                    service_js_exists,
                    f"Service.js file: {'EXISTS ✅' if service_js_exists else 'NOT FOUND ❌'}"
                )
                
        except Exception as e:
            self.log_test(f"Gonzalo Service - Directory Check", False, f"Error: {str(e)}")

    async def test_specific_client_qr_verification(self):
        """Test QR generation for specific clients mentioned by user"""
        print("\n🔍 TESTING SPECIFIC CLIENT QR VERIFICATION...")
        
        # User mentioned these specific clients to test
        test_clients = [
            {"unique_url": "f6f7ce4e", "name": "Estudio Jurídico Villegas", "port": 3002},
            {"unique_url": "bba9207c", "name": "Consultorio Dr. Martinez", "port": 3003},
            {"unique_url": "3d5e0794", "name": "Cliente Prueba QR", "port": 3004}
        ]
        
        # First, check what clients actually exist in the database
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    existing_clients = await response.json()
                    self.log_test(
                        "QR Verification - Database Check",
                        True,
                        f"Found {len(existing_clients)} clients in database"
                    )
                    
                    # Log existing clients for comparison
                    for client in existing_clients:
                        print(f"  - {client.get('name', 'Unknown')} (URL: {client.get('unique_url', 'N/A')}, Port: {client.get('whatsapp_port', 'N/A')})")
                    
                else:
                    self.log_test(
                        "QR Verification - Database Check",
                        False,
                        f"Cannot access clients: HTTP {response.status}",
                        await response.text()
                    )
                    return
        except Exception as e:
            self.log_test("QR Verification - Database Check", False, f"Error: {str(e)}")
            return
        
        # Test each specific client mentioned by user
        for test_client in test_clients:
            unique_url = test_client["unique_url"]
            expected_name = test_client["name"]
            expected_port = test_client["port"]
            
            # Test 1: Client landing page status
            try:
                async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/status", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        client_name = data.get('client', {}).get('name', 'Unknown')
                        connected = data.get('client', {}).get('connected', False)
                        
                        self.log_test(
                            f"QR Verification - Status ({expected_name})",
                            True,
                            f"Client found: {client_name}, Connected: {connected}"
                        )
                    else:
                        self.log_test(
                            f"QR Verification - Status ({expected_name})",
                            False,
                            f"HTTP {response.status} for URL {unique_url}",
                            await response.text()
                        )
                        continue
            except Exception as e:
                self.log_test(f"QR Verification - Status ({expected_name})", False, f"Error: {str(e)}")
                continue
            
            # Test 2: Client QR endpoint
            try:
                async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/qr", timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        has_qr = data.get('qr') is not None
                        error = data.get('error')
                        
                        if has_qr:
                            self.log_test(
                                f"QR Verification - QR Generation ({expected_name})",
                                True,
                                f"QR code generated successfully for {expected_name}"
                            )
                        else:
                            self.log_test(
                                f"QR Verification - QR Generation ({expected_name})",
                                False,
                                f"No QR available. Error: {error or 'Service not running'}"
                            )
                    else:
                        self.log_test(
                            f"QR Verification - QR Generation ({expected_name})",
                            False,
                            f"HTTP {response.status} for QR endpoint",
                            await response.text()
                        )
            except Exception as e:
                self.log_test(f"QR Verification - QR Generation ({expected_name})", False, f"Error: {str(e)}")
            
            # Test 3: Direct service connectivity (if service is running)
            try:
                service_url = f"http://localhost:{expected_port}"
                async with self.session.get(f"{service_url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        service_status = data.get('status', 'unknown')
                        service_connected = data.get('connected', False)
                        
                        self.log_test(
                            f"QR Verification - Direct Service ({expected_name})",
                            True,
                            f"Service running on port {expected_port}, Status: {service_status}, Connected: {service_connected}"
                        )
                        
                        # Test 4: Direct QR from service
                        try:
                            async with self.session.get(f"{service_url}/qr", timeout=10) as qr_response:
                                if qr_response.status == 200:
                                    qr_data = await qr_response.json()
                                    has_direct_qr = qr_data.get('qr') is not None
                                    
                                    self.log_test(
                                        f"QR Verification - Direct QR ({expected_name})",
                                        True,
                                        f"Direct QR from service: {'Available' if has_direct_qr else 'Not available'}"
                                    )
                                else:
                                    self.log_test(
                                        f"QR Verification - Direct QR ({expected_name})",
                                        False,
                                        f"HTTP {qr_response.status} from direct service QR"
                                    )
                        except Exception as qr_e:
                            self.log_test(f"QR Verification - Direct QR ({expected_name})", False, f"QR Error: {str(qr_e)}")
                    else:
                        self.log_test(
                            f"QR Verification - Direct Service ({expected_name})",
                            False,
                            f"Service not responding on port {expected_port}: HTTP {response.status}"
                        )
            except Exception as e:
                self.log_test(f"QR Verification - Direct Service ({expected_name})", False, f"Service not running on port {expected_port}: {str(e)}")

    async def test_individual_services_status(self):
        """Test if individual WhatsApp services are running"""
        print("\n🔧 TESTING INDIVIDUAL WHATSAPP SERVICES...")
        
        # Check for service directories
        import os
        services_dir = "/app/whatsapp-services"
        
        if os.path.exists(services_dir):
            service_dirs = [d for d in os.listdir(services_dir) if d.startswith('client-')]
            self.log_test(
                "Individual Services - Directory Check",
                len(service_dirs) > 0,
                f"Found {len(service_dirs)} service directories: {service_dirs}"
            )
            
            # Test connectivity to each service
            for service_dir in service_dirs:
                # Extract port from service directory or try common ports
                for port in range(3002, 3010):  # Common port range for individual services
                    try:
                        service_url = f"http://localhost:{port}"
                        async with self.session.get(f"{service_url}/health", timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                self.log_test(
                                    f"Individual Service - Port {port}",
                                    True,
                                    f"Service running on port {port}, status: {data.get('status', 'unknown')}"
                                )
                                break
                    except:
                        continue
                else:
                    self.log_test(
                        f"Individual Service - {service_dir}",
                        False,
                        f"No service found running for {service_dir} on ports 3002-3009"
                    )
        else:
            self.log_test(
                "Individual Services - Directory Check",
                False,
                "No whatsapp-services directory found"
            )

    async def test_email_landing_urls(self):
        """Test the URLs that would be sent in emails"""
        print("\n📧 TESTING EMAIL LANDING URLS...")
        
        # Get base URL from environment
        import os
        from dotenv import load_dotenv
        load_dotenv('/app/backend/.env')
        base_url = os.environ.get('BASE_URL', 'Unknown')
        
        self.log_test(
            "Email URLs - Base URL Check",
            base_url != 'Unknown',
            f"Base URL configured as: {base_url}"
        )
        
        # Test if the base URL is accessible (this is what users click in emails)
        try:
            async with self.session.get(f"{base_url}/api/", timeout=10) as response:
                if response.status == 200:
                    self.log_test(
                        "Email URLs - Base URL Accessibility",
                        True,
                        f"Base URL {base_url} is accessible"
                    )
                else:
                    self.log_test(
                        "Email URLs - Base URL Accessibility",
                        False,
                        f"Base URL {base_url} returns HTTP {response.status} - This could cause 'Error conectando con el servidor'",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Email URLs - Base URL Accessibility", False, f"Cannot access base URL {base_url}: {str(e)}")

    async def test_cors_and_mobile_headers(self):
        """Test CORS and mobile-specific headers"""
        print("\n📱 TESTING CORS AND MOBILE COMPATIBILITY...")
        
        # Test with mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://2d0cc784-803b-4b5a-8a26-60b890ad523e.preview.emergentagent.com'
        }
        
        try:
            async with self.session.get(f"{self.backend_url}/api/", headers=mobile_headers, timeout=10) as response:
                if response.status == 200:
                    # Check CORS headers
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    }
                    
                    self.log_test(
                        "Mobile Compatibility - CORS Headers",
                        True,
                        f"Mobile request successful with CORS headers: {cors_headers}"
                    )
                else:
                    self.log_test(
                        "Mobile Compatibility - CORS Headers",
                        False,
                        f"Mobile request failed with HTTP {response.status}",
                        await response.text()
                    )
        except Exception as e:
            self.log_test("Mobile Compatibility - CORS Headers", False, f"Mobile request error: {str(e)}")

    async def run_all_tests(self):
        """Run all backend tests focused on diagnosing mobile landing page issues"""
        print("=" * 80)
        print("BACKEND TESTING - MOBILE LANDING PAGE DIAGNOSTICS")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        print()

        # Test basic connectivity first
        backend_connected = await self.test_basic_connectivity()
        
        if not backend_connected:
            print("❌ CRITICAL: Backend API is not accessible. This explains 'Error conectando con el servidor'")
            return
        
        # ========== URGENT: GONZALO'S QR ISSUE ==========
        await self.test_gonzalo_specific_qr_issue()
        
        # ========== SPECIFIC MOBILE LANDING PAGE TESTS ==========
        await self.test_mobile_landing_page_access()
        await self.test_individual_services_status()
        await self.test_email_landing_urls()
        await self.test_cors_and_mobile_headers()
        
        # ========== ADMIN PANEL TESTS ==========
        print("\n👨‍💼 TESTING ADMIN PANEL...")
        await self.test_admin_routes()
        
        # ========== DATABASE INTEGRATION ==========
        print("\n💾 TESTING DATABASE INTEGRATION...")
        await self.test_database_integration()
        
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
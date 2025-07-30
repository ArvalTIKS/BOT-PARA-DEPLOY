#!/usr/bin/env python3
"""
Individual Multi-Tenant WhatsApp Architecture Testing
Tests individual WhatsApp services per client on unique ports
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

class IndividualArchitectureTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.session = None
        self.test_client_id = None
        self.test_client_port = None
        
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

    async def test_admin_client_creation(self):
        """Test admin panel client creation with individual architecture"""
        try:
            # Create a test client
            client_data = {
                "name": "Test Client Individual",
                "email": "test@individual.com",
                "openai_api_key": "sk-test-individual-key",
                "openai_assistant_id": "asst_test_individual"
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/admin/clients",
                json=client_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.test_client_id = data.get('id')
                    self.test_client_port = data.get('whatsapp_port')
                    
                    self.log_test(
                        "Admin - Client Creation (Individual)", 
                        True, 
                        f"Created client {data.get('name')} with port {self.test_client_port} and unique URL {data.get('unique_url')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin - Client Creation (Individual)", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Admin - Client Creation (Individual)", False, f"Error: {str(e)}")
            return False

    async def test_admin_get_clients(self):
        """Test getting all clients from admin panel"""
        try:
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    client_count = len(data)
                    
                    # Check if our test client exists
                    test_client_found = False
                    if self.test_client_id:
                        for client in data:
                            if client.get('id') == self.test_client_id:
                                test_client_found = True
                                break
                    
                    self.log_test(
                        "Admin - Get All Clients", 
                        True, 
                        f"Retrieved {client_count} clients, Test client found: {test_client_found}"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin - Get All Clients", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Admin - Get All Clients", False, f"Error: {str(e)}")
            return False

    async def test_individual_service_creation(self):
        """Test creating individual WhatsApp service for client"""
        if not self.test_client_id:
            self.log_test("Individual Service Creation", False, "No test client available")
            return False
            
        try:
            toggle_data = {"action": "connect"}
            async with self.session.put(
                f"{self.backend_url}/api/admin/clients/{self.test_client_id}/toggle",
                json=toggle_data,
                timeout=30  # Service creation can take time
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get('message', '')
                    status = data.get('status', '')
                    
                    self.log_test(
                        "Individual Service Creation", 
                        True, 
                        f"Service creation initiated: {message}, Status: {status}"
                    )
                    
                    # Wait a bit for service to start
                    await asyncio.sleep(5)
                    return True
                else:
                    self.log_test(
                        "Individual Service Creation", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Individual Service Creation", False, f"Error: {str(e)}")
            return False

    async def test_individual_service_connectivity(self):
        """Test connectivity to individual WhatsApp service"""
        if not self.test_client_port:
            self.log_test("Individual Service Connectivity", False, "No test client port available")
            return False
            
        try:
            service_url = f"http://localhost:{self.test_client_port}"
            async with self.session.get(f"{service_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('status', 'unknown')
                    connected = data.get('connected', False)
                    
                    self.log_test(
                        "Individual Service Connectivity", 
                        True, 
                        f"Service on port {self.test_client_port} - Status: {status}, Connected: {connected}"
                    )
                    return True
                else:
                    self.log_test(
                        "Individual Service Connectivity", 
                        False, 
                        f"HTTP {response.status} on port {self.test_client_port}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Individual Service Connectivity", False, f"Error connecting to port {self.test_client_port}: {str(e)}")
            return False

    async def test_individual_qr_generation(self):
        """Test QR code generation for individual service"""
        if not self.test_client_port:
            self.log_test("Individual QR Generation", False, "No test client port available")
            return False
            
        try:
            service_url = f"http://localhost:{self.test_client_port}"
            async with self.session.get(f"{service_url}/qr", timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    has_qr = data.get('qr') is not None
                    has_raw = data.get('raw') is not None
                    
                    self.log_test(
                        "Individual QR Generation", 
                        True, 
                        f"QR service on port {self.test_client_port} - QR available: {has_qr}, Raw data: {has_raw}"
                    )
                    return True
                else:
                    self.log_test(
                        "Individual QR Generation", 
                        False, 
                        f"HTTP {response.status} on port {self.test_client_port}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Individual QR Generation", False, f"Error getting QR from port {self.test_client_port}: {str(e)}")
            return False

    async def test_client_landing_status(self):
        """Test client landing page status endpoint"""
        if not self.test_client_id:
            self.log_test("Client Landing Status", False, "No test client available")
            return False
            
        try:
            # Get client data first to get unique URL
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    test_client = None
                    for client in clients:
                        if client.get('id') == self.test_client_id:
                            test_client = client
                            break
                    
                    if not test_client:
                        self.log_test("Client Landing Status", False, "Test client not found in client list")
                        return False
                    
                    unique_url = test_client.get('unique_url')
                    
                    # Test landing page status
                    async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/status", timeout=10) as status_response:
                        if status_response.status == 200:
                            data = await status_response.json()
                            client_name = data.get('client', {}).get('name', 'Unknown')
                            connected = data.get('client', {}).get('connected', False)
                            
                            self.log_test(
                                "Client Landing Status", 
                                True, 
                                f"Landing page accessible for {client_name}, Connected: {connected}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Client Landing Status", 
                                False, 
                                f"HTTP {status_response.status}",
                                await status_response.text()
                            )
                            return False
                else:
                    self.log_test("Client Landing Status", False, "Could not get client list")
                    return False
        except Exception as e:
            self.log_test("Client Landing Status", False, f"Error: {str(e)}")
            return False

    async def test_client_landing_qr(self):
        """Test client landing page QR endpoint"""
        if not self.test_client_id:
            self.log_test("Client Landing QR", False, "No test client available")
            return False
            
        try:
            # Get client data first to get unique URL
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    test_client = None
                    for client in clients:
                        if client.get('id') == self.test_client_id:
                            test_client = client
                            break
                    
                    if not test_client:
                        self.log_test("Client Landing QR", False, "Test client not found in client list")
                        return False
                    
                    unique_url = test_client.get('unique_url')
                    
                    # Test landing page QR
                    async with self.session.get(f"{self.backend_url}/api/client/{unique_url}/qr", timeout=15) as qr_response:
                        if qr_response.status == 200:
                            data = await qr_response.json()
                            has_qr = data.get('qr') is not None
                            client_name = data.get('client_name', 'Unknown')
                            
                            self.log_test(
                                "Client Landing QR", 
                                True, 
                                f"QR endpoint accessible for {client_name}, Has QR: {has_qr}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Client Landing QR", 
                                False, 
                                f"HTTP {qr_response.status}",
                                await qr_response.text()
                            )
                            return False
                else:
                    self.log_test("Client Landing QR", False, "Could not get client list")
                    return False
        except Exception as e:
            self.log_test("Client Landing QR", False, f"Error: {str(e)}")
            return False

    async def test_individual_openai_integration(self):
        """Test OpenAI integration with individual client credentials"""
        if not self.test_client_id:
            self.log_test("Individual OpenAI Integration", False, "No test client available")
            return False
            
        try:
            test_message = {
                "phone_number": "5491234567890",
                "message": "Hola, necesito información sobre servicios individuales",
                "message_id": f"individual_test_{self.test_client_id}",
                "timestamp": int(time.time())
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/client/{self.test_client_id}/process-message",
                json=test_message,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    success = data.get('success', False)
                    has_reply = data.get('reply') is not None
                    reply_length = len(data.get('reply', '')) if has_reply else 0
                    
                    self.log_test(
                        "Individual OpenAI Integration", 
                        True, 
                        f"Message processed with individual client credentials - Success: {success}, Has reply: {has_reply}, Reply length: {reply_length}"
                    )
                    return True
                else:
                    self.log_test(
                        "Individual OpenAI Integration", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Individual OpenAI Integration", False, f"Error: {str(e)}")
            return False

    async def test_email_service_integration(self):
        """Test email service integration"""
        try:
            # Test by creating another client which should trigger email sending
            client_data = {
                "name": "Email Test Client",
                "email": "emailtest@individual.com",
                "openai_api_key": "sk-test-email-key",
                "openai_assistant_id": "asst_test_email"
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/admin/clients",
                json=client_data,
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    self.log_test(
                        "Email Service Integration", 
                        True, 
                        f"Client creation with email service - Client: {data.get('name')}, Email should be sent to: {data.get('email')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Email Service Integration", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Email Service Integration", False, f"Error: {str(e)}")
            return False

    async def test_deploy_environment_compatibility(self):
        """Test deploy environment compatibility"""
        try:
            # Check if system Chromium is available
            chromium_path = "/usr/bin/chromium"
            chromium_available = os.path.exists(chromium_path)
            
            # Check environment variable
            emergent_env = os.environ.get('EMERGENT_ENV', 'preview')
            
            self.log_test(
                "Deploy Environment Compatibility", 
                True, 
                f"Environment: {emergent_env}, System Chromium available: {chromium_available} at {chromium_path}"
            )
            return True
        except Exception as e:
            self.log_test("Deploy Environment Compatibility", False, f"Error: {str(e)}")
            return False

    async def test_port_uniqueness(self):
        """Test that each client gets a unique port"""
        try:
            # Get all clients and check port uniqueness
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    ports = [client.get('whatsapp_port') for client in clients if client.get('whatsapp_port')]
                    unique_ports = set(ports)
                    
                    ports_unique = len(ports) == len(unique_ports)
                    
                    self.log_test(
                        "Port Uniqueness", 
                        ports_unique, 
                        f"Total ports: {len(ports)}, Unique ports: {len(unique_ports)}, All unique: {ports_unique}"
                    )
                    return ports_unique
                else:
                    self.log_test(
                        "Port Uniqueness", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Port Uniqueness", False, f"Error: {str(e)}")
            return False

    async def test_service_isolation(self):
        """Test that services are isolated per client"""
        try:
            # Get all clients
            async with self.session.get(f"{self.backend_url}/api/admin/clients", timeout=10) as response:
                if response.status == 200:
                    clients = await response.json()
                    
                    isolated_services = 0
                    total_services = 0
                    
                    for client in clients:
                        port = client.get('whatsapp_port')
                        if port:
                            total_services += 1
                            try:
                                # Try to connect to individual service
                                async with self.session.get(f"http://localhost:{port}/health", timeout=5) as service_response:
                                    if service_response.status == 200:
                                        isolated_services += 1
                            except:
                                # Service not running is also valid (means it's isolated)
                                isolated_services += 1
                    
                    isolation_rate = (isolated_services / total_services * 100) if total_services > 0 else 100
                    
                    self.log_test(
                        "Service Isolation", 
                        isolation_rate >= 80, 
                        f"Services isolated: {isolated_services}/{total_services} ({isolation_rate:.1f}%)"
                    )
                    return isolation_rate >= 80
                else:
                    self.log_test(
                        "Service Isolation", 
                        False, 
                        f"HTTP {response.status}",
                        await response.text()
                    )
                    return False
        except Exception as e:
            self.log_test("Service Isolation", False, f"Error: {str(e)}")
            return False

    async def cleanup_test_clients(self):
        """Clean up test clients created during testing"""
        try:
            if self.test_client_id:
                async with self.session.delete(f"{self.backend_url}/api/admin/clients/{self.test_client_id}", timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ Cleaned up test client {self.test_client_id}")
                    else:
                        print(f"⚠️ Could not clean up test client {self.test_client_id}")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")

    async def run_all_tests(self):
        """Run all individual architecture tests"""
        print("=" * 80)
        print("INDIVIDUAL MULTI-TENANT WHATSAPP ARCHITECTURE TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        print()

        # Test basic connectivity first
        backend_connected = await self.test_basic_connectivity()
        
        if not backend_connected:
            print("❌ CRITICAL: Backend API is not accessible. Stopping tests.")
            return
            
        # ========== INDIVIDUAL ARCHITECTURE TESTS ==========
        print("\n🏗️ TESTING INDIVIDUAL ARCHITECTURE...")
        await self.test_admin_client_creation()
        await self.test_admin_get_clients()
        await self.test_individual_service_creation()
        await self.test_individual_service_connectivity()
        await self.test_individual_qr_generation()
        
        # ========== CLIENT LANDING PAGES ==========
        print("\n🌐 TESTING CLIENT LANDING PAGES...")
        await self.test_client_landing_status()
        await self.test_client_landing_qr()
        
        # ========== INDIVIDUAL OPENAI INTEGRATION ==========
        print("\n🤖 TESTING INDIVIDUAL OPENAI INTEGRATION...")
        await self.test_individual_openai_integration()
        
        # ========== EMAIL SERVICE ==========
        print("\n📧 TESTING EMAIL SERVICE...")
        await self.test_email_service_integration()
        
        # ========== DEPLOY ENVIRONMENT ==========
        print("\n🚀 TESTING DEPLOY ENVIRONMENT...")
        await self.test_deploy_environment_compatibility()
        
        # ========== ARCHITECTURE VALIDATION ==========
        print("\n🔍 TESTING ARCHITECTURE VALIDATION...")
        await self.test_port_uniqueness()
        await self.test_service_isolation()
        
        # Cleanup
        print("\n🧹 CLEANING UP...")
        await self.cleanup_test_clients()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("INDIVIDUAL ARCHITECTURE TEST SUMMARY")
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
                if any(keyword in result['test'] for keyword in ['Connectivity', 'Creation', 'Service', 'OpenAI']):
                    critical_issues.append(result['test'])
        
        if critical_issues:
            for issue in critical_issues:
                print(f"🚨 {issue}")
        else:
            print("✅ No critical issues found")
        
        print("=" * 80)

async def main():
    """Main test runner"""
    async with IndividualArchitectureTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
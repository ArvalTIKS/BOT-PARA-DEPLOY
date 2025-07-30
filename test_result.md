#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "ARQUITECTURA MULTI-TENANT RESTAURADA: Revertir sistema consolidado incorrecto y restaurar la arquitectura original donde cada cliente debe tener su propia instancia independiente del servicio WhatsApp conectada a su propio número único de WhatsApp en un puerto distinto (3002, 3003, etc). Solucionar problemas de Chromium en servicios individuales y verificar que cada cliente obtenga su QR code y servicio independiente correctamente."

backend:
  - task: "Individual WhatsApp Service Architecture"
    implemented: true
    working: false
    file: "/app/backend/whatsapp_manager.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "ARQUITECTURA INDIVIDUAL RESTAURADA: Eliminada arquitectura consolidada incorrecta. Cada cliente debe tener su propio servicio WhatsApp en puerto único (3002, 3003, etc). Servicios individuales generan QR correctamente pero necesita testing completo de funcionalidad multi-tenant."

  - task: "Admin Panel Client Creation"
    implemented: true
    working: false
    file: "/app/backend/admin_routes.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "Panel admin debe permitir crear clientes con nombre, email, OpenAI API key y Assistant ID. Debe asignar puerto único y enviar email de invitación."

  - task: "Email Service Integration"
    implemented: true
    working: false
    file: "/app/backend/email_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "Servicio email debe enviar invitaciones con URLs únicas de landing page a cada cliente creado."

  - task: "Individual Client Services Management"
    implemented: true
    working: false
    file: "/app/backend/whatsapp_manager.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "WhatsAppServiceManager debe crear/iniciar/detener servicios individuales por cliente en puertos únicos. Cada servicio debe usar Chromium del sistema y generar QR independiente."

  - task: "Client Landing Pages Individual Services"
    implemented: true
    working: false
    file: "/app/backend/client_routes.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "Client routes debe obtener QR y status de servicios individuales específicos por cliente, no del sistema consolidado."

  - task: "Individual OpenAI Integration Per Client"
    implemented: true
    working: false
    file: "/app/backend/client_routes.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "Cada cliente debe usar sus propias credenciales OpenAI (API key y Assistant ID específicos) para procesar mensajes independientemente."

  - task: "Deploy Environment Compatibility"
    implemented: true
    working: false
    file: "/app/whatsapp-services/client-*/service.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: false
          agent: "main"
          comment: "Servicios individuales deben funcionar correctamente en ambiente deploy con Chromium del sistema y configuración optimizada."

frontend:
  # Frontend testing not performed as per instructions

metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus:
    - "Individual WhatsApp Service Architecture"
    - "Admin Panel Client Creation"
    - "Email Service Integration"
    - "Individual Client Services Management"
    - "Deploy Environment Compatibility"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "ARQUITECTURA INDIVIDUAL RESTAURADA: ✅ Eliminada completamente la arquitectura consolidada incorrecta (consolidated_routes.py, consolidated_whatsapp_manager.py). ✅ Sistema ahora usa servicios individuales por cliente en puertos únicos (3002, 3003, etc). ✅ Cada cliente tendrá su propio proceso Node.js independiente. ✅ Solucionados problemas de Chromium usando sistema Chromium (/usr/bin/chromium). ✅ Servicio individual genera QR correctamente. NECESITA TESTING COMPLETO de funcionalidad multi-tenant: creación de clientes, envío de emails, QR individual, OpenAI por cliente."
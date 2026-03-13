#!/bin/bash
# Comprehensive seed data script - FIXED to match current schema
# All enum values are uppercase, all required fields are provided

echo "🌱 Seeding database with comprehensive sample data..."
echo ""

# Create test user
echo "👤 Creating test user..."
curl -s -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "fullname": "Test User"
  }' > /dev/null 2>&1

# Login
TOKEN=$(curl -s -X POST http://localhost:8080/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get auth token"
  exit 1
fi

echo "✓ Got authentication token"
echo ""
echo "📝 Creating mind nodes..."

# 1. Company (requires: industry)
COMPANY=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "company",
    "title": "TechCorp Inc",
    "creator": "test@example.com",
    "description": "A leading technology company",
    "status": "active",
    "type_specific_attributes": {
      "industry": "Software Development",
      "size": 500,
      "founded_date": "2010-01-15"
    }
  }')
UUID_COMPANY=$(echo $COMPANY | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Company: TechCorp Inc"

# 2. Department (requires: department_code)
DEPT=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "department",
    "title": "Engineering Department",
    "creator": "test@example.com",
    "description": "Software engineering team",
    "status": "active",
    "type_specific_attributes": {
      "department_code": "ENG-001",
      "manager": "john.manager@techcorp.com"
    }
  }')
UUID_DEPT=$(echo $DEPT | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Department: Engineering"

# 3. Resource (has defaults, resource_type uppercase)
RESOURCE=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "resource",
    "title": "John Developer",
    "creator": "test@example.com",
    "description": "Senior Software Engineer",
    "status": "active",
    "type_specific_attributes": {
      "resource_type": "PERSON",
      "email": "john.dev@techcorp.com",
      "hourly_rate": 120.0,
      "efficiency": 1.2
    }
  }')
UUID_RESOURCE=$(echo $RESOURCE | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Resource: John Developer"

# 4. Project (requires: start_date, end_date)
PROJECT=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "project",
    "title": "Mind Graph Editor",
    "creator": "test@example.com",
    "description": "Build a graph-based knowledge management system",
    "status": "active",
    "type_specific_attributes": {
      "start_date": "2026-01-01",
      "end_date": "2026-06-30",
      "budget": 250000.0
    }
  }')
UUID_PROJECT=$(echo $PROJECT | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Project: Mind Graph Editor"

# 5. Requirement (requires: requirement_type UPPERCASE, content)
REQ1=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "requirement",
    "title": "Graph Visualization",
    "creator": "test@example.com",
    "description": "Display minds as nodes and relationships as edges",
    "status": "active",
    "type_specific_attributes": {
      "requirement_type": "USER_STORY",
      "content": "As a user, I want to see all mind nodes displayed as interactive graph nodes with relationships shown as edges, so that I can visualize the knowledge structure."
    }
  }')
UUID_REQ1=$(echo $REQ1 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Requirement: Graph Visualization"

# 6. Requirement 2
REQ2=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "requirement",
    "title": "Real-time Collaboration",
    "creator": "test@example.com",
    "description": "Multiple users can edit the graph simultaneously",
    "status": "draft",
    "type_specific_attributes": {
      "requirement_type": "USER_NEED",
      "content": "Users need the ability to collaborate in real-time on the same graph with automatic synchronization of changes."
    }
  }')
UUID_REQ2=$(echo $REQ2 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Requirement: Real-time Collaboration"

# 7. Task (requires: priority UPPERCASE, assignee)
TASK1=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "task",
    "title": "Implement React Flow Integration",
    "creator": "test@example.com",
    "description": "Integrate React Flow library for graph visualization",
    "status": "active",
    "type_specific_attributes": {
      "priority": "HIGH",
      "assignee": "john.dev@techcorp.com",
      "due_date": "2026-02-15",
      "effort": 40.0
    }
  }')
UUID_TASK1=$(echo $TASK1 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Task: Implement React Flow Integration"

# 8. Task 2
TASK2=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "task",
    "title": "Create Backend API Endpoints",
    "creator": "test@example.com",
    "description": "Build FastAPI endpoints for minds and relationships",
    "status": "done",
    "type_specific_attributes": {
      "priority": "HIGH",
      "assignee": "john.dev@techcorp.com",
      "due_date": "2026-03-10",
      "effort": 30.0
    }
  }')
UUID_TASK2=$(echo $TASK2 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Task: Create Backend API Endpoints"

# 9. AcceptanceCriteria (requires: criteria_text, verification_method, verification_status)
AC=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "acceptance_criteria",
    "title": "Graph renders all nodes",
    "creator": "test@example.com",
    "description": "Acceptance criteria for graph visualization",
    "status": "active",
    "type_specific_attributes": {
      "criteria_text": "All mind nodes must be visible on the graph canvas with correct positioning",
      "verification_method": "Manual testing with sample dataset",
      "verification_status": "pending"
    }
  }')
UUID_AC=$(echo $AC | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Acceptance Criteria: Graph renders all nodes"

# 10. Risk (requires: severity LOWERCASE, probability LOWERCASE)
RISK=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "risk",
    "title": "Performance with large graphs",
    "creator": "test@example.com",
    "description": "Graph may become slow with 1000+ nodes",
    "status": "active",
    "type_specific_attributes": {
      "severity": "high",
      "probability": "likely",
      "mitigation_plan": "Implement virtualization and lazy loading"
    }
  }')
UUID_RISK=$(echo $RISK | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Risk: Performance with large graphs"

# 11. Knowledge (requires: category, tags, content)
KNOW1=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "knowledge",
    "title": "React Flow Documentation",
    "creator": "test@example.com",
    "description": "Official React Flow documentation and examples",
    "status": "active",
    "type_specific_attributes": {
      "category": "Documentation",
      "tags": ["react", "graph", "visualization"],
      "content": "React Flow is a library for building node-based editors and interactive diagrams. Visit https://reactflow.dev for complete documentation."
    }
  }')
UUID_KNOW1=$(echo $KNOW1 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Knowledge: React Flow Documentation"

# 12. Knowledge 2
KNOW2=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "knowledge",
    "title": "Neo4j Graph Database",
    "creator": "test@example.com",
    "description": "Neo4j graph database concepts and best practices",
    "status": "active",
    "type_specific_attributes": {
      "category": "Database",
      "tags": ["neo4j", "graph", "database"],
      "content": "Neo4j is a native graph database that stores data as nodes and relationships. Use Cypher query language for data operations."
    }
  }')
UUID_KNOW2=$(echo $KNOW2 | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Knowledge: Neo4j Graph Database"

# 13. Email (requires: sender, recipients, subject, sent_at)
EMAIL=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "email",
    "title": "Project Kickoff Meeting",
    "creator": "test@example.com",
    "description": "Invitation to project kickoff meeting",
    "status": "active",
    "type_specific_attributes": {
      "sender": "manager@techcorp.com",
      "recipients": ["john.dev@techcorp.com", "team@techcorp.com"],
      "subject": "Mind Graph Editor - Project Kickoff",
      "sent_at": "2026-01-05T10:00:00Z"
    }
  }')
UUID_EMAIL=$(echo $EMAIL | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Email: Project Kickoff Meeting"

# 14. Account (account_type UPPERCASE)
ACCOUNT=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "account",
    "title": "AWS Production Account",
    "creator": "test@example.com",
    "description": "Production infrastructure costs",
    "status": "active",
    "type_specific_attributes": {
      "account_type": "COST"
    }
  }')
UUID_ACCOUNT=$(echo $ACCOUNT | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Account: AWS Production Account"

# 15. Failure (requires: failure_mode, effects, causes)
FAILURE=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "failure",
    "title": "API Timeout on Large Queries",
    "creator": "test@example.com",
    "description": "API times out when querying large datasets",
    "status": "active",
    "type_specific_attributes": {
      "failure_mode": "Request timeout after 30 seconds",
      "effects": "Users cannot retrieve large graph datasets",
      "causes": "Inefficient Cypher queries without pagination",
      "detection_method": "API monitoring and error logs"
    }
  }')
UUID_FAILURE=$(echo $FAILURE | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Failure: API Timeout on Large Queries"

echo ""
echo "🔗 Creating relationships..."

# Company contains Department
if [ ! -z "$UUID_COMPANY" ] && [ ! -z "$UUID_DEPT" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_COMPANY/relationships?target_uuid=$UUID_DEPT&relationship_type=contains" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Company CONTAINS Department"
fi

# Department contains Project
if [ ! -z "$UUID_DEPT" ] && [ ! -z "$UUID_PROJECT" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_DEPT/relationships?target_uuid=$UUID_PROJECT&relationship_type=contains" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Department CONTAINS Project"
fi

# Resource assigned to Project
if [ ! -z "$UUID_RESOURCE" ] && [ ! -z "$UUID_PROJECT" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_RESOURCE/relationships?target_uuid=$UUID_PROJECT&relationship_type=assigned_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Resource ASSIGNED_TO Project"
fi

# Project contains Requirements
if [ ! -z "$UUID_PROJECT" ] && [ ! -z "$UUID_REQ1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_PROJECT/relationships?target_uuid=$UUID_REQ1&relationship_type=contains" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Project CONTAINS Requirement 1"
fi

if [ ! -z "$UUID_PROJECT" ] && [ ! -z "$UUID_REQ2" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_PROJECT/relationships?target_uuid=$UUID_REQ2&relationship_type=contains" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Project CONTAINS Requirement 2"
fi

# Tasks implement Requirements
if [ ! -z "$UUID_TASK1" ] && [ ! -z "$UUID_REQ1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK1/relationships?target_uuid=$UUID_REQ1&relationship_type=implements" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task 1 IMPLEMENTS Requirement 1"
fi

if [ ! -z "$UUID_TASK2" ] && [ ! -z "$UUID_REQ1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK2/relationships?target_uuid=$UUID_REQ1&relationship_type=implements" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task 2 IMPLEMENTS Requirement 1"
fi

# Tasks assigned to Resource
if [ ! -z "$UUID_TASK1" ] && [ ! -z "$UUID_RESOURCE" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK1/relationships?target_uuid=$UUID_RESOURCE&relationship_type=assigned_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task 1 ASSIGNED_TO Resource"
fi

# Task depends on Task
if [ ! -z "$UUID_TASK1" ] && [ ! -z "$UUID_TASK2" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK1/relationships?target_uuid=$UUID_TASK2&relationship_type=depends_on" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task 1 DEPENDS_ON Task 2"
fi

# Acceptance Criteria relates to Requirement
if [ ! -z "$UUID_AC" ] && [ ! -z "$UUID_REQ1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_AC/relationships?target_uuid=$UUID_REQ1&relationship_type=relates_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Acceptance Criteria RELATES_TO Requirement 1"
fi

# Risk mitigated by Task
if [ ! -z "$UUID_RISK" ] && [ ! -z "$UUID_TASK1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK1/relationships?target_uuid=$UUID_RISK&relationship_type=mitigates" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task 1 MITIGATES Risk"
fi

# Knowledge relates to Task
if [ ! -z "$UUID_KNOW1" ] && [ ! -z "$UUID_TASK1" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_KNOW1/relationships?target_uuid=$UUID_TASK1&relationship_type=relates_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Knowledge 1 RELATES_TO Task 1"
fi

echo ""
echo "✅ Seeding complete!"
echo "📊 Created:"
echo "   - 1 Test user (test@example.com / password123)"
echo "   - 15 Mind nodes (all major types)"
echo "   - 12 Relationships"
echo ""
echo "🌐 Visit http://localhost:3000/graph-editor to view the graph"
echo "🔑 Login with: test@example.com / password123"

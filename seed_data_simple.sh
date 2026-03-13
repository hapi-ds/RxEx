#!/bin/bash
# Simple seed script that works with the current schema

echo "🌱 Seeding database with sample data..."

# Create test user
echo "👤 Creating test user..."
curl -s -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "fullname": "Test User"}' > /dev/null 2>&1

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

# Create Company
echo "📝 Creating nodes..."
COMPANY=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "company",
    "title": "TechCorp Inc",
    "creator": "test@example.com",
    "description": "A technology company",
    "status": "active"
  }')
UUID_COMPANY=$(echo $COMPANY | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Company: TechCorp Inc"

# Create Department
DEPT=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "department",
    "title": "Engineering",
    "creator": "test@example.com",
    "description": "Engineering department",
    "status": "active"
  }')
UUID_DEPT=$(echo $DEPT | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Department: Engineering"

# Create Resource
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
      "email": "john@techcorp.com"
    }
  }')
UUID_RESOURCE=$(echo $RESOURCE | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Resource: John Developer"

# Create Project
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

# Create Requirement
REQ=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "requirement",
    "title": "Graph Visualization",
    "creator": "test@example.com",
    "description": "Display minds as nodes and relationships as edges",
    "status": "active",
    "type_specific_attributes": {
      "requirement_type": "FUNCTIONAL",
      "content": "The system shall display all mind nodes as interactive graph nodes with relationships shown as edges"
    }
  }')
UUID_REQ=$(echo $REQ | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Requirement: Graph Visualization"

# Create Task
TASK=$(curl -s -X POST http://localhost:8080/api/v1/minds \
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
      "assignee": "john@techcorp.com",
      "due_date": "2026-02-15"
    }
  }')
UUID_TASK=$(echo $TASK | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Task: Implement React Flow Integration"

# Create Knowledge
KNOW=$(curl -s -X POST http://localhost:8080/api/v1/minds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mind_type": "knowledge",
    "title": "React Flow Documentation",
    "creator": "test@example.com",
    "description": "Official React Flow documentation and examples",
    "status": "active",
    "type_specific_attributes": {
      "url": "https://reactflow.dev/docs",
      "content_type": "DOCUMENTATION"
    }
  }')
UUID_KNOW=$(echo $KNOW | grep -o '"uuid":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "  ✓ Knowledge: React Flow Documentation"

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

# Project contains Requirement
if [ ! -z "$UUID_PROJECT" ] && [ ! -z "$UUID_REQ" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_PROJECT/relationships?target_uuid=$UUID_REQ&relationship_type=contains" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Project CONTAINS Requirement"
fi

# Task implements Requirement
if [ ! -z "$UUID_TASK" ] && [ ! -z "$UUID_REQ" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK/relationships?target_uuid=$UUID_REQ&relationship_type=implements" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task IMPLEMENTS Requirement"
fi

# Resource assigned to Task
if [ ! -z "$UUID_RESOURCE" ] && [ ! -z "$UUID_TASK" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_TASK/relationships?target_uuid=$UUID_RESOURCE&relationship_type=assigned_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Task ASSIGNED_TO Resource"
fi

# Knowledge relates to Task
if [ ! -z "$UUID_KNOW" ] && [ ! -z "$UUID_TASK" ]; then
  curl -s -X POST "http://localhost:8080/api/v1/minds/$UUID_KNOW/relationships?target_uuid=$UUID_TASK&relationship_type=relates_to" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  echo "  ✓ Knowledge RELATES_TO Task"
fi

echo ""
echo "✅ Seeding complete!"
echo "📊 Created 7 nodes and 6 relationships"
echo "🌐 Visit http://localhost:3000/graph-editor to view the graph"

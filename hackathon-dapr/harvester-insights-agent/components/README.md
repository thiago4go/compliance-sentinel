# Dapr Components for Harvester Agent

**IMPORTANT**: These component definitions reference EXISTING shared components in the compliance-sentinel system.

## Component References

### 1. messagepubsub (pubsub.yaml)
- **Type**: Redis Pub/Sub
- **Purpose**: Event-driven communication between agents
- **Shared with**: All agents in the system
- **Topics used by harvester**:
  - `harvest-request` (subscriber)
  - `compliance-query` (subscriber)  
  - `harvester-complete` (publisher)
  - `workflow-trigger` (publisher)

### 2. workflowstatestore (statestore.yaml)
- **Type**: Redis State Store
- **Purpose**: Workflow state management
- **Shared with**: workflow-agent, other agents
- **Actor support**: Enabled for Dapr Workflows

### 3. conversationstore (conversationstore.yaml)
- **Type**: Redis State Store
- **Purpose**: Agent conversation memory
- **Scope**: harvester-insights-agent only
- **Key prefix**: `conversation:`

### 4. searchresultsstore (searchresultsstore.yaml)
- **Type**: Redis State Store
- **Purpose**: Search results caching
- **Scope**: harvester-insights-agent only
- **Key prefix**: `search:`

### 5. agentstatestore (agentstatestore.yaml)
- **Type**: Redis State Store
- **Purpose**: Agent registry and state
- **Shared with**: All agents
- **Key prefix**: `agent:`

## Development vs Production

### Development (docker-compose.dev.yml)
- Uses local Redis instance
- Components point to `redis-dev:6379`

### Production
- Uses shared Redis cluster
- Components point to production Redis endpoints
- All agents share the same component instances

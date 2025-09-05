"""
API Documentation Processor
Handles OneFlow OpenAPI specification parsing and knowledge base creation
"""
import os
import json
import yaml
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import streamlit as st


class APIDocsProcessor:
    """Processes and caches OneFlow API documentation"""

    def __init__(self):
        self.api_spec_url = os.getenv('ONEFLOW_API_SPEC_URL',
                                      'https://api.oneflow.com/static/papi/version_1.yml')
        self.cache_dir = 'data'
        self.spec_file = os.path.join(self.cache_dir, 'oneflow_api_spec.yml')
        self.knowledge_base_file = os.path.join(self.cache_dir, 'knowledge_base.json')
        self.cache_refresh_hours = int(os.getenv('CACHE_REFRESH_HOURS', '24'))

        # Ensure data directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialize knowledge base
        self.knowledge_base = self._load_or_create_knowledge_base()

    def _load_or_create_knowledge_base(self) -> Dict[str, Any]:
        """Load existing knowledge base or create a new one"""
        if self._should_refresh_cache():
            return self._create_knowledge_base()

        # Try to load existing knowledge base
        if os.path.exists(self.knowledge_base_file):
            try:
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    st.success(f"Loaded cached knowledge base with {len(data.get('endpoints', {}))} endpoints")
                    return data
            except Exception as e:
                st.warning(f"Could not load cached knowledge base: {e}")
                # Delete corrupted cache file
                try:
                    os.remove(self.knowledge_base_file)
                except:
                    pass

        # Create new knowledge base if loading failed
        return self._create_knowledge_base()

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed"""
        if not os.path.exists(self.knowledge_base_file):
            return True

        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(self.knowledge_base_file)
        )

        return file_age > timedelta(hours=self.cache_refresh_hours)

    def _create_knowledge_base(self) -> Dict[str, Any]:
        """Create knowledge base from OneFlow API specification"""
        try:
            # Download or load API specification
            api_spec = self._get_api_specification()

            if not api_spec:
                return self._get_fallback_knowledge_base()

            # Process the specification
            knowledge_base = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'api_version': api_spec.get('info', {}).get('version', 'unknown'),
                    'title': api_spec.get('info', {}).get('title', 'OneFlow API')
                },
                'endpoints': self._extract_endpoints(api_spec),
                'workflows': self._define_workflows(),
                'schemas': self._extract_schemas(api_spec)
            }

            # Save knowledge base (with datetime serialization fix)
            with open(self.knowledge_base_file, 'w') as f:
                json.dump(knowledge_base, f, indent=2, default=str)

            return knowledge_base

        except Exception as e:
            st.error(f"Error creating knowledge base: {e}")
            return self._get_fallback_knowledge_base()

    def _get_api_specification(self) -> Optional[Dict[str, Any]]:
        """Download and parse OneFlow API specification"""
        try:
            # Try to download fresh specification
            response = requests.get(self.api_spec_url, timeout=30)
            response.raise_for_status()

            # Save the specification
            with open(self.spec_file, 'w') as f:
                f.write(response.text)

            # Parse YAML
            return yaml.safe_load(response.text)

        except Exception as e:
            st.warning(f"Could not download API specification: {e}")

            # Try to load cached version
            if os.path.exists(self.spec_file):
                try:
                    with open(self.spec_file, 'r') as f:
                        return yaml.safe_load(f)
                except Exception as e2:
                    st.error(f"Could not load cached specification: {e2}")

            return None

    def _extract_endpoints(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize endpoints from API specification"""
        endpoints = {}
        paths = api_spec.get('paths', {})

        for path, path_info in paths.items():
            for method, method_info in path_info.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_key = f"{method.upper()} {path}"

                    endpoints[endpoint_key] = {
                        'path': path,
                        'method': method.upper(),
                        'summary': method_info.get('summary', ''),
                        'description': method_info.get('description', ''),
                        'operationId': method_info.get('operationId', ''),
                        'tags': method_info.get('tags', []),
                        'parameters': self._extract_parameters(method_info),
                        'request_body': self._extract_request_body(method_info),
                        'responses': self._extract_responses(method_info),
                        'workflow_category': self._categorize_endpoint(path, method_info),
                        'prerequisites': self._identify_prerequisites(path, method),
                        'follow_ups': self._identify_follow_ups(path, method)
                    }

        return endpoints

    def _extract_parameters(self, method_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameters from method info"""
        parameters = []
        for param in method_info.get('parameters', []):
            parameters.append({
                'name': param.get('name', ''),
                'in': param.get('in', ''),
                'required': param.get('required', False),
                'description': param.get('description', ''),
                'schema': param.get('schema', {}),
                'example': param.get('example', '')
            })
        return parameters

    def _extract_request_body(self, method_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body information"""
        request_body = method_info.get('requestBody')
        if not request_body:
            return None

        return {
            'description': request_body.get('description', ''),
            'required': request_body.get('required', False),
            'content': request_body.get('content', {})
        }

    def _extract_responses(self, method_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract response information"""
        return method_info.get('responses', {})

    def _categorize_endpoint(self, path: str, method_info: Dict[str, Any]) -> str:
        """Categorize endpoint based on path and tags"""
        tags = method_info.get('tags', [])

        if any('account' in tag.lower() for tag in tags):
            return 'authentication_setup'
        elif any('user' in tag.lower() for tag in tags):
            return 'user_management'
        elif any('template' in tag.lower() for tag in tags):
            return 'template_management'
        elif any('contact' in tag.lower() for tag in tags):
            return 'contact_management'
        elif any('contract' in tag.lower() for tag in tags):
            if 'parties' in path or 'participants' in path:
                return 'contract_parties'
            elif 'files' in path:
                return 'file_management'
            elif 'publish' in path:
                return 'contract_publishing'
            else:
                return 'contract_management'
        elif any('webhook' in tag.lower() for tag in tags):
            return 'integration_automation'
        else:
            return 'general'

    def _identify_prerequisites(self, path: str, method: str) -> List[str]:
        """Identify prerequisite endpoints for this endpoint"""
        prerequisites = []

        # Contract creation needs templates and account info
        if '/contracts/create' in path:
            prerequisites.extend(['GET /templates', 'GET /accounts/me'])

        # Adding parties needs contract to exist
        if '/parties' in path and method == 'POST':
            prerequisites.append('POST /contracts/create')

        # Adding participants needs party to exist
        if '/participants' in path and method == 'POST':
            prerequisites.extend(['POST /contracts/create', 'POST /contracts/{id}/parties'])

        return prerequisites

    def _identify_follow_ups(self, path: str, method: str) -> List[str]:
        """Identify logical follow-up endpoints"""
        follow_ups = []

        # After creating contract, suggest adding parties
        if '/contracts/create' in path:
            follow_ups.extend([
                'POST /contracts/{id}/parties',
                'POST /contracts/{id}/files',
                'POST /contracts/{id}/publish'
            ])

        # After adding parties, suggest adding participants
        if '/parties' in path and method == 'POST':
            follow_ups.extend([
                'POST /contracts/{id}/parties/{party_id}/participants',
                'POST /contracts/{id}/publish'
            ])

        return follow_ups

    def _extract_schemas(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract schema definitions"""
        components = api_spec.get('components', {})
        return components.get('schemas', {})

    def _define_workflows(self) -> Dict[str, Any]:
        """Define common workflow patterns"""
        return {
            'basic_contract_creation': {
                'name': 'Basic Contract Creation',
                'description': 'Create a simple contract from template',
                'steps': [
                    'GET /accounts/me - Verify account access',
                    'GET /templates - Find available templates',
                    'POST /contracts/create - Create contract from template',
                    'POST /contracts/{id}/parties - Add contract parties',
                    'POST /contracts/{id}/publish - Publish for signing'
                ],
                'endpoints_sequence': [
                    'GET /accounts/me',
                    'GET /templates',
                    'POST /contracts/create',
                    'POST /contracts/{id}/parties',
                    'POST /contracts/{id}/publish'
                ]
            },
            'contact_management': {
                'name': 'Contact Management',
                'description': 'Manage contacts for contract parties',
                'steps': [
                    'GET /contacts - List existing contacts',
                    'POST /contacts - Create new contact',
                    'GET /contacts/{id} - Retrieve contact details'
                ],
                'endpoints_sequence': [
                    'GET /contacts',
                    'POST /contacts'
                ]
            },
            'webhook_integration': {
                'name': 'Webhook Integration',
                'description': 'Setup real-time notifications',
                'steps': [
                    'POST /webhooks - Create webhook endpoint',
                    'GET /webhooks - List configured webhooks',
                    'GET /contracts/{id}/events - Monitor contract events'
                ],
                'endpoints_sequence': [
                    'POST /webhooks',
                    'GET /webhooks'
                ]
            }
        }

    def _get_fallback_knowledge_base(self) -> Dict[str, Any]:
        """Provide a minimal fallback knowledge base"""
        return {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'api_version': 'fallback',
                'title': 'OneFlow API (Fallback)'
            },
            'endpoints': {
                'GET /accounts/me': {
                    'path': '/accounts/me',
                    'method': 'GET',
                    'summary': 'Get account information',
                    'workflow_category': 'authentication_setup'
                }
            },
            'workflows': self._define_workflows(),
            'schemas': {}
        }

    def refresh_cache(self):
        """Force refresh of cached data"""
        if os.path.exists(self.knowledge_base_file):
            os.remove(self.knowledge_base_file)
        if os.path.exists(self.spec_file):
            os.remove(self.spec_file)

        self.knowledge_base = self._create_knowledge_base()

    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """Search endpoints by query"""
        results = []
        query_lower = query.lower()

        for endpoint_key, endpoint_info in self.knowledge_base.get('endpoints', {}).items():
            # Search in summary, description, and path
            if (query_lower in endpoint_info.get('summary', '').lower() or
                    query_lower in endpoint_info.get('description', '').lower() or
                    query_lower in endpoint_info.get('path', '').lower()):
                results.append({
                    'endpoint': endpoint_key,
                    'info': endpoint_info
                })

        return results

    def get_workflow_by_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get workflow information by category"""
        return self.knowledge_base.get('workflows', {}).get(category)
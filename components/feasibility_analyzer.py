"""
Feasibility Analyzer
Processes sales questions using OpenAI to assess OneFlow API feasibility
"""
import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
import streamlit as st

class FeasibilityAnalyzer:
    """Analyzes sales questions and assesses technical feasibility using OneFlow API"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-3.5-turbo"

        # Define OneFlow business capabilities
        self.business_capabilities = {
            'contract_creation': {
                'description': 'Create contracts from templates or scratch',
                'supported': True,
                'caveats': ['Requires valid template', 'Template must be active'],
                'endpoints': ['/templates', '/contracts/create']
            },
            'file_management': {
                'description': 'Upload and manage files/documents',
                'supported': True,
                'caveats': ['Template must allow file attachments', 'Size limits apply', 'Separate API call after contract creation'],
                'endpoints': ['/contracts/{id}/files']
            },
            'multi_party_contracts': {
                'description': 'Contracts with multiple parties and signers',
                'supported': True,
                'caveats': ['Each party needs valid email', 'Signing order configurable'],
                'endpoints': ['/contracts/{id}/parties', '/contracts/{id}/participants']
            },
            'template_management': {
                'description': 'Create and manage contract templates',
                'supported': True,
                'caveats': ['Template creation may require admin rights', 'Template changes affect existing contracts'],
                'endpoints': ['/templates', '/template_types']
            },
            'webhook_integration': {
                'description': 'Real-time notifications and integrations',
                'supported': True,
                'caveats': ['Requires accessible webhook endpoint', 'Event types are predefined'],
                'endpoints': ['/webhooks']
            },
            'contact_management': {
                'description': 'Manage contacts and party information',
                'supported': True,
                'caveats': ['Contact validation depends on data quality', 'Duplicate detection is basic'],
                'endpoints': ['/contacts']
            },
            'contract_publishing': {
                'description': 'Publish contracts for signing',
                'supported': True,
                'caveats': ['All required fields must be completed', 'Cannot unpublish once sent'],
                'endpoints': ['/contracts/{id}/publish']
            },
            'data_extraction': {
                'description': 'Extract data from signed contracts',
                'supported': True,
                'caveats': ['Depends on template data field configuration', 'Custom fields need setup'],
                'endpoints': ['/contracts/{id}/data_fields']
            }
        }

    def assess_feasibility(self, sales_question: str) -> Optional[Dict[str, Any]]:
        """Assess technical feasibility of a sales question"""
        try:
            # Create the prompt for OpenAI
            prompt = self._create_assessment_prompt(sales_question)

            # Call OpenAI with timeout to prevent hanging
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent assessments
                max_tokens=800,
                timeout=15
            )

            # Parse the response
            result = self._parse_openai_response(response.choices[0].message.content)

            return result

        except Exception as e:
            st.warning(f"OpenAI unavailable, using fallback assessment: {str(e)[:100]}")
            return self._create_fallback_assessment(sales_question)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for OpenAI"""
        capabilities_text = "\n".join([
            f"- {cap}: {info['description']} (Caveats: {', '.join(info['caveats'])})"
            for cap, info in self.business_capabilities.items()
        ])

        return f"""You are a OneFlow API expert helping sales teams assess technical feasibility.

OneFlow is a contract management platform with these key capabilities:
{capabilities_text}

Your job is to analyze sales questions and provide clear, business-focused feasibility assessments.

Respond in JSON format with these fields:
- "feasibility": "Yes" | "No" | "Conditional"
- "confidence": "High" | "Medium" | "Low"
- "quick_answer": Brief, sales-friendly explanation
- "capabilities_used": List of relevant OneFlow capabilities
- "important_caveats": List of key limitations or requirements
- "business_impact": How caveats might affect implementation or sales
- "related_features": Other OneFlow capabilities that might be relevant
- "follow_up_questions": Questions to better understand requirements

Guidelines:
- Use business language, not technical jargon
- Be honest about limitations
- Focus on what matters for sales conversations
- Consider implementation complexity in confidence scoring
- Highlight caveats that could affect deal closing"""

    def _create_assessment_prompt(self, sales_question: str) -> str:
        """Create assessment prompt for sales question"""
        return f"""
Sales Question: "{sales_question}"

Please assess the technical feasibility of this request using OneFlow's API capabilities.

Consider:
1. Is this technically possible with OneFlow?
2. What are the key capabilities involved?
3. What important caveats should sales know about?
4. How might implementation complexity affect the sales process?
5. What related features might be valuable to mention?

Provide a structured JSON assessment.
"""

    def _parse_openai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI response and extract structured data"""
        try:
            # Try to extract JSON from the response
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            elif '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_text = response_text[start:end]
            else:
                return self._create_fallback_from_text(response_text)

            # Parse the JSON
            parsed_response = json.loads(json_text)

            # Validate and enhance the response
            return self._validate_and_enhance_assessment(parsed_response)

        except Exception as e:
            st.warning(f"Could not parse OpenAI response: {e}")
            return self._create_fallback_from_text(response_text)

    def _validate_and_enhance_assessment(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the parsed assessment"""
        # Ensure required fields exist with defaults
        assessment.setdefault('feasibility', 'Conditional')
        assessment.setdefault('confidence', 'Medium')
        assessment.setdefault('quick_answer', 'Technical assessment completed')
        assessment.setdefault('capabilities_used', [])
        assessment.setdefault('important_caveats', [])
        assessment.setdefault('business_impact', 'Standard implementation considerations apply')
        assessment.setdefault('related_features', [])
        assessment.setdefault('follow_up_questions', [])

        # Add confidence scoring explanation
        assessment['confidence_reasoning'] = self._explain_confidence(assessment)

        return assessment

    def _explain_confidence(self, assessment: Dict[str, Any]) -> str:
        """Explain the confidence level reasoning"""
        confidence = assessment.get('confidence', 'Medium')
        caveats_count = len(assessment.get('important_caveats', []))

        if confidence == 'High':
            return "Standard OneFlow capability with well-documented implementation path"
        elif confidence == 'Low':
            return f"Complex implementation with {caveats_count} important considerations"
        else:
            return f"Feasible with {caveats_count} key requirements that need attention"

    def _create_fallback_assessment(self, sales_question: str) -> Dict[str, Any]:
        """Create a fallback assessment when OpenAI is not available"""
        question_lower = sales_question.lower()

        # Simple keyword-based assessment
        if any(word in question_lower for word in ['create', 'contract', 'template']):
            return {
                'feasibility': 'Yes',
                'confidence': 'High',
                'quick_answer': 'Contract creation from templates is a core OneFlow capability.',
                'capabilities_used': ['contract_creation', 'template_management'],
                'important_caveats': [
                    'Requires a valid, active template',
                    'Template must be properly configured for intended use'
                ],
                'business_impact': 'Standard implementation - no unusual complexity',
                'related_features': ['file_management', 'multi_party_contracts'],
                'follow_up_questions': [
                    'What type of contract template do you need?',
                    'How many parties will typically be involved?'
                ],
                'confidence_reasoning': 'Core OneFlow functionality',
                'fallback_used': True
            }
        elif any(word in question_lower for word in ['pdf', 'file', 'attach', 'upload']):
            return {
                'feasibility': 'Yes',
                'confidence': 'Medium',
                'quick_answer': 'File attachments are supported, with some configuration requirements.',
                'capabilities_used': ['file_management'],
                'important_caveats': [
                    'Template must be configured to allow file attachments',
                    'Files are added after contract creation (separate API call)',
                    'File size and format restrictions apply'
                ],
                'business_impact': 'May require template reconfiguration for some use cases',
                'related_features': ['contract_creation', 'template_management'],
                'follow_up_questions': [
                    'What file types need to be supported?',
                    'Who will be uploading the files?'
                ],
                'confidence_reasoning': 'Requires template configuration considerations',
                'fallback_used': True
            }
        else:
            return {
                'feasibility': 'Conditional',
                'confidence': 'Low',
                'quick_answer': 'Need more specific information to assess feasibility.',
                'capabilities_used': [],
                'important_caveats': ['Insufficient information for detailed assessment'],
                'business_impact': 'Cannot assess without more details',
                'related_features': list(self.business_capabilities.keys())[:3],
                'follow_up_questions': [
                    'Can you provide more specific details about what you need to accomplish?',
                    'What is the main business process you\'re trying to automate?'
                ],
                'confidence_reasoning': 'Need more information for accurate assessment',
                'fallback_used': True
            }

    def _create_fallback_from_text(self, response_text: str) -> Dict[str, Any]:
        """Create assessment from unstructured OpenAI response"""
        return {
            'feasibility': 'Conditional',
            'confidence': 'Medium',
            'quick_answer': response_text[:200] + '...' if len(response_text) > 200 else response_text,
            'capabilities_used': [],
            'important_caveats': ['Assessment based on unstructured analysis'],
            'business_impact': 'Manual review recommended',
            'related_features': [],
            'follow_up_questions': ['Please rephrase your question for more accurate assessment'],
            'confidence_reasoning': 'Unstructured response format',
            'fallback_used': True
        }

    def get_capability_info(self, capability: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific capability"""
        return self.business_capabilities.get(capability)

    def list_capabilities(self) -> List[str]:
        """List all available capabilities"""
        return list(self.business_capabilities.keys())
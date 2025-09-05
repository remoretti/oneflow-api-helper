"""
Response Generator
Creates sales-friendly responses from feasibility assessments
"""
from typing import Dict, Any, List
from datetime import datetime

class ResponseGenerator:
    """Generates sales-friendly responses from feasibility assessments"""

    def __init__(self):
        self.confidence_emojis = {
            'High': '🟢',
            'Medium': '🟡',
            'Low': '🔴'
        }

        self.feasibility_emojis = {
            'Yes': '✅',
            'No': '❌',
            'Conditional': '⚠️'
        }

    def generate_response(self, assessment: Dict[str, Any], original_question: str) -> str:
        """Generate a complete sales response from assessment"""
        try:
            response_parts = []

            # Header with quick answer
            response_parts.append(self._create_header(assessment, original_question))

            # Main explanation
            response_parts.append(self._create_explanation(assessment))

            # Important caveats (if any)
            if assessment.get('important_caveats'):
                response_parts.append(self._create_caveats_section(assessment))

            # Business impact
            response_parts.append(self._create_business_impact(assessment))

            # Related features (if any)
            if assessment.get('related_features'):
                response_parts.append(self._create_related_features(assessment))

            # Follow-up questions (if any)
            if assessment.get('follow_up_questions'):
                response_parts.append(self._create_follow_up_section(assessment))

            # Confidence explanation
            response_parts.append(self._create_confidence_footer(assessment))

            return '\n\n'.join(response_parts)

        except Exception as e:
            return self._create_error_response(str(e))

    def _create_header(self, assessment: Dict[str, Any], original_question: str) -> str:
        """Create response header with quick answer"""
        feasibility = assessment.get('feasibility', 'Conditional')
        confidence = assessment.get('confidence', 'Medium')
        quick_answer = assessment.get('quick_answer', 'Assessment completed')

        feasibility_icon = self.feasibility_emojis.get(feasibility, '❓')
        confidence_icon = self.confidence_emojis.get(confidence, '🟡')

        header = f"**{feasibility_icon} Quick Answer: {feasibility}** {confidence_icon}\n\n"
        header += f"**{quick_answer}**"

        return header

    def _create_explanation(self, assessment: Dict[str, Any]) -> str:
        """Create detailed explanation section"""
        capabilities = assessment.get('capabilities_used', [])

        if not capabilities:
            return "This request can be assessed based on OneFlow's general API capabilities."

        explanation = "**How this works with OneFlow:**\n"

        # Map capabilities to user-friendly descriptions
        capability_descriptions = {
            'contract_creation': 'Create contracts from your templates',
            'file_management': 'Upload and manage documents/files',
            'multi_party_contracts': 'Handle contracts with multiple parties and signers',
            'template_management': 'Create and customize contract templates',
            'webhook_integration': 'Set up real-time notifications and integrations',
            'contact_management': 'Manage contact information and party details',
            'contract_publishing': 'Send contracts for review and signing',
            'data_extraction': 'Extract and use data from completed contracts'
        }

        for capability in capabilities:
            description = capability_descriptions.get(capability, f"Use {capability.replace('_', ' ')}")
            explanation += f"• {description}\n"

        return explanation

    def _create_caveats_section(self, assessment: Dict[str, Any]) -> str:
        """Create important caveats section"""
        caveats = assessment.get('important_caveats', [])

        if not caveats:
            return ""

        section = "**Important Considerations:**\n"
        for caveat in caveats:
            section += f"• {caveat}\n"

        return section

    def _create_business_impact(self, assessment: Dict[str, Any]) -> str:
        """Create business impact section"""
        impact = assessment.get('business_impact', '')

        if not impact or impact == 'Standard implementation considerations apply':
            return ""

        return f"**Business Impact:** {impact}"

    def _create_related_features(self, assessment: Dict[str, Any]) -> str:
        """Create related features section"""
        related = assessment.get('related_features', [])

        if not related:
            return ""

        feature_names = {
            'contract_creation': 'Contract Creation',
            'file_management': 'Document Management',
            'multi_party_contracts': 'Multi-Party Workflows',
            'template_management': 'Template Customization',
            'webhook_integration': 'API Integrations',
            'contact_management': 'Contact Database',
            'contract_publishing': 'Digital Signing',
            'data_extraction': 'Data Automation'
        }

        section = "**You might also be interested in:**\n"
        for feature in related[:3]:  # Limit to top 3
            name = feature_names.get(feature, feature.replace('_', ' ').title())
            section += f"• {name}\n"

        return section

    def _create_follow_up_section(self, assessment: Dict[str, Any]) -> str:
        """Create follow-up questions section"""
        questions = assessment.get('follow_up_questions', [])

        if not questions:
            return ""

        section = "**To better help you, I'd like to know:**\n"
        for question in questions[:3]:  # Limit to top 3
            section += f"• {question}\n"

        return section

    def _create_confidence_footer(self, assessment: Dict[str, Any]) -> str:
        """Create confidence explanation footer"""
        confidence = assessment.get('confidence', 'Medium')
        reasoning = assessment.get('confidence_reasoning', '')

        confidence_icon = self.confidence_emojis.get(confidence, '🟡')

        footer = f"**{confidence_icon} Confidence Level: {confidence}**"
        if reasoning:
            footer += f" - {reasoning}"

        # Add fallback notice if applicable
        if assessment.get('fallback_used'):
            footer += "\n\n*Note: This assessment used fallback analysis. For more detailed evaluation, please ensure OpenAI integration is available.*"

        return footer

    def _create_error_response(self, error_message: str) -> str:
        """Create error response"""
        return f"""**❌ Assessment Error**

I encountered an issue while generating this response: {error_message}

Please try rephrasing your question or contact support if the issue persists.

**You can try asking:**
• "Can OneFlow create contracts from templates?"
• "Does OneFlow support file attachments?"
• "Can we set up multi-party contracts?"
"""

    def create_summary_export(self, assessment: Dict[str, Any], original_question: str) -> Dict[str, Any]:
        """Create exportable summary of the assessment"""
        return {
            'timestamp': datetime.now().isoformat(),
            'question': original_question,
            'feasibility': assessment.get('feasibility'),
            'confidence': assessment.get('confidence'),
            'quick_answer': assessment.get('quick_answer'),
            'key_caveats': assessment.get('important_caveats', []),
            'business_impact': assessment.get('business_impact'),
            'capabilities_involved': assessment.get('capabilities_used', []),
            'follow_up_needed': len(assessment.get('follow_up_questions', [])) > 0,
            'assessment_method': 'Fallback' if assessment.get('fallback_used') else 'AI-Powered'
        }

    def format_for_email(self, assessment: Dict[str, Any], original_question: str) -> str:
        """Format assessment for email sharing"""
        summary = self.create_summary_export(assessment, original_question)

        email_body = f"""OneFlow API Feasibility Assessment

Question: {original_question}

Assessment: {summary['feasibility']} (Confidence: {summary['confidence']})

Summary: {summary['quick_answer']}

Key Considerations:
{chr(10).join([f"• {caveat}" for caveat in summary['key_caveats']])}

Business Impact: {summary['business_impact']}

Generated: {summary['timestamp']}
Assessment Method: {summary['assessment_method']}
"""

        return email_body
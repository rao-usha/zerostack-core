"""
AI Insights Service

Generates AI-powered insights from data analysis using LLMs.
Provides summaries, explanations, and follow-up recommendations for PE due diligence.
"""
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AIInsight:
    """A single AI-generated insight"""
    category: str  # summary, anomaly_explanation, recommendation, follow_up
    title: str
    content: str
    confidence: float  # 0-1 confidence in the insight
    supporting_data: Dict[str, Any]


@dataclass
class AIAnalysisReport:
    """Complete AI analysis report"""
    executive_summary: str
    key_findings: List[str]
    risk_assessment: str
    anomaly_explanations: List[AIInsight]
    recommendations: List[str]
    follow_up_questions: List[str]
    data_quality_assessment: str


class AIInsightsService:
    """Service for generating AI-powered insights from data analysis"""

    # System prompt for PE due diligence analysis
    SYSTEM_PROMPT = """You are a senior PE due diligence analyst. Your role is to analyze
financial and operational data from target companies and provide clear, actionable insights.

When analyzing data:
1. Focus on material issues that could affect deal valuation
2. Explain anomalies in business context
3. Suggest specific follow-up questions for management
4. Be direct about risks and concerns
5. Quantify impacts where possible

Your output should be professional, concise, and suitable for investment committee review."""

    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        """
        Initialize AI insights service.

        Args:
            provider: LLM provider (openai, anthropic, google, xai)
            model: Model name (uses default if not specified)
        """
        self.provider_name = provider
        self.model = model or self._get_default_model(provider)
        self._provider = None

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-pro",
            "xai": "grok-beta",
        }
        return defaults.get(provider, "gpt-4-turbo-preview")

    def _get_provider(self):
        """Lazy load the LLM provider"""
        if self._provider is None:
            try:
                from llm.providers import get_provider
                self._provider = get_provider(self.provider_name, self.model)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM provider: {e}")
                raise
        return self._provider

    async def generate_executive_summary(
        self,
        analysis_data: Dict[str, Any],
        deal_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate an executive summary of the data analysis.

        Args:
            analysis_data: Results from file analysis (anomalies, red flags, quality metrics)
            deal_context: Optional context about the PE deal

        Returns:
            Executive summary string
        """
        prompt = self._build_summary_prompt(analysis_data, deal_context)

        try:
            response = await self._call_llm(prompt)
            return response
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return self._generate_fallback_summary(analysis_data)

    async def explain_anomalies(
        self,
        anomalies: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[AIInsight]:
        """
        Generate business-context explanations for detected anomalies.

        Args:
            anomalies: List of detected anomalies
            context: Additional context (industry, company size, etc.)

        Returns:
            List of AIInsight objects with explanations
        """
        if not anomalies:
            return []

        prompt = self._build_anomaly_explanation_prompt(anomalies, context)

        try:
            response = await self._call_llm(prompt)
            return self._parse_anomaly_explanations(response, anomalies)
        except Exception as e:
            logger.error(f"Failed to explain anomalies: {e}")
            return self._generate_fallback_anomaly_explanations(anomalies)

    async def generate_follow_up_questions(
        self,
        analysis_data: Dict[str, Any],
        red_flags: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Generate specific follow-up questions for target company management.

        Args:
            analysis_data: Full analysis results
            red_flags: Detected red flags

        Returns:
            List of follow-up questions
        """
        prompt = self._build_follow_up_prompt(analysis_data, red_flags)

        try:
            response = await self._call_llm(prompt)
            return self._parse_questions(response)
        except Exception as e:
            logger.error(f"Failed to generate follow-up questions: {e}")
            return self._generate_fallback_questions(red_flags)

    async def generate_full_report(
        self,
        file_analysis: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        red_flags: List[Dict[str, Any]],
        trend_analysis: Optional[Dict[str, Any]] = None,
        reconciliation: Optional[Dict[str, Any]] = None,
        deal_context: Optional[Dict[str, Any]] = None,
    ) -> AIAnalysisReport:
        """
        Generate a comprehensive AI analysis report.

        Args:
            file_analysis: Basic file analysis results
            anomalies: Detected anomalies
            red_flags: Detected red flags
            trend_analysis: Trend analysis results
            reconciliation: Reconciliation results
            deal_context: Deal context information

        Returns:
            AIAnalysisReport with full analysis
        """
        # Compile all data
        analysis_data = {
            "file_analysis": file_analysis,
            "anomalies": anomalies,
            "red_flags": red_flags,
            "trend_analysis": trend_analysis,
            "reconciliation": reconciliation,
        }

        prompt = self._build_full_report_prompt(analysis_data, deal_context)

        try:
            response = await self._call_llm(prompt, max_tokens=4000)
            return self._parse_full_report(response, analysis_data)
        except Exception as e:
            logger.error(f"Failed to generate full report: {e}")
            return self._generate_fallback_report(analysis_data)

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> str:
        """Call the LLM and return the response"""
        provider = self._get_provider()

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        full_response = ""
        async for event in provider.stream_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            if event["type"] == "delta":
                full_response += event["content"]
            elif event["type"] == "error":
                raise Exception(event["error"])

        return full_response.strip()

    def _build_summary_prompt(
        self,
        analysis_data: Dict[str, Any],
        deal_context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for executive summary generation"""
        context_str = ""
        if deal_context:
            context_str = f"""
Deal Context:
- Target Company: {deal_context.get('target_company', 'Unknown')}
- Industry: {deal_context.get('industry', 'Unknown')}
- Deal Stage: {deal_context.get('deal_stage', 'Unknown')}
"""

        # Extract key metrics
        quality_score = analysis_data.get('overall_quality_score', 'N/A')
        total_rows = analysis_data.get('total_rows', 0)
        anomaly_count = len(analysis_data.get('anomalies', []))
        red_flag_count = len(analysis_data.get('red_flags', []))
        categories = analysis_data.get('detected_categories', [])

        return f"""Analyze the following PE due diligence data and provide a concise executive summary (2-3 paragraphs).
{context_str}
Data Overview:
- Total Records: {total_rows:,}
- Data Quality Score: {quality_score}/100
- Detected Data Categories: {', '.join(categories) if categories else 'None identified'}
- Anomalies Detected: {anomaly_count}
- Red Flags Detected: {red_flag_count}

Key Issues:
{json.dumps(analysis_data.get('potential_issues', []), indent=2)}

Red Flags:
{json.dumps([rf.get('title', 'Unknown') for rf in analysis_data.get('red_flags', [])[:5]], indent=2)}

Provide an executive summary that:
1. Assesses overall data quality and reliability
2. Highlights the most significant findings
3. Indicates the level of concern (low/medium/high)
"""

    def _build_anomaly_explanation_prompt(
        self,
        anomalies: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for anomaly explanations"""
        context_str = ""
        if context:
            context_str = f"Industry: {context.get('industry', 'Unknown')}\n"

        anomaly_details = []
        for i, anomaly in enumerate(anomalies[:10], 1):  # Limit to 10
            anomaly_details.append(f"""
Anomaly {i}:
- Type: {anomaly.get('anomaly_type', 'Unknown')}
- Column: {anomaly.get('column_name', 'Unknown')}
- Title: {anomaly.get('title', 'Unknown')}
- Description: {anomaly.get('description', 'No description')}
- Evidence: {json.dumps(anomaly.get('evidence', {}), indent=2)}
""")

        return f"""Analyze these data anomalies and explain them in business context.
{context_str}
{chr(10).join(anomaly_details)}

For each anomaly, provide:
1. Most likely business explanation
2. Alternative explanations to investigate
3. Potential impact on deal valuation
4. Recommended verification steps

Format your response as a numbered list matching the anomaly numbers above.
"""

    def _build_follow_up_prompt(
        self,
        analysis_data: Dict[str, Any],
        red_flags: List[Dict[str, Any]],
    ) -> str:
        """Build prompt for follow-up questions"""
        red_flag_summary = []
        for rf in red_flags[:10]:
            red_flag_summary.append(f"- {rf.get('title', 'Unknown')}: {rf.get('description', '')[:200]}")

        return f"""Based on the following red flags detected in due diligence data, generate specific
follow-up questions for target company management.

Data Quality Score: {analysis_data.get('overall_quality_score', 'N/A')}/100
Categories Detected: {', '.join(analysis_data.get('detected_categories', []))}

Red Flags:
{chr(10).join(red_flag_summary)}

Generate 5-10 specific, pointed questions that:
1. Address each major red flag directly
2. Seek explanations and supporting documentation
3. Are suitable for a management meeting
4. Help validate or refute concerns

Format as a numbered list of questions only.
"""

    def _build_full_report_prompt(
        self,
        analysis_data: Dict[str, Any],
        deal_context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for full report generation"""
        file_analysis = analysis_data.get('file_analysis', {})
        anomalies = analysis_data.get('anomalies', [])
        red_flags = analysis_data.get('red_flags', [])

        context_str = ""
        if deal_context:
            context_str = f"""
Target: {deal_context.get('target_company', 'Unknown')}
Industry: {deal_context.get('industry', 'Unknown')}
"""

        return f"""Generate a comprehensive PE due diligence data analysis report.
{context_str}
DATA OVERVIEW:
- Files Analyzed: {file_analysis.get('filename', 'Unknown')}
- Total Records: {file_analysis.get('total_rows', 0):,}
- Quality Score: {file_analysis.get('overall_quality_score', 'N/A')}/100
- Data Categories: {', '.join(file_analysis.get('detected_data_categories', []))}

ANOMALIES DETECTED ({len(anomalies)}):
{json.dumps([{'type': a.get('anomaly_type'), 'title': a.get('title'), 'severity': a.get('severity')} for a in anomalies[:10]], indent=2)}

RED FLAGS DETECTED ({len(red_flags)}):
{json.dumps([{'type': rf.get('flag_type'), 'title': rf.get('title'), 'severity': rf.get('severity'), 'category': rf.get('category')} for rf in red_flags[:10]], indent=2)}

Generate a report with the following sections:
1. EXECUTIVE SUMMARY (2-3 paragraphs)
2. KEY FINDINGS (bullet points)
3. RISK ASSESSMENT (high/medium/low with explanation)
4. DATA QUALITY ASSESSMENT (brief assessment)
5. RECOMMENDED FOLLOW-UP ACTIONS (numbered list)
6. QUESTIONS FOR MANAGEMENT (numbered list)

Be direct, specific, and focus on material issues.
"""

    def _parse_anomaly_explanations(
        self,
        response: str,
        anomalies: List[Dict[str, Any]],
    ) -> List[AIInsight]:
        """Parse LLM response into AIInsight objects"""
        insights = []
        for i, anomaly in enumerate(anomalies[:10]):
            insights.append(AIInsight(
                category="anomaly_explanation",
                title=anomaly.get('title', f'Anomaly {i+1}'),
                content=response,  # In practice, would parse specific sections
                confidence=0.7,
                supporting_data=anomaly.get('evidence', {}),
            ))
        return insights

    def _parse_questions(self, response: str) -> List[str]:
        """Parse questions from LLM response"""
        lines = response.strip().split('\n')
        questions = []
        for line in lines:
            line = line.strip()
            # Remove numbering
            if line and line[0].isdigit():
                line = line.lstrip('0123456789.)')
            line = line.strip()
            if line and line.endswith('?'):
                questions.append(line)
        return questions if questions else [response]

    def _parse_full_report(
        self,
        response: str,
        analysis_data: Dict[str, Any],
    ) -> AIAnalysisReport:
        """Parse full report from LLM response"""
        # Simple parsing - in production would use more sophisticated parsing
        sections = response.split('\n\n')

        return AIAnalysisReport(
            executive_summary=self._extract_section(response, "EXECUTIVE SUMMARY"),
            key_findings=self._extract_bullet_points(response, "KEY FINDINGS"),
            risk_assessment=self._extract_section(response, "RISK ASSESSMENT"),
            anomaly_explanations=[],  # Would parse from response
            recommendations=self._extract_numbered_list(response, "RECOMMENDED"),
            follow_up_questions=self._extract_numbered_list(response, "QUESTIONS"),
            data_quality_assessment=self._extract_section(response, "DATA QUALITY"),
        )

    def _extract_section(self, text: str, header: str) -> str:
        """Extract a section from the response"""
        lines = text.split('\n')
        capturing = False
        section = []

        for line in lines:
            if header.upper() in line.upper():
                capturing = True
                continue
            elif capturing:
                if line.strip() and line.strip()[0].isdigit() and '.' in line[:3]:
                    break  # Hit next section
                if any(h in line.upper() for h in ['KEY FINDINGS', 'RISK ASSESSMENT', 'DATA QUALITY', 'RECOMMENDED', 'QUESTIONS']):
                    if header.upper() not in line.upper():
                        break
                section.append(line)

        return '\n'.join(section).strip()

    def _extract_bullet_points(self, text: str, header: str) -> List[str]:
        """Extract bullet points from a section"""
        section = self._extract_section(text, header)
        bullets = []
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                bullets.append(line.lstrip('-*• ').strip())
        return bullets

    def _extract_numbered_list(self, text: str, header: str) -> List[str]:
        """Extract numbered list from a section"""
        section = self._extract_section(text, header)
        items = []
        for line in section.split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                items.append(line.lstrip('0123456789.) ').strip())
        return items

    # Fallback methods when LLM is unavailable

    def _generate_fallback_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a basic summary without LLM"""
        quality_score = analysis_data.get('overall_quality_score', 0)
        anomaly_count = len(analysis_data.get('anomalies', []))
        red_flag_count = len(analysis_data.get('red_flags', []))

        severity = "low"
        if red_flag_count > 5 or quality_score < 50:
            severity = "high"
        elif red_flag_count > 2 or quality_score < 70:
            severity = "medium"

        return f"""Data Analysis Summary

The analyzed data has an overall quality score of {quality_score}/100.
Analysis detected {anomaly_count} statistical anomalies and {red_flag_count} PE-specific red flags.

Risk Level: {severity.upper()}

Review the detailed findings below for specific issues requiring attention."""

    def _generate_fallback_anomaly_explanations(
        self,
        anomalies: List[Dict[str, Any]],
    ) -> List[AIInsight]:
        """Generate basic anomaly explanations without LLM"""
        insights = []
        for anomaly in anomalies[:10]:
            insights.append(AIInsight(
                category="anomaly_explanation",
                title=anomaly.get('title', 'Unknown Anomaly'),
                content=anomaly.get('description', 'No description available'),
                confidence=0.5,
                supporting_data=anomaly.get('evidence', {}),
            ))
        return insights

    def _generate_fallback_questions(
        self,
        red_flags: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate basic follow-up questions without LLM"""
        questions = []
        for rf in red_flags[:10]:
            title = rf.get('title', 'Unknown issue')
            questions.append(f"Can you explain the {title}?")
            questions.append(f"What documentation supports the data related to {title}?")
        return questions[:10]

    def _generate_fallback_report(
        self,
        analysis_data: Dict[str, Any],
    ) -> AIAnalysisReport:
        """Generate basic report without LLM"""
        anomalies = analysis_data.get('anomalies', [])
        red_flags = analysis_data.get('red_flags', [])
        file_analysis = analysis_data.get('file_analysis', {})

        quality_score = file_analysis.get('overall_quality_score', 0)

        return AIAnalysisReport(
            executive_summary=self._generate_fallback_summary(analysis_data),
            key_findings=[
                f"Data quality score: {quality_score}/100",
                f"Detected {len(anomalies)} anomalies",
                f"Detected {len(red_flags)} red flags",
            ],
            risk_assessment="Manual review required - AI analysis unavailable",
            anomaly_explanations=self._generate_fallback_anomaly_explanations(anomalies),
            recommendations=[
                "Review all detected anomalies",
                "Investigate red flags with target company",
                "Request supporting documentation",
            ],
            follow_up_questions=self._generate_fallback_questions(red_flags),
            data_quality_assessment=f"Data quality score: {quality_score}/100",
        )


# Convenience function for quick insights
async def get_quick_insights(
    analysis_results: Dict[str, Any],
    provider: str = "openai",
) -> Dict[str, Any]:
    """
    Get quick AI insights from analysis results.

    Args:
        analysis_results: Dict with anomalies, red_flags, and file_analysis
        provider: LLM provider to use

    Returns:
        Dict with summary, key_findings, and recommendations
    """
    try:
        service = AIInsightsService(provider=provider)

        summary = await service.generate_executive_summary(analysis_results)
        questions = await service.generate_follow_up_questions(
            analysis_results,
            analysis_results.get('red_flags', [])
        )

        return {
            "summary": summary,
            "follow_up_questions": questions,
            "generated": True,
        }
    except Exception as e:
        logger.error(f"Quick insights generation failed: {e}")
        return {
            "summary": "AI insights unavailable",
            "follow_up_questions": [],
            "generated": False,
            "error": str(e),
        }

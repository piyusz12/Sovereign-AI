import logging

logger = logging.getLogger(__name__)

class ContextBudgeter:
    """
    Prevents large context windows from triggering VRAM OOMs.
    """
    def __init__(self, max_total_tokens: int = 8192):
        self.max_total_tokens = max_total_tokens
        
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation: 1 token ~ 4 characters"""
        return len(text) // 4
        
    def trim_context(self, system_prompt: str, user_request: str, retrieved_docs: list[str], tool_results: str) -> tuple[str, str]:
        """
        Trims retrieved docs and tool results to fit within the budget.
        Returns (trimmed_docs, trimmed_tool_results).
        """
        sys_tokens = self.estimate_tokens(system_prompt)
        user_tokens = self.estimate_tokens(user_request)
        
        # Reserve some for the output
        output_reserve = 1000
        budget = self.max_total_tokens - (sys_tokens + user_tokens + output_reserve)
        
        if budget < 1000:
            logger.warning(f"Context budget critically low: {budget} tokens available.")
            
        # Allocate half budget to docs, half to tool results
        docs_budget = budget // 2
        tool_budget = budget - docs_budget
        
        # Process tool results
        tool_str = tool_results
        if self.estimate_tokens(tool_str) > tool_budget:
            logger.info("Trimming tool results to fit context budget")
            allowed_chars = tool_budget * 4
            tool_str = tool_str[:allowed_chars] + "\n...[TRUNCATED FOR MEMORY]..."
            
        # Process docs
        final_docs = []
        current_doc_tokens = 0
        for doc in retrieved_docs:
            dt = self.estimate_tokens(doc)
            if current_doc_tokens + dt > docs_budget:
                logger.info("Dropping lower-ranked documents to fit context budget")
                break
            final_docs.append(doc)
            current_doc_tokens += dt
            
        return "\n".join(final_docs), tool_str

context_budgeter = ContextBudgeter()

from llm import OpenAIClient



MAX_TOKENS = 1000




class SessionManager:
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client

    
    def investigate(self, problem_description: str, investigation_cycles: int = 50, max_tokens: int = MAX_TOKENS) -> str:
        
        conversation_history = []

        conversation_history.append({
            "role": "user",
            "content": problem_description
        })
        
        tokens_expended = 0

        for i in range(investigation_cycles):

            choice, usage = self.openai_client.get_response(
                messages=conversation_history
            )
            
            message = choice["message"]
            finish_reason = choice["finish_reason"]

            conversation_history.append(message)
            tokens_expended += usage["total_tokens"] #TODO: Add more price-reflective breakout

            if finish_reason == "tool_calls":
                for tool_call in message["tool_calls"]:
                    import json
                    
                    if isinstance(tool_call["function"]["arguments"], str):
                        tool_call["function"]["arguments"] = json.loads(tool_call["function"]["arguments"])
                    
                    conversation_history.append(self.openai_client.execute_tool_call(tool_call))

            if tokens_expended >= max_tokens or finish_reason == "stop":
                break


        return [self.openai_client.get_system_prompt()] + conversation_history
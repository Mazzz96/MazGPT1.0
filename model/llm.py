from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch
import os

class LocalLLM:
    BASE_SYSTEM_PROMPT = (
        """
        MazGPT System Prompt (v1.0)
        You are MazGPT, an empathetic, creative, and highly capable AI assistant. Your core values are helpfulness, friendliness, and deep contextual awareness. You:
        - Remember and use long-term and recent context to personalize every reply.
        - Are always creative, witty, and engaging, but never robotic or generic.
        - Use humor, analogies, and vivid language when appropriate.
        - Can summarize, reason, and break down complex topics for any audience.
        - Support and reply in multiple languages if the user requests or context suggests.
        - Are a world-class assistant for knowledge work, coding, research, and creative tasks.
        - Always act with empathy, patience, and encouragement.
        - Never claim to be human, and always disclose you are an AI if asked.
        - Respect user preferences, project context, and privacy.
        - If you don’t know, say so honestly and offer to help find out.
        - Avoid refusals unless required by law, ethics, or safety.
        - Always comply with Meta’s Acceptable Use Policy and community guidelines.
        """
    )

    def __init__(self, model_name, device=None):
        # If model_name is a local path, use it directly
        if os.path.isdir(model_name):
            model_path = model_name
        else:
            model_path = model_name  # fallback, but should always be a local path now
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def build_system_prompt(self, language="en", tone="friendly"):
        tone_map = {
            "friendly": "Be warm, encouraging, and supportive.",
            "formal": "Use a formal, professional tone.",
            "concise": "Be brief and to the point, but still helpful.",
            "playful": "Be witty, playful, and use light humor.",
        }
        lang_map = {
            "en": "Reply in English.",
            "es": "Responde en español.",
            "fr": "Réponds en français.",
            "de": "Antworte auf Deutsch.",
            "zh": "请用中文回答。",
            "ar": "أجب باللغة العربية.",
        }
        tone_instruction = tone_map.get(tone, "")
        lang_instruction = lang_map.get(language, "")
        return self.BASE_SYSTEM_PROMPT + "\n" + tone_instruction + "\n" + lang_instruction

    def generate(self, prompt, max_new_tokens=128, stream=False, language="en", tone="friendly"):
        full_prompt = self.build_system_prompt(language, tone) + "\n" + prompt
        input_ids = self.tokenizer(full_prompt, return_tensors="pt").input_ids.to(self.device)
        if stream:
            streamer = TextStreamer(self.tokenizer, skip_prompt=True)
            self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                streamer=streamer,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        else:
            output = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            return self.tokenizer.decode(output[0], skip_special_tokens=True)[len(full_prompt):]

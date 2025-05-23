import yaml
from model.llm import LocalLLM
import os

class SkillRouter:
    def __init__(self, config_path="model/model_config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.models = {}
        for m in self.config["models"]:
            # Always use the local path from config
            self.models[m["name"]] = LocalLLM(model_name=m["path"])
        self.skill_map = self._build_skill_map()

    def _build_skill_map(self):
        skill_map = {}
        for m in self.config["models"]:
            for skill in m["skills"]:
                skill_map.setdefault(skill, []).append(m["name"])
        return skill_map

    def classify(self, query):
        q = query.lower()
        if any(w in q for w in ["code", "python", "function", "bug", "error"]):
            return "code"
        if any(w in q for w in ["image", "vision", ".png", ".jpg"]):
            return "image"
        if any(w in q for w in ["translate", "spanish", "chinese", "arabic"]):
            return "multilingual"
        if any(w in q for w in ["math", "calculate", "reason"]):
            return "reasoning"
        return "general"

    def route(self, query):
        skill = self.classify(query)
        models = self.skill_map.get(skill, self.skill_map.get("general", []))
        ens = self.config.get("ensembling", {})
        if ens.get("enabled"):
            for strat in ens.get("strategies", []):
                if strat["skill"] == skill:
                    outputs = [self.models[m].generate(query) for m in strat["models"]]
                    if strat["method"] == "best":
                        return max(outputs, key=len)
                    elif strat["method"] == "first":
                        return outputs[0]
        return self.models[models[0]].generate(query) if models else "No model available for this skill."

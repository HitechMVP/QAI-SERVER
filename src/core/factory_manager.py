import json
import os
import logging

logger = logging.getLogger("FactoryManager")

class FactoryManager:
    def __init__(self, config_path="configs/factory.json"):
        self.config_path = config_path
        self.structure = {}   
        self.valid_devices = set() 
        self.device_to_line = {}  
        
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.structure = json.load(f)
            
            self.valid_devices.clear()
            self.device_to_line.clear()
            
            for line_id, info in self.structure.items():
                for dev_id in info.get('devices', []):
                    self.valid_devices.add(dev_id)
                    self.device_to_line[dev_id] = line_id
            
            logger.info(f"Loaded factory config: {len(self.structure)} lines, {len(self.valid_devices)} devices.")
            
        except Exception as e:
            logger.error(f"Failed to load factory config: {e}")

    def is_allowed(self, device_id):
        return device_id in self.valid_devices

    def get_line_info(self, line_id):
        return self.structure.get(line_id, {})

    def get_all_lines(self):
        return self.structure

factory_manager = FactoryManager()
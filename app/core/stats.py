# stats.py

import json
import os



class Stat():
    def __init__(self,name):
        self.stat = name
        self.level = 1
        self.xp = 0
        self.xp_required = 100

    def add_xp(self,amount):
        if amount <= 0:
             return
        self.xp += amount
        self.update_level()

    def update_xp_required(self):
        return 100 + (self.level - 1) * 50
    
    def update_level(self):
        while self.xp >= self.xp_required:
            self.level += 1
            self.xp -= self.xp_required
            self.xp_required = self.update_xp_required()

def to_file(stats,filename = "app/storage/stats.json"):
        stat_dict = {
            name:{
                "Level": stat.level,
                "XP":stat.xp,
                "xp-required":stat.xp_required

            }for name, stat in stats.items()
        }

        os.makedirs(os.path.dirname(filename),exist_ok=True)
        
        with open(filename,'w')as f :
            json.dump(stat_dict,f,indent=4)

def from_file(filename = "app/storage/stats.json"):
     if not os.path.exists(filename):
          return
     with open(filename,'r')as f :
          data = json.load(f)
          
     for name,saved in data.items():
          if name in stats:
               stat = stats[name]
               stat.level = saved.get("Level",1)
               stat.xp = saved.get("XP",0)
               stat.xp_required = saved.get("xp-required",100)
    


stats = {
    "Strength":Stat(name="Strength"),
    "Vitality":Stat(name="Vitality"),
    "Intelligence":Stat(name="Intelligence"),
    "Willpower":Stat(name="Willpower"),
    "Skills":Stat(name="Skills")
}

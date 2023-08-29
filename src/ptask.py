class PTask:
    def __init__(self, id, ins_count, period, priority):
        self.id = id
        self.ins_count = ins_count
        self.period = period
        self.priority = priority

    def needed_resource(self):
        return self.ins_count / self.period
    
    def __str__(self):
        return f'PTask - id: {self.id}, instruction count: {self.ins_count}, period: {self.period}, priority: {self.priority}'
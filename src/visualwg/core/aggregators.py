'''
Created on Mar 23, 2011

@author: vgapeyev
'''


class AggregatorArray:
    
    def __init__(self, spec_list):
        self.aggs = {}
        for (name, type, summarizer) in spec_list:
            if type == "real" and summarizer == "mean":
                self.aggs[name] = RealMeanAggregator()
            elif type == "code" and summarizer == "concat":
                self.aggs[name] = EnumConcatAggregator()    
            elif type == "int" and summarizer == "concat":  #TODO proper type and aggregator for INT
                self.aggs[name] = EnumConcatAggregator()    
            else:
                raise ValueError("Aggregator (%s, %s) is not supported" % (type, summarizer))
        
    def reset(self):
        for a in self.aggs.values():
            a.reset()
            
    def __getitem__(self, name):
        return self.aggs[name]
                
    def invalidity_in_row(self):
        return any([ agg.was_last_invalid() for (_, agg) in self.aggs.items()])
            
    def get_invalid_row_part(self):
        return dict([ (name, agg.get_last()) for (name, agg) in self.aggs.items() if agg.was_last_invalid() ])
        
    def get_aggregate_row(self):
        return dict([ (name, agg.agg_value()) for (name, agg) in self.aggs.items() ])
        
        
class RealMeanAggregator:
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.sum = 0.0
        self.count = 0
        self.last = None
        self.__was_last_invalid = False
                
    def add(self, dpoint):
        self.last = dpoint
        if dpoint != None:
            try:
                r = float(dpoint)
                self.sum += r
                self.count += 1
                self.__was_last_invalid = False
            except ValueError:
                self.__was_last_invalid = True
        else: 
            self.__was_last_invalid = False

    def was_last_invalid(self):
        return self.__was_last_invalid
    
    def get_last(self):
        return self.last
                
    def agg_value(self):
        if self.count == 0:
            return None
        else: 
            return self.sum / self.count
        
        
class EnumConcatAggregator:
    def __init__(self):
        self.concat_symbol = "|"
        self.reset()
        
    def reset(self):
        self.valset = set([])
        self.last = None
        self.__was_last_invalid = False
                
    def add(self, dpoint):
        self.last = dpoint
        if dpoint != None:
            try:
                r = dpoint.strip()
                self.valset.add(r)                
                self.__was_last_invalid = False
            except ValueError:
                self.__was_last_invalid = True
        else: 
            self.__was_last_invalid = False

    def was_last_invalid(self):
        return self.__was_last_invalid
    
    def get_last(self):
        return self.last
                
    def agg_value(self):
        if len(self.valset) == 0:
            return None
        else: 
            lst = list(self.valset)
            lst.sort()
            return  self.concat_symbol.join(lst)
     
    
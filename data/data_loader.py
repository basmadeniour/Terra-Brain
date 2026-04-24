import csv
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class DataLoader:
    
    LAND_TYPE_SUITABILITY = {
        'park': {'plantable': True, 'base_score': 40, 'weight': 1.2},
        'forest': {'plantable': True, 'base_score': 40, 'weight': 1.3},
        'agricultural': {'plantable': True, 'base_score': 40, 'weight': 1.1},
        'grass': {'plantable': True, 'base_score': 35, 'weight': 1.0},
        'meadow': {'plantable': True, 'base_score': 35, 'weight': 1.0},
        'garden': {'plantable': True, 'base_score': 35, 'weight': 1.1},
        'empty': {'plantable': True, 'base_score': 5, 'weight': 0.8},
        'residential': {'plantable': True, 'base_score': 10, 'weight': 0.6},
        'greenfield': {'plantable': True, 'base_score': 30, 'weight': 1.0},
        'tundra': {'plantable': False, 'base_score': 0, 'weight': 0.2},
        'rainforest': {'plantable': True, 'base_score': 35, 'weight': 1.1},
        'wetland': {'plantable': True, 'base_score': 25, 'weight': 0.9},
        'desert': {'plantable': False, 'base_score': 0, 'weight': 0.1},
        'commercial': {'plantable': False, 'base_score': -20, 'weight': 0.3},
        'industrial': {'plantable': False, 'base_score': -50, 'weight': 0.1},
        'road': {'plantable': False, 'base_score': -60, 'weight': 0.0},
        'building': {'plantable': False, 'base_score': -70, 'weight': 0.0},
        'water': {'plantable': False, 'base_score': -100, 'weight': 0.0},
        'plantable_empty': {'plantable': True, 'base_score': 30, 'weight': 1.0},
        'already_planted': {'plantable': True, 'base_score': 35, 'weight': 1.1},
        'barren': {'plantable': False, 'base_score': -10, 'weight': 0.3},
        'unknown': {'plantable': True, 'base_score': 0, 'weight': 0.5},
    }
    
    VALIDATION_RULES = {
        'latitude': {'min': -90, 'max': 90},
        'longitude': {'min': -180, 'max': 180},
        'pollution': {'min': 0, 'max': 500},
        'temperature': {'min': -50, 'max': 60},
        'score': {'min': 0, 'max': 200},
    }
    
    BENEFIT_WEIGHTS = {'pollution': 0.5, 'temperature': 0.3, 'base_score': 0.2}
    IDEAL_TEMPERATURE = 22
    
    def __init__(self, verbose: bool = True, dedup_precision: int = 5):
        self.verbose = verbose
        self.dedup_precision = dedup_precision
        self.stats = {
            'total_loaded': 0, 'valid': 0, 'invalid': 0,
            'duplicates_removed': 0, 'enriched': 0, 'normalized': False,
        }
    
    def _log(self, msg: str, level: str = "INFO"):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DataLoader] [{level}] {msg}")
    
    def _safe_float(self, val: Any, default: float = 0.0) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def _create_standard_point(self, row: Dict) -> Dict:
        lat, lon = self._safe_float(row.get('latitude', 0)), self._safe_float(row.get('longitude', 0))
        land_type = row.get('land_type', 'unknown').lower()
        suit = self.LAND_TYPE_SUITABILITY.get(land_type, self.LAND_TYPE_SUITABILITY['unknown'])
        
        return {
            'id': hashlib.md5(f"{lat:.6f}_{lon:.6f}".encode()).hexdigest()[:8],
            'location': (lat, lon),
            'pollution': self._safe_float(row.get('pollution', 50)),
            'temperature': self._safe_float(row.get('temperature', 25)),
            'land_type': land_type,
            'is_plantable': suit['plantable'],
            'is_valid_location': suit['plantable'],
            'has_tree': row.get('has_tree', False),
            'is_factory': row.get('is_factory', False),
            'score': self._safe_float(row.get('score', 0)),
            'base_score': suit['base_score'],
            'weight': suit['weight'],
            'source': row.get('source', 'csv'),
            'timestamp': datetime.now().isoformat()
        }
    
    def _is_valid_point(self, point: Dict) -> Tuple[bool, Optional[str]]:
        lat, lon = point['location']
        rules = self.VALIDATION_RULES
        
        if not (rules['latitude']['min'] <= lat <= rules['latitude']['max']):
            return False, f"Invalid latitude: {lat}"
        if not (rules['longitude']['min'] <= lon <= rules['longitude']['max']):
            return False, f"Invalid longitude: {lon}"
        
        if point['pollution'] < rules['pollution']['min']:
            return False, f"Pollution too low: {point['pollution']}"
        if point['pollution'] > rules['pollution']['max']:
            point['pollution'] = rules['pollution']['max']
        
        if point['temperature'] < rules['temperature']['min']:
            return False, f"Temperature too low: {point['temperature']}"
        if point['temperature'] > rules['temperature']['max']:
            point['temperature'] = rules['temperature']['max']
        
        return True, None
    
    def _get_location_key(self, point: Dict) -> str:
        lat, lon = point['location']
        return f"{round(lat, self.dedup_precision)}_{round(lon, self.dedup_precision)}"
    
    def remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for p in data:
            key = self._get_location_key(p)
            if key not in seen:
                seen.add(key)
                unique.append(p)
            else:
                self.stats['duplicates_removed'] += 1
        self._log(f"Removed {self.stats['duplicates_removed']} duplicates, {len(unique)} unique")
        return unique
    
    def normalize_data(self, data: List[Dict]) -> List[Dict]:
        if not data:
            return data
        
        max_pollution = max(p['pollution'] for p in data)
        max_temp_diff = max(abs(p['temperature'] - self.IDEAL_TEMPERATURE) for p in data)
        max_score = max(p['score'] for p in data)
        
        for p in data:
            p['pollution_norm'] = p['pollution'] / max_pollution
            p['temperature_norm'] = abs(p['temperature'] - self.IDEAL_TEMPERATURE) / max_temp_diff
            p['score_norm'] = p['score'] / max_score
        
        self.stats['normalized'] = True
        return data
    
    def _is_normalized(self, data: List[Dict]) -> bool:
        return bool(data and 'pollution_norm' in data[0])
    
    def enrich_data(self, data: List[Dict]) -> List[Dict]:
        if not self._is_normalized(data) and data:
            data = self.normalize_data(data)
        
        for p in data:
            pollution_factor = (1 - p.get('pollution_norm', 0.5)) ** 2 * 50
            temp_factor = (1 - p.get('temperature_norm', 0.5)) * 30
            base_factor = p.get('base_score', 0)
            weight = p.get('weight', 1.0)
            
            p['computed_benefit'] = (
                pollution_factor * self.BENEFIT_WEIGHTS['pollution'] +
                temp_factor * self.BENEFIT_WEIGHTS['temperature'] +
                base_factor * self.BENEFIT_WEIGHTS['base_score']
            ) * weight
            
            p['is_valid_location'] = (
                p.get('is_plantable', False) and 
                not p.get('has_tree', False) and 
                not p.get('is_factory', False)
            )
            self.stats['enriched'] += 1
        
        return data
    
    def filter_plantable(self, data: List[Dict]) -> List[Dict]:
        result = [p for p in data if p.get('is_valid_location', False)]
        self._log(f"Filtered: {len(result)} plantable out of {len(data)}")
        return result
    
    def get_statistics(self, data: List[Dict]) -> Dict:
        if not data:
            return {'error': 'No data'}
        
        plantable = [p for p in data if p.get('is_valid_location', False)]
        land_types = {}
        for p in data:
            lt = p.get('land_type', 'unknown')
            land_types[lt] = land_types.get(lt, 0) + 1
        
        return {
            'total_points': len(data),
            'plantable_count': len(plantable),
            'non_plantable_count': len(data) - len(plantable),
            'land_type_distribution': land_types,
            'unique_land_types': len(land_types),
            'avg_pollution': sum(p['pollution'] for p in data) / len(data),
            'avg_temperature': sum(p['temperature'] for p in data) / len(data),
            'avg_benefit': sum(p.get('computed_benefit', 0) for p in data) / len(data),
            'duplicates_removed': self.stats['duplicates_removed'],
            'normalized': self.stats['normalized'],
        }
    
    def load_from_csv(self, filename: str, validate: bool = True, 
                      normalize: bool = True, enrich: bool = True,
                      remove_dups: bool = True) -> List[Dict]:
        self._log(f"Loading from CSV: {filename}")
        raw_data = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for row_num, row in enumerate(csv.DictReader(f), 2):
                    try:
                        raw_data.append(self._create_standard_point(row))
                    except (ValueError, KeyError):
                        continue
        except FileNotFoundError:
            self._log(f"File not found: {filename}", "ERROR")
            return []
        except Exception as e:
            self._log(f"Error: {e}", "ERROR")
            return []
        
        self.stats['total_loaded'] = len(raw_data)
        
        if validate:
            valid = []
            for p in raw_data:
                is_valid, _ = self._is_valid_point(p)
                if is_valid:
                    valid.append(p)
                else:
                    self.stats['invalid'] += 1
            raw_data = valid
        
        if remove_dups:
            raw_data = self.remove_duplicates(raw_data)
        if normalize:
            raw_data = self.normalize_data(raw_data)
        if enrich:
            raw_data = self.enrich_data(raw_data)
        
        self.stats['valid'] = len(raw_data)
        return raw_data
    
    def load_from_json(self, filename: str, **kwargs) -> List[Dict]:
        self._log(f"Loading from JSON: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._log(f"Error: {e}", "ERROR")
            return []
        
        standardized = []
        for item in data:
            if 'location' in item:
                if isinstance(item['location'], (list, tuple)):
                    lat, lon = item['location']
                elif isinstance(item['location'], dict):
                    lat = item['location'].get('lat', item['location'].get('latitude', 0))
                    lon = item['location'].get('lon', item['location'].get('longitude', 0))
                else:
                    continue
            else:
                lat, lon = item.get('latitude', item.get('lat', 0)), item.get('longitude', item.get('lon', 0))
            
            land_type = item.get('land_type', 'unknown').lower()
            suit = self.LAND_TYPE_SUITABILITY.get(land_type, self.LAND_TYPE_SUITABILITY['unknown'])
            
            standardized.append({
                'id': hashlib.md5(f"{float(lat):.6f}_{float(lon):.6f}".encode()).hexdigest()[:8],
                'location': (float(lat), float(lon)),
                'pollution': self._safe_float(item.get('pollution', 50)),
                'temperature': self._safe_float(item.get('temperature', 25)),
                'land_type': land_type,
                'is_plantable': suit['plantable'],
                'is_valid_location': suit['plantable'],
                'has_tree': item.get('has_tree', False),
                'is_factory': item.get('is_factory', False),
                'score': self._safe_float(item.get('score', 0)),
                'base_score': suit['base_score'],
                'weight': suit['weight'],
                'source': 'json'
            })
        
        self.stats['total_loaded'] = len(standardized)
        
        if kwargs.get('validate', True):
            valid = [p for p in standardized if self._is_valid_point(p)[0]]
            standardized = valid
        if kwargs.get('remove_dups', True):
            standardized = self.remove_duplicates(standardized)
        if kwargs.get('normalize', True):
            standardized = self.normalize_data(standardized)
        if kwargs.get('enrich', True):
            standardized = self.enrich_data(standardized)
        
        return standardized
    
    def save_to_json(self, data: List[Dict], filename: str):
        serializable = []
        for p in data:
            p_copy = p.copy()
            if 'location' in p_copy and isinstance(p_copy['location'], tuple):
                p_copy['location'] = list(p_copy['location'])
            serializable.append(p_copy)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        
        self._log(f"Saved {len(data)} points to {filename}")
    
    def print_summary(self, data: List[Dict]):
        stats = self.get_statistics(data)
        if 'error' in stats:
            print(f"\n{stats['error']}")
            return
        
        print(f"\n{'='*60}\nDATA LOADER SUMMARY\n{'='*60}")
        print(f"Total points:        {stats['total_points']}")
        print(f"Valid plantable:     {stats['plantable_count']}")
        print(f"Non-plantable:       {stats['non_plantable_count']}")
        print(f"Duplicates removed:  {stats['duplicates_removed']}")
        print(f"Normalized:          {'Yes' if stats['normalized'] else 'No'}")
        print(f"\nAvg Pollution:       {stats['avg_pollution']:.1f}")
        print(f"Avg Temperature:     {stats['avg_temperature']:.1f}C")
        print(f"Avg Benefit:         {stats['avg_benefit']:.1f}")
        print(f"\nLand types:          ({stats['unique_land_types']} unique)")
        for lt, count in sorted(stats['land_type_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {lt}: {count}")
        print("="*60)
    
    def reset_stats(self):
        self.stats = {'total_loaded': 0, 'valid': 0, 'invalid': 0, 
                      'duplicates_removed': 0, 'enriched': 0, 'normalized': False}